# /api/index.py

import os
import json
import requests
import base64
from flask import Flask, request

# --- 应用配置 ---
app = Flask(__name__)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

def extract_media_info(message):
    """从消息中提取最重要的媒体信息。"""
    media_priority_list = [
        ('document', False, None), ('video', False, '.mp4'),
        ('animation', False, '.mp4'), ('photo', True, '.jpg'),
        ('audio', False, '.mp3'), ('voice', '.ogg'),
        ('sticker', False, '.webp'),
    ]

    for field, is_list, suffix in media_priority_list:
        if media_obj := message.get(field):
            target_obj = max(media_obj, key=lambda m: m.get('file_size', 0)) if is_list else media_obj
            if not (file_id := target_obj.get('file_id')): continue
            
            file_name = target_obj.get('file_name') or f"{file_id}{suffix}"
            return {"file_id": file_id, "file_name": file_name, "media_type": field}

    if (web_page := message.get('web_page')) and (photo_list := web_page.get('photo')):
        largest_photo = max(photo_list, key=lambda p: p.get('file_size', 0))
        if file_id := largest_photo.get('file_id'):
            return {"file_id": file_id, "file_name": f"link_preview_{file_id}.jpg", "media_type": "web_page_photo"}

    return None

@app.route('/', methods=['POST'])
def webhook():
    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
    except (ValueError, TypeError):
        return "服务配置错误: 无效的 YOUR_TELEGRAM_ID", 500

    update = request.get_json()
    if not update: return "未收到 JSON 数据。", 400

    message = update.get('message')
    if not (message and message.get('from', {}).get('id') == YOUR_TELEGRAM_ID):
        return "消息并非来自授权用户。", 200

    media_info = extract_media_info(message)
    if not media_info:
        return "消息为纯文本或不含可处理的媒体。", 200

    file_name_b64 = base64.b64encode(media_info['file_name'].encode('utf-8')).decode('utf-8')
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "event_type": "upload_file_to_release",
        "client_payload": {"file_id": media_info['file_id'], "original_file_name_b64": file_name_b64}
    }
    
    try:
        response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
        reply_text = f"✅ 已收到 {media_info['media_type']}: '{media_info['file_name']}'。已触发 GitHub Action。"
    except requests.exceptions.RequestException as e:
        reply_text = f"❌ 触发 Action 失败: {e}"
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": message['chat']['id'], "text": reply_text})
    return "Webhook 已处理。", 200