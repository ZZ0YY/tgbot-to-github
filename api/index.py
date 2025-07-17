# api/index.py

import os
import json
import requests
import base64  # 引入 base64 库
from flask import Flask, request

# 初始化 Flask 应用
app = Flask(__name__)

# 从环境变量中读取配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# GitHub API dispatch URL
DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

@app.route('/', methods=['POST'])
def webhook():
    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
    except (ValueError, TypeError):
        # 如果ID配置错误，直接返回
        return "Server configuration error: Invalid YOUR_TELEGRAM_ID", 500

    update = request.get_json()
    if not update:
        return "No JSON payload received.", 400

    message = update.get('message')

    if (
        message and
        message.get('from', {}).get('id') == YOUR_TELEGRAM_ID and
        message.get('document')
    ):
        document = message['document']
        file_id = document['file_id']
        # 获取原始文件名
        original_file_name = document.get('file_name', 'untitled_from_telegram')
        chat_id = message['chat']['id']

        # --- 核心修改：对文件名进行 Base64 编码 ---
        # 1. 将文件名字符串用 utf-8 编码为字节串
        # 2. 对字节串进行 Base64 编码
        # 3. 将 Base64 编码后的字节串变回 utf-8 字符串，以便放入 JSON
        file_name_b64 = base64.b64encode(original_file_name.encode('utf-8')).decode('utf-8')
        # ----------------------------------------

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}",
        }
        data = {
            "event_type": "upload_file_to_release",
            "client_payload": {
                "file_id": file_id,
                # 传递编码后的文件名
                "file_name_b64": file_name_b64,
            }
        }
        
        try:
            response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
            response.raise_for_status()
            # 回复用户时，使用原始文件名，体验更好
            reply_text = f"✅ Success! Received '{original_file_name}'. GitHub Action triggered."
        except requests.exceptions.RequestException as e:
            reply_text = f"❌ Error! Failed to trigger GitHub Action for '{original_file_name}'.\nDetails: {e}"
        
        # 发送反馈消息
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply_text})
        return "Webhook processed.", 200

    return "Message not applicable.", 200