# /api/index.py (Forward-to-Self Version)

import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# 配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route('/', methods=['POST'])
def webhook():
    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
    except (ValueError, TypeError):
        return "Server config error: Invalid YOUR_TELEGRAM_ID", 500

    update = request.get_json()
    if not update: return "No JSON payload", 400

    message = update.get('message')
    if not (message and message.get('from', {}).get('id') == YOUR_TELEGRAM_ID):
        return "Not an authorized message", 200

    # 检查消息是否包含任何媒体
    if message.get('document') or message.get('photo') or message.get('video') or message.get('audio'):
        from_chat_id = message['chat']['id'] # 消息来源的 chat_id
        message_id_to_forward = message['message_id'] # 需要转发的消息 ID

        # --- 核心逻辑：将收到的消息转发到用户的收藏夹 ---
        forward_url = f"{TELEGRAM_API_URL}/forwardMessage"
        forward_payload = {
            'chat_id': YOUR_TELEGRAM_ID, # 目标 chat_id 是用户的收藏夹
            'from_chat_id': from_chat_id,
            'message_id': message_id_to_forward,
        }
        
        try:
            forward_res = requests.post(forward_url, json=forward_payload, timeout=10)
            forward_res.raise_for_status()
            forward_data = forward_res.json()

            if forward_data.get('ok'):
                # 从转发成功的返回结果中，获取文件在收藏夹中的新 message_id
                new_message_id = forward_data['result']['message_id']
                
                # 触发 GitHub Action，并传递新的 message_id
                headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
                dispatch_data = {
                    "event_type": "upload_file_from_user_api",
                    "client_payload": {
                        "chat_id": YOUR_TELEGRAM_ID, # 明确告诉 Action 去收藏夹找
                        "message_id": new_message_id,
                    }
                }
                
                dispatch_res = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(dispatch_data), timeout=10)
                dispatch_res.raise_for_status()
                reply_text = "✅ 收到文件，已存入收藏夹并触发下载任务。"
            else:
                reply_text = f"❌ 转发到收藏夹失败: {forward_data.get('description')}"
        
        except requests.exceptions.RequestException as e:
            reply_text = f"❌ 操作失败: {e}"
        
        # 回复原始对话
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": from_chat_id, "text": reply_text})
        return "Webhook processed.", 200

    return "No media found in message.", 200