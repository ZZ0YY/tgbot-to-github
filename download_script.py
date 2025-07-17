# download_script.py (Final "Keep It Simple" Version)

import os
import sys
import base64
import shutil

def main():
    bot_token = os.getenv('BOT_TOKEN')
    file_id = os.getenv('FILE_ID')
    file_name_b64 = os.getenv('FILE_NAME_B64')

    if not all([bot_token, file_id, file_name_b64]):
        print("Error: Missing critical environment variables.", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. 核心：只做 Base64 解码，获取原始的、纯净的 UTF-8 文件名
        original_file_name = base64.b64decode(file_name_b64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding file name: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Using original decoded file name: '{original_file_name}'")

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
    print(f"Downloading file...")

    try:
        # **使用原始文件名来保存文件**
        with requests.get(download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(original_file_name, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as e:
        print(f"Error downloading file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"File downloaded successfully and saved as '{original_file_name}'")

    # --- 将原始文件名传递给 GitHub Release 步骤 ---
    github_output_file = os.getenv('GITHUB_OUTPUT')
    if github_output_file:
        with open(github_output_file, 'a') as f:
            print(f"downloaded_file_name={original_file_name}", file=f)

if __name__ == '__main__':
    # 引入 requests 库
    import requests
    main()