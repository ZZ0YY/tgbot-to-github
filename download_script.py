# download_script.py

import os
import requests
import sys

def main():
    """
    一个用于在 GitHub Actions 中从 Telegram 下载文件的脚本。
    它从环境变量中读取配置，并将下载的文件名输出到 GITHUB_OUTPUT。
    """
    # 从环境变量中获取所需信息
    bot_token = os.getenv('BOT_TOKEN')
    file_id = os.getenv('FILE_ID')
    file_name = os.getenv('FILE_NAME')

    # 验证环境变量是否存在
    if not all([bot_token, file_id, file_name]):
        print("Error: Missing one or more environment variables (BOT_TOKEN, FILE_ID, FILE_NAME).")
        sys.exit(1)

    # 1. 使用 getFile 方法获取文件的 file_path
    get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
    try:
        response = requests.get(get_file_url, params={'file_id': file_id}, timeout=20)
        response.raise_for_status()  # 如果请求失败 (非2xx状态码)，会抛出异常
        
        data = response.json()
        if not data.get('ok'):
            print(f"Error from Telegram API: {data.get('description')}")
            sys.exit(1)

        file_path = data['result']['file_path']

    except requests.exceptions.RequestException as e:
        print(f"Error getting file info from Telegram: {e}")
        sys.exit(1)
    except KeyError:
        print(f"Error: Unexpected JSON response from Telegram getFile API. Response: {response.text}")
        sys.exit(1)

    # 2. 构建完整的文件下载 URL
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    # 3. 下载文件
    print(f"Downloading '{file_name}' from Telegram...")
    try:
        with requests.get(download_url, stream=True, timeout=300) as r: # 增加超时时间以防大文件
            r.raise_for_status()
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    print(f"File downloaded successfully and saved as '{file_name}'")

    # 4. 将下载的文件名输出给 GitHub Actions 的后续步骤使用
    github_output_file = os.getenv('GITHUB_OUTPUT')
    if github_output_file:
        with open(github_output_file, 'a') as f:
            print(f"downloaded_file_name={file_name}", file=f)
    else:
        print("Warning: GITHUB_OUTPUT environment variable not found. Cannot set output for next steps.")

if __name__ == '__main__':
    main()