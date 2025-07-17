# download_script.py (Final version with URL encoding for filenames)

import os
import sys
import base64
import urllib.parse  # 引入 URL 编码库

# 注意：我们不再需要 Telethon，因为你要求回到 Bot API 方案
import requests

def main():
    bot_token = os.getenv('BOT_TOKEN')
    file_id = os.getenv('FILE_ID')
    file_name_b64 = os.getenv('FILE_NAME_B64')

    if not all([bot_token, file_id, file_name_b64]):
        print("Error: Missing critical environment variables.", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. Base64 解码，获取原始的、可能带中文的文件名
        original_file_name = base64.b64decode(file_name_b64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding file name: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Original decoded file name: '{original_file_name}'")

    # --- 核心修改：对原始文件名进行 URL 编码，用于保存和传递 ---
    # quote_plus 会将空格编码为 '+'
    safe_file_name = urllib.parse.quote_plus(original_file_name)
    print(f"URL-encoded safe file name: '{safe_file_name}'")
    # -----------------------------------------------------------

    # --- 下载逻辑 (Bot API, 20MB 限制) ---
    get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
    try:
        response = requests.get(get_file_url, params={'file_id': file_id}, timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get('ok'):
            print(f"Error from Telegram API: {data.get('description')}", file=sys.stderr)
            sys.exit(1)
        file_path = data['result']['file_path']
    except Exception as e:
        print(f"Error getting file info: {e}", file=sys.stderr)
        sys.exit(1)

    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    print(f"Downloading using Bot API...")

    try:
        with requests.get(download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            # **使用编码后的安全文件名来保存文件**
            with open(safe_file_name, 'wb') as f:
                shutil.copyfileobj(r.raw, f) # 使用 shutil 提高大文件下载效率
        
        # 下载后验证文件大小 (借鉴成熟项目的思路)
        expected_size = data['result'].get('file_size')
        if expected_size:
            actual_size = os.path.getsize(safe_file_name)
            if expected_size != actual_size:
                print(f"Warning: File size mismatch! Expected: {expected_size}, Got: {actual_size}", file=sys.stderr)

    except Exception as e:
        print(f"Error downloading file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"File downloaded successfully and saved as '{safe_file_name}'")

    # --- 将编码后的安全文件名传递给 GitHub Release 步骤 ---
    github_output_file = os.getenv('GITHUB_OUTPUT')
    if github_output_file:
        with open(github_output_file, 'a') as f:
            print(f"downloaded_file_name={safe_file_name}", file=f)

if __name__ == '__main__':
    # 为了提高下载效率，额外引入 shutil
    import shutil
    main()