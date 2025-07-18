# /download_script.py

import os
import sys
import base64
import shutil
import requests

def main():
    """使用 Bot API 从 Telegram 下载文件，并以其原始名称保存到 'downloads' 子目录中。"""
    bot_token = os.getenv('BOT_TOKEN')
    file_id = os.getenv('FILE_ID')
    original_file_name_b64 = os.getenv('ORIGINAL_FILE_NAME_B64')

    if not all([bot_token, file_id, original_file_name_b64]):
        print("错误: 缺少关键的环境变量。", file=sys.stderr)
        sys.exit(1)

    try:
        original_file_name = base64.b64decode(original_file_name_b64).decode('utf-8')
    except Exception as e:
        print(f"错误: 解码文件名失败 - {e}", file=sys.stderr)
        sys.exit(1)
        
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    save_path = os.path.join(download_dir, original_file_name)
    
    print(f"准备下载 '{original_file_name}' 到 '{save_path}'...")

    get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
    try:
        response = requests.get(get_file_url, params={'file_id': file_id}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get('ok'): raise ValueError(f"Telegram API 错误: {data.get('description')}")
        file_path = data['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    except Exception as e:
        print(f"错误: 获取文件信息失败 - {e}", file=sys.stderr)
        sys.exit(1)

    print("开始从 Telegram 下载文件...")
    try:
        with requests.get(download_url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as e:
        print(f"错误: 下载文件时失败 - {e}", file=sys.stderr)
        sys.exit(1)

    print("文件下载成功。")

if __name__ == '__main__':
    main()