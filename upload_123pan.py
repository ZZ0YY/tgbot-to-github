# /upload_123pan.py

import os
import sys
import hashlib
import time
import requests
from requests.exceptions import RequestException

# --- 配置常量 ---
API_BASE_URL = "https://open-api.123pan.com"
SINGLE_UPLOAD_THRESHOLD = 950 * 1024 * 1024
MAX_RETRIES = 3

# --- 全局变量 ---
ACCESS_TOKEN = os.getenv("PAN_123_ACCESS_TOKEN")
COMMON_HEADERS = {
    "Platform": "open_platform",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def calculate_md5(file_path, chunk_size=8192):
    """计算文件的MD5值"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()

def make_request(method, url, **kwargs):
    """带重试机制的通用网络请求函数"""
    headers = COMMON_HEADERS.copy()
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
            response.raise_for_status()
            if response.status_code == 200 and not response.text:
                return {"code": 0, "message": "ok", "data": None}
            return response.json()
        except RequestException as e:
            print(f"  - 网络请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except requests.exceptions.JSONDecodeError:
            if response.status_code == 200:
                 return {"code": 0, "message": "ok", "data": None}
            raise

def get_or_create_directory(directory_name, parent_id):
    """检查目录是否存在，不存在则创建。返回目录ID。"""
    print(f"  - 正在检查父目录 (ID: {parent_id}) 下是否存在名为 '{directory_name}' 的子目录...")
    
    try:
        list_url = f"{API_BASE_URL}/api/v2/file/list?parentFileId={parent_id}&limit=100"
        list_res = make_request("GET", list_url)
        
        if list_res and list_res.get("code") == 0:
            for item in list_res.get("data", {}).get("fileList", []):
                if (item.get("type") == 1 and 
                    item.get("filename") == directory_name and 
                    item.get("trashed") == 0):
                    dir_id = item['fileId']
                    print(f"  - ✅ 发现已存在的目录，ID: {dir_id}")
                    return dir_id
    except RequestException as e:
        print(f"  - ⚠️ 检查目录是否存在时出错: {e}。将尝试直接创建。", file=sys.stderr)

    print(f"  - 目录不存在，正在创建...")
    try:
        mkdir_url = f"{API_BASE_URL}/upload/v1/file/mkdir"
        mkdir_payload = {"name": directory_name, "parentID": int(parent_id)}
        mkdir_res = make_request("POST", mkdir_url, json=mkdir_payload)
        
        if mkdir_res and mkdir_res.get("code") == 0:
            new_dir_id = mkdir_res.get("data", {}).get("dirID")
            if new_dir_id:
                print(f"  - ✅ 目录创建成功，ID: {new_dir_id}")
                return new_dir_id
        
        if "重名" in mkdir_res.get("message", ""):
             print(f"  - ⚠️ 创建时提示重名，将重新检查以获取ID。", file=sys.stderr)
             return get_or_create_directory(directory_name, parent_id)

        print(f"  - ❌ 创建目录失败，API响应: {mkdir_res}", file=sys.stderr)
        return None
        
    except RequestException as e:
        print(f"  - ❌ 创建目录时发生网络错误: {e}", file=sys.stderr)
        return None

def upload_single(file_path, original_name, upload_domain, parent_id):
    """执行单步上传"""
    print(f"  - 使用 [单步上传] 模式...")
    file_size = os.path.getsize(file_path)
    file_md5 = calculate_md5(file_path)
    url = f"https://{upload_domain}/upload/v2/file/single/create"
    form_data = {'parentFileID': (None, str(parent_id)), 'filename': (None, original_name), 'etag': (None, file_md5), 'size': (None, str(file_size))}
    with open(file_path, 'rb') as f:
        files = {'file': (original_name, f)}
        headers = COMMON_HEADERS.copy()
        for attempt in range(MAX_RETRIES):
            try:
                f.seek(0)
                response = requests.post(url, headers=headers, data=form_data, files=files, timeout=300)
                response.raise_for_status()
                res_json = response.json()
                if res_json.get("code") == 0 and res_json.get("data", {}).get("completed"):
                    print(f"  - ✅ 单步上传成功, FileID: {res_json['data']['fileID']}")
                    return True
                else:
                    print(f"  - ❌ API返回错误: {res_json}", file=sys.stderr)
            except RequestException as e:
                print(f"  - 网络请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}", file=sys.stderr)
                if attempt >= MAX_RETRIES - 1:
                    print(f"  - ❌ 达到最大重试次数，上传失败。", file=sys.stderr)
                    return False
                time.sleep(2 ** attempt)
    return False

def upload_chunked(file_path, original_name, parent_id):
    """执行分片上传"""
    print(f"  - 文件较大, 启动 [分片上传] 模式...")
    file_size = os.path.getsize(file_path)
    file_md5 = calculate_md5(file_path)
    print("    - 步骤 1/3: 创建文件...")
    create_url = f"{API_BASE_URL}/upload/v2/file/create"
    create_payload = {"parentFileID": int(parent_id), "filename": original_name, "etag": file_md5, "size": file_size}
    try:
        create_res = make_request("POST", create_url, json=create_payload)
    except RequestException as e:
        print(f"    - ❌ 创建文件失败: {e}", file=sys.stderr)
        return False
    if create_res.get("data", {}).get("reuse"):
        print(f"    - ✅ 秒传成功! FileID: {create_res['data']['fileID']}")
        return True
    data = create_res.get("data")
    if not data or not all(k in data for k in ["preuploadID", "sliceSize", "servers"]):
        print(f"    - ❌ 创建文件API响应格式不正确: {create_res}", file=sys.stderr)
        return False
    preupload_id, slice_size, upload_domain = data["preuploadID"], data["sliceSize"], data["servers"][0]
    print(f"    - PreuploadID: {preupload_id[:15]}...")
    print(f"    - 分片大小: {slice_size // 1024 // 1024} MB")
    print("    - 步骤 2/3: 逐个上传分片...")
    slice_url = f"{upload_domain}/upload/v2/file/slice"
    slice_count = (file_size + slice_size - 1) // slice_size
    with open(file_path, 'rb') as f:
        for i in range(slice_count):
            slice_no, chunk = i + 1, f.read(slice_size)
            if not chunk: break
            print(f"      - 正在上传分片 {slice_no}/{slice_count}...")
            slice_md5 = hashlib.md5(chunk).hexdigest()
            form_data = {'preuploadID': (None, preupload_id), 'sliceNo': (None, str(slice_no)), 'sliceMD5': (None, slice_md5)}
            files = {'slice': chunk}
            try:
                make_request("POST", slice_url, data=form_data, files=files, timeout=300)
            except RequestException as e:
                print(f"      - ❌ 分片 {slice_no} 上传失败: {e}", file=sys.stderr)
                return False
    print("    - 步骤 3/3: 通知服务器合并文件...")
    complete_url = f"{API_BASE_URL}/upload/v2/file/upload_complete"
    for _ in range(10):
        try:
            complete_res = make_request("POST", complete_url, json={"preuploadID": preupload_id})
            if complete_res.get("data", {}).get("completed"):
                print(f"    - ✅ 合并成功! FileID: {complete_res['data']['fileID']}")
                return True
            time.sleep(1)
        except RequestException as e:
            print(f"    - ❌ 请求合并接口失败: {e}", file=sys.stderr)
            return False
    print("    - ❌ 合并超时，上传失败。", file=sys.stderr)
    return False

def main():
    if not ACCESS_TOKEN:
        print("错误: 缺少环境变量 PAN_123_ACCESS_TOKEN。", file=sys.stderr)
        return 1
    file_paths_str = os.getenv("DOWNLOADED_FILES")
    original_names_str = os.getenv("ORIGINAL_NAMES")
    if not file_paths_str or not original_names_str:
        print("没有找到要上传的文件，脚本退出。")
        return 0
    delimiter = "---END_OF_FILE_PATH---"
    file_paths = [path for path in file_paths_str.split('\n') if path and path != delimiter]
    original_names = [name for name in original_names_str.split('\n') if name and name != delimiter]
    if len(file_paths) != len(original_names):
        print("错误: 文件路径和原始文件名的数量不匹配。", file=sys.stderr)
        return 1
    print(f"检测到 {len(file_paths)} 个文件需要上传。")
    root_upload_dir_id = os.getenv("PARENT_FILE_ID", "0")
    release_tag = os.getenv("RELEASE_TAG")
    target_upload_dir_id = root_upload_dir_id
    if release_tag:
        print(f"\n--- 准备目标目录 (基于 Release Tag: {release_tag}) ---")
        target_upload_dir_id = get_or_create_directory(release_tag, root_upload_dir_id)
        if target_upload_dir_id is None:
            print("错误: 无法获取或创建目标目录，上传任务中止。", file=sys.stderr)
            return 1
    else:
        print("\n--- 未提供 RELEASE_TAG，文件将直接上传到根目录 ---")
    upload_domain_for_single = ""
    try:
        domain_res = make_request("GET", f"{API_BASE_URL}/upload/v2/file/domain")
        if domain_res.get("code") == 0 and domain_res.get("data"):
            upload_domain_for_single = domain_res["data"][0].replace("http://", "").replace("https://", "")
            print(f"获取到上传域名: {upload_domain_for_single}")
    except RequestException as e:
        print(f"警告: 获取单步上传域名失败: {e}", file=sys.stderr)
    success_count, failure_count = 0, 0
    for path, name in zip(file_paths, original_names):
        print(f"\n--- 开始处理文件: '{name}' (上传至目录ID: {target_upload_dir_id}) ---")
        if not os.path.exists(path):
            print(f"  - ❌ 文件不存在，跳过。", file=sys.stderr)
            failure_count += 1; continue
        file_size = os.path.getsize(path)
        print(f"  - 文件大小: {file_size / 1024 / 1024:.2f} MB")
        uploaded = False
        if file_size < SINGLE_UPLOAD_THRESHOLD and upload_domain_for_single:
            uploaded = upload_single(path, name, upload_domain_for_single, target_upload_dir_id)
        else:
            uploaded = upload_chunked(path, name, target_upload_dir_id)
        if uploaded: success_count += 1
        else: failure_count += 1
    print("\n--- 上传任务全部完成 ---")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failure_count}")
    if failure_count > 0: return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
