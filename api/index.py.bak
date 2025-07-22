# /api/index.py

import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# 配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_CHAT_ID_STR = os.getenv('AUTHORIZED_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 用于处理相册的简单去重
processed_media_groups = {}

def trigger_action(chat_id, message_id):
    """封装触发 GitHub Action 的函数"""
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "event_type": "upload_file_from_user_api",
        "client_payload": {"chat_id": chat_id, "message_id": message_id}
    }
    try:
        response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
        return True, ""
    except requests.exceptions.RequestException as e:
        return False, str(e)

def send_reply(chat_id, text):
    """封装发送回复的函数"""
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

@app.route('/', methods=['POST'])
def webhook():
    try:
        AUTHORIZED_CHAT_ID = int(AUTHORIZED_CHAT_ID_STR)
    except (ValueError, TypeError):
        print("严重错误: 环境变量 AUTHORIZED_CHAT_ID 无效或未设置!")
        return "Server config error: Invalid AUTHORIZED_CHAT_ID", 500

    update = request.get_json()
    if not update: return "No JSON payload", 400

    message = update.get('message')
    if not message: return "No message in update", 200

    chat_id = message['chat']['id']

    if chat_id != AUTHORIZED_CHAT_ID:
        return "Message not from authorized group", 200

    if message.get('document') or message.get('photo') or message.get('video'):
        message_id = message['message_id']
        file_name = "媒体文件"
        if media_obj := message.get('document') or message.get('video'):
            file_name = media_obj.get('file_name', '媒体文件')
        elif photo_list := message.get('photo'):
            file_name = f"照片_{photo_list[-1]['file_unique_id']}.jpg"

        media_group_id = message.get('media_group_id')
        if media_group_id and not processed_media_groups.get(media_group_id):
            send_reply(chat_id, f"✅ 收到一个相册 (Album)，将逐一处理...")
            processed_media_groups[media_group_id] = True
        
        success, error_msg = trigger_action(chat_id, message_id)
        
        if not media_group_id: # 只为非相册消息或相册第一条回复
            if success:
                send_reply(chat_id, f"✅ 已收到 '{file_name}'，下载任务已触发。")
            else:
                send_reply(chat_id, f"❌ 触发 '{file_name}' 失败: {error_msg}")
        
        return "Webhook processed.", 200

    return "No processable media in message.", 200