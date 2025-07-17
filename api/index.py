# api/index.py

import os
import json
import requests
from flask import Flask, request

# 初始化 Flask 应用
app = Flask(__name__)

# 从 Vercel 的环境变量中读取配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO') # 格式: "your-username/your-repo"

# 预先检查环境变量是否存在
if not all([BOT_TOKEN, YOUR_TELEGRAM_ID_STR, GITHUB_TOKEN, GITHUB_REPO]):
    # 在生产环境中，我们不能简单地停止应用，但可以记录一个错误。
    # Vercel 的日志会显示这个信息。
    print("FATAL ERROR: One or more environment variables are not set!")

# 将字符串ID转换为整数，并处理可能的错误
try:
    YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
except (ValueError, TypeError):
    YOUR_TELEGRAM_ID = None
    print(f"FATAL ERROR: YOUR_TELEGRAM_ID ('{YOUR_TELEGRAM_ID_STR}') is not a valid integer!")

# GitHub API dispatch URL
DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

# 主 Webhook 路由，Vercel 会将所有请求都指向这里
@app.route('/', methods=['POST'])
def webhook():
    # 检查所有配置是否就绪
    if not all([BOT_TOKEN, YOUR_TELEGRAM_ID, GITHUB_TOKEN, GITHUB_REPO]):
        return "Server configuration error.", 500

    # 从 Telegram 获取 JSON 数据
    update = request.get_json()

    if not update:
        return "No JSON payload received.", 400

    # 从 update 中提取 message 对象
    message = update.get('message')

    # 核心逻辑：验证消息来源和内容
    # 1. 消息存在
    # 2. 消息发送者是授权用户 (你自己)
    # 3. 消息包含一个文件 (document)
    if (
        message and
        message.get('from', {}).get('id') == YOUR_TELEGRAM_ID and
        message.get('document')
    ):
        document = message['document']
        file_id = document['file_id']
        # 如果文件名不存在，提供一个默认值
        file_name = document.get('file_name', 'untitled_from_telegram')
        chat_id = message['chat']['id']

        print(f"Received file '{file_name}' from authorized user. Triggering GitHub Action...")
        
        # 准备触发 GitHub Actions 的请求头和数据
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28" # 推荐的最佳实践
        }
        data = {
            "event_type": "upload_file_to_release", # 自定义的事件类型，必须与 workflow 文件中的 on.repository_dispatch.types 匹配
            "client_payload": { # 将文件信息作为载荷传递给 Action
                "file_id": file_id,
                "file_name": file_name,
            }
        }
        
        # 发送 POST 请求到 GitHub API 来触发 Action
        try:
            response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
            response.raise_for_status() # 如果请求失败 (非2xx状态码)，会抛出异常
            
            reply_text = f"✅ Success! Received '{file_name}'. GitHub Action has been triggered to upload it to today's release."
            print("Successfully triggered GitHub Action.")

        except requests.exceptions.RequestException as e:
            reply_text = f"❌ Error! Failed to trigger GitHub Action for '{file_name}'.\nDetails: {e}"
            print(f"Error triggering GitHub Action: {e}")
            
        # 给自己发送一个操作结果的反馈
        send_reply(chat_id, reply_text)
        
        return "Webhook processed.", 200

    # 如果消息不符合条件，静默处理
    print("Received a message, but it was not a document from the authorized user. Ignoring.")
    return "Message not applicable.", 200

def send_reply(chat_id, text):
    """一个简单的辅助函数，用于向用户发送回复消息"""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(api_url, json=payload, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Error sending reply to Telegram: {e}")

# 这个入口点是为了本地测试，Vercel 会忽略它
if __name__ == "__main__":
    app.run(debug=True, port=5001)