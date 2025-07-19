# /api/index.py

import os
import json
import requests
from flask import Flask, request

# --- 应用配置 ---
app = Flask(__name__)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_CHAT_ID_STR = os.getenv('AUTHORIZED_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 用于处理相册的简单去重，在 Serverless 环境下能有效处理紧邻到达的消息
processed_media_groups = {}

def trigger_action(chat_id, message_id):
    """一个封装好的函数，用于触发 GitHub Action。返回 (是否成功, 错误信息)"""
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
    """一个封装好的函数，用于向群组发送回复。"""
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

@app.route('/', methods=['POST'])
def webhook():
    try:
        AUTHORIZED_CHAT_ID = int(AUTHORIZED_CHAT_ID_STR)
    except (ValueError, TypeError):
        # 如果配置错误，这是一个严重问题，但服务器本身没必要宕机
        print("严重错误: 环境变量 AUTHORIZED_CHAT_ID 无效或未设置!")
        return "Server config error: Invalid AUTHORIZED_CHAT_ID", 500

    update = request.get_json()
    if not update: return "No JSON payload", 400

    message = update.get('message')
    if not message: return "No message found in update", 200

    chat_id = message['chat']['id']

    # 验证消息是否来自我们授权的那个群组
    if chat_id != AUTHORIZED_CHAT_ID:
        return "Message not from the authorized group.", 200

    # 检查消息是否包含可处理的媒体
    if message.get('document') or message.get('photo') or message.get('video') or message.get('audio'):
        message_id = message['message_id']
        
        file_name = "媒体文件" # 默认名
        media_obj = message.get('document') or message.get('video')
        if media_obj and media_obj.get('file_name'):
            file_name = media_obj.get('file_name')
        elif message.get('photo'):
            # 为照片生成一个独特的描述
            file_name = f"照片_{message['photo'][-1]['file_unique_id']}.jpg"

        media_group_id = message.get('media_group_id')
        
        # 处理相册 (Media Group)
        if media_group_id:
            if not processed_media_groups.get(media_group_id):
                send_reply(chat_id, f"✅ 收到一个相册 (Album)，将逐一处理其中的项目...")
                processed_media_groups[media_group_id] = True
            
            # 为相册中的每个项目单独触发 Action
            success, error_msg = trigger_action(chat_id, message_id)
            if not success:
                 send_reply(chat_id, f"❌ 触发相册项目 '{file_name}' 失败: {error_msg}")

        # 处理单个文件/媒体
        else:
            success, error_msg = trigger_action(chat_id, message_id)
            if success:
                send_reply(chat_id, f"✅ 已收到文件 '{file_name}'，下载任务已触发。")
            else:
                send_reply(chat_id, f"❌ 触发文件 '{file_name}' 失败: {error_msg}")

        return "Webhook processed.", 200

    return "Message contains no processable media.", 200