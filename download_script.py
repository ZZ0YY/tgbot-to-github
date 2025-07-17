# download_script.py

import os
import requests
import sys
import base64  # 引入 base64 库

def main():
    """
    一个用于在 GitHub Actions 中从 Telegram 下载文件的脚本。
    它从环境变量中读取配置，对文件名进行 Base64 解码，
    然后下载文件，并将解码后的文件名输出到 GITHUB_OUTPUT。
    """
    bot_token = os.getenv('BOT_TOKEN')
    file_id = os.getenv('FILE_ID')
    # 从环境变量接收 Base64 编码的文件名
    file_name_b64 = os.getenv('FILE_NAME_B64')

    if not all([bot_token, file_id, file_name_b64]):
        print("Error: Missing one or more environment variables.")
        sys.exit(1)

    # --- 核心修改：对文件名进行 Base64 解码 ---
    try:
        # 1. 将 Base64 字符串解码为字节串
        # 2. 将字节串用 utf-8 解码为原始的文件名字符串
        file_name = base64.b64decode(file_name_b64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding file name from Base64: {e}")
        # 如果解码失败，使用一个安全的文件名作为备用
        file_name = f"DECODING_ERROR_{file_id}"
    # ----------------------------------------

    print(f"Decoded file name: '{file_name}'")

    get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
    try:
        response = requests.get(get_file_url, params={'file_id': file_id}, timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get('ok'):
            print(f"Error from Telegram API: {data.get('description')}")
            sys.exit(1)
        file_path = data['result']['file_path']
    except Exception as e:
        print(f"Error getting file info from Telegram: {e}")
        sys.exit(1)

    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    print(f"Downloading '{file_name}' from Telegram...")
    try:
        with requests.get(download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    print(f"File downloaded successfully and saved as '{file_name}'")

    github_output_file = os.getenv('GITHUB_OUTPUT')
    if github_output_file:
        with open(github_output_file, 'a') as f:
            # 确保输出的是解码后的、原始的文件名
            print(f"downloaded_file_name={file_name}", file=f)
    else:
        print("Warning: GITHUB_OUTPUT environment variable not found.")

if __name__ == '__main__':
    main()