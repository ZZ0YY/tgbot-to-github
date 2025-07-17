# api/index.py

import os
import json
import requests
import traceback # 引入 traceback 模块
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YOUR_TELEGRAM_ID_STR = os.getenv('YOUR_TELEGRAM_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# 全局变量，用于在出错时发送消息
CHAT_ID_FOR_DEBUG = None
try:
    if YOUR_TELEGRAM_ID_STR:
        CHAT_ID_FOR_DEBUG = int(YOUR_TELEGRAM_ID_STR)
except:
    pass

def send_debug_message(text):
    """一个辅助函数，用于发送调试信息给自己"""
    if not CHAT_ID_FOR_DEBUG or not BOT_TOKEN:
        return
    
    # 限制消息长度，防止超长
    if len(text) > 4000:
        text = text[:4000] + "\n... (truncated)"
        
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID_FOR_DEBUG, "text": f"🐞 DEBUG:\n\n{text}"}
    try:
        requests.post(api_url, json=payload, timeout=5)
    except Exception as e:
        # 如果连发送调试消息都失败了，就没办法了
        print(f"Failed to send debug message: {e}")

@app.route('/', methods=['POST'])
def webhook():
    try:
        # 检查所有配置是否就绪
        if not all([BOT_TOKEN, YOUR_TELEGRAM_ID_STR, GITHUB_TOKEN, GITHUB_REPO]):
            send_debug_message("Server Error: One or more environment variables are not set!")
            return "Server configuration error.", 500
        
        YOUR_TELEGRAM_ID = int(YOUR_TELEGRAM_ID_STR)

        update = request.get_json()
        if not update:
            send_debug_message("Received a request, but it has no JSON payload.")
            return "No JSON payload.", 400

        # 发送收到的原始数据给自己，用于分析
        send_debug_message(f"Received update:\n{json.dumps(update, indent=2)}")

        message = update.get('message')
        
        if (
            message and
            message.get('from', {}).get('id') == YOUR_TELEGRAM_ID and
            message.get('document')
        ):
            document = message['document']
            file_id = document['file_id']
            file_name = document.get('file_name', 'untitled_from_telegram')
            chat_id = message['chat']['id']

            send_debug_message(f"Condition met. Triggering action for '{file_name}'...")

            DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {GITHUB_TOKEN}",
            }
            data = {"event_type": "upload_file_to_release", "client_payload": {"file_id": file_id, "file_name": file_name}}
            
            response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
            
            if response.status_code == 204:
                reply_text = f"✅ Success! Triggered action for '{file_name}'."
            else:
                reply_text = f"❌ Error triggering action. GitHub API responded with {response.status_code}.\nResponse: {response.text}"
            
            send_debug_message(reply_text) # 把成功或失败的结果也发给自己
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": reply_text})
            return "OK", 200
        else:
            send_debug_message("Condition not met. Ignoring message.")
            return "Message not applicable.", 200

    except Exception as e:
        # 捕捉所有未知错误，并将详细信息发送给自己
        error_details = traceback.format_exc()
        send_debug_message(f"An unexpected error occurred:\n{error_details}")
        return "Internal server error.", 500