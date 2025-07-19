# /download_script.py (Final version for curl)

import os, sys, base64, shutil, requests

def main():
    bot_token, file_id, b64_name = (os.getenv(k) for k in ['BOT_TOKEN', 'FILE_ID', 'ORIGINAL_FILE_NAME_B64'])
    if not all([bot_token, file_id, b64_name]):
        print("错误: 缺少环境变量。", file=sys.stderr); sys.exit(1)

    try:
        original_name = base64.b64decode(b64_name).decode('utf-8')
    except Exception as e:
        print(f"错误: 解码文件名失败 - {e}", file=sys.stderr); sys.exit(1)
        
    save_path = os.path.join("downloads", original_name)
    os.makedirs("downloads", exist_ok=True)
    print(f"准备下载 '{original_name}' 到 '{save_path}'...")

    try:
        # (下载逻辑与之前版本完全相同)
        get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        response = requests.get(get_file_url, params={'file_id': file_id}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get('ok'): raise ValueError(f"API 错误: {data.get('description')}")
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{data['result']['file_path']}"

        with requests.get(download_url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
    except Exception as e:
        print(f"错误: 下载文件时失败 - {e}", file=sys.stderr); sys.exit(1)

    print(f"文件下载成功: {save_path}")

    # 将两个关键信息输出给后续步骤
    if output_file := os.getenv('GITHUB_OUTPUT'):
        with open(output_file, 'a') as f:
            print(f"file_path={save_path}", file=f)
            print(f"original_name={original_name}", file=f)

if __name__ == '__main__':
    main()