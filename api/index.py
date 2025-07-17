# api/index.py (Bot API - Final Robust Version)

import os
import json
import requests
import base64
from flask import Flask, request
import time

# --- (顶部配置部分保持不变) ---
app = Flask(__name__)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

# 用于相册去重，键为 media_group_id，值为时间戳
# 在 Serverless 环境中，这是一个简单的、尽力而为的去重机制
MEDIA_GROUP_CACHE = {}

def cleanup_cache():
    """清理超过60秒的旧缓存条目"""
    current_time = time.time()
    for group_id in list(MEDIA_GROUP_CACHE.keys()):
        if current_time - MEDIA_GROUP_CACHE[group_id] > 60:
            del MEDIA_GROUP_CACHE[group_id]

def get_media_info(message):
    """从消息中提取 file_id, original_file_name 和 media_type"""
    # 优先级最高的 Document
    if doc := message.get('document'):
        return doc.get('file_id'), doc.get('file_name', f"{doc.get('file_id')}.dat"), 'document'

    # 其次是其他媒体类型
    media_map = {
        'photo': '.jpg', 'video': '.mp4', 'animation': '.mp4',
        'audio': '.mp3', 'voice': '.ogg', 'sticker': '.webp'
    }
    
    for media_type, ext in media_map.items():
        if media_obj := message.get(media_type):
            # Photo 和 Video 是数组，取最大的
            if isinstance(media_obj, list):
                media_obj = max(media_obj, key=lambda m: m.get('file_size', 0))
            
            file_id = media_obj.get('file_id')
            
            # 尝试从 caption 生成文件名，否则用 file_id
            caption = message.get('caption', '').strip()
            if caption and len(caption) < 100: # 避免过长的 caption
                # 简单清理 caption 作为文件名
                safe_caption = "".join(c for c in caption if c.isalnum() or c in (' ', '.', '_')).rstrip()
                file_name = f"{safe_caption}{ext}" if safe_caption else f"{file_id}{ext}"
            else:
                file_name = f"{file_id}{ext}"
                
            return file_id, file_name, media_type

    # 最后检查链接预览
    if (wp := message.get('web_page')) and (photo := wp.get('photo')):
        largest_photo = max(photo, key=lambda p: p.get('file_size', 0))
        file_id = largest_photo.get('file_id')
        file_name = f"link_preview_{file_id}.jpg"
        return file_id, file_name, 'web_page_photo'
        
    return None, None, None


@app.route('/', methods=['POST'])
def webhook():
    cleanup_cache() # 每次请求都清理一下旧缓存

    update = request.get_json()
    if not update or not (message := update.get('message')):
        return "Invalid request", 400

    try:
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)
    except (ValueError, TypeError):
        return "Server config error", 500

    if message.get('from', {}).get('id') != YOUR_TELEGRAM_ID:
        return "Unauthorized user", 200

    # 处理相册（Media Group）
    if media_group_id := message.get('media_group_id'):
        if media_group_id in MEDIA_GROUP_CACHE:
            return "Media group part already processed", 200
        MEDIA_GROUP_CACHE[media_group_id] = time.time()

    file_id, original_file_name, media_type = get_media_info(message)

    if not file_id:
        return "No processable media found", 200

    # 后续流程（编码、发送请求、回复）
    file_name_b64 = base64.b64encode(original_file_name.encode('utf-8')).decode('utf-8')
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "event_type": "upload_file_to_release",
        "client_payload": {"file_id": file_id, "file_name_b64": file_name_b64}
    }
    
    try:
        response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
        reply_text = f"✅ Received {media_type} '{original_file_name}'. Action triggered."
    except requests.exceptions.RequestException as e:
        reply_text = f"❌ Failed to trigger Action. Details: {e}"
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": message['chat']['id'], "text": reply_text})
    return "Webhook processed.", 200