# /api/index.py

import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# 从环境变量读取配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

@app.route('/', methods=['POST'])
def webhook():
    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
    except (ValueError, TypeError):
        return "Server config error: Invalid YOUR_TELEGRAM_ID", 500

    update = request.get_json()
    if not update: return "No JSON payload", 400

    message = update.get('message')

    # 验证消息是否来自您的主号
    if not (message and message.get('from', {}).get('id') == YOUR_TELEGRAM_ID):
        return "Message not from authorized user", 200

    # 检查消息是否包含任何可下载的媒体
    if message.get('document') or message.get('photo') or message.get('video') or message.get('audio') or message.get('animation') or message.get('sticker'):
        message_id = message['message_id']
        chat_id = message['chat']['id']
        
        # 尝试获取文件名用于反馈，如果获取不到则使用通用名
        media = message.get('document') or message.get('video') or {}
        file_name = media.get('file_name', 'media file')

        headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
        data = {
            "event_type": "upload_file_from_user_api",
            "client_payload": {
                "chat_id": chat_id,
                "message_id": message_id,
            }
        }
        
        try:
            response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
            response.raise_for_status()
            reply_text = f"✅ 已收到 '{file_name}'。用户 API 下载任务已触发。"
        except requests.exceptions.RequestException as e:
            reply_text = f"❌ 触发 Action 失败: {e}"
        
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply_text})
        return "Webhook processed.", 200

    return "消息中未发现可处理的媒体。", 200