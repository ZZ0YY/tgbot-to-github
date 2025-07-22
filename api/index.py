# /api/index.py

import os
import json
import requests
import threading
from flask import Flask, request

app = Flask(__name__)

# --- 新增: 用于批处理的全局变量 ---
# 使用线程锁来确保线程安全
job_queue_lock = threading.Lock()
# 存放待处理任务, 格式: {chat_id: {"message_ids": [id1, id2, ...], "timer": Timer_Object}}
batch_jobs = {}
# 等待更多文件的秒数
BATCH_WAIT_SECONDS = 15.0

# --- 配置 (与原来相同) ---
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_CHAT_ID_STR = os.getenv('AUTHORIZED_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_reply(chat_id, text):
    """封装发送回复的函数"""
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

# --- 修改: 触发函数现在接收一个 ID 列表 ---
def trigger_action(chat_id, message_ids):
    """封装触发 GitHub Action 的函数, 现在可以处理一批消息ID"""
    print(f"准备为 Chat ID {chat_id} 触发 Action，包含消息ID: {message_ids}")
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    # --- 修改: client_payload 现在包含一个 message_ids 列表 ---
    data = {
        "event_type": "upload_file_from_user_api",
        "client_payload": {"chat_id": chat_id, "message_ids": json.dumps(message_ids)}
    }
    try:
        response = requests.post(DISPATCH_URL, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
        return True, ""
    except requests.exceptions.RequestException as e:
        return False, str(e)

# --- 新增: 批处理任务的执行函数 ---
def process_batch(chat_id):
    """
    这是计时器到期后执行的函数。
    它会获取队列中的所有 message_id，然后触发 GitHub Action。
    """
    with job_queue_lock:
        job = batch_jobs.pop(chat_id, None)  # 取出并移除任务

    if job and job["message_ids"]:
        ids_count = len(job["message_ids"])
        send_reply(chat_id, f"⌛️ 收集完毕！共收到 {ids_count} 个文件，正在触发后台处理任务...")
        
        success, error_msg = trigger_action(chat_id, job["message_ids"])
        
        if success:
            print(f"成功为 {ids_count} 个文件触发 Action。")
            send_reply(chat_id, f"✅ 成功触发！{ids_count} 个文件正在上传中，请稍后在 Release 页面查看。")
        else:
            print(f"触发 Action 失败: {error_msg}")
            send_reply(chat_id, f"❌ 触发后台任务失败: {error_msg}")

@app.route('/', methods=['POST'])
def webhook():
    try:
        AUTHORIZED_CHAT_ID = int(AUTHORIZED_CHAT_ID_STR)
    except (ValueError, TypeError):
        print("严重错误: 环境变量 AUTHORIZED_CHAT_ID 无效或未设置!")
        return "Server config error: Invalid AUTHORIZED_CHAT_ID", 500

    update = request.get_json()
    if not update or not (message := update.get('message')):
        return "Invalid payload", 400

    chat_id = message['chat']['id']
    if chat_id != AUTHORIZED_CHAT_ID:
        return "Unauthorized chat", 200

    if message.get('document') or message.get('photo') or message.get('video'):
        message_id = message['message_id']
        
        with job_queue_lock:
            # --- 核心逻辑修改 ---
            if chat_id not in batch_jobs:
                # 这是这个批次的第一个文件
                send_reply(chat_id, f"✅ 收到第一个文件。将在 {int(BATCH_WAIT_SECONDS)} 秒内等待接收更多文件...")
                batch_jobs[chat_id] = {
                    "message_ids": [message_id],
                    # 创建并启动一个新的计时器
                    "timer": threading.Timer(BATCH_WAIT_SECONDS, process_batch, args=[chat_id])
                }
                batch_jobs[chat_id]["timer"].start()
            else:
                # 已经有等待处理的批次，将当前文件加入队列并重置计时器
                batch_jobs[chat_id]["timer"].cancel() # 取消旧的计时器
                batch_jobs[chat_id]["message_ids"].append(message_id)
                timer = threading.Timer(BATCH_WAIT_SECONDS, process_batch, args=[chat_id])
                batch_jobs[chat_id]["timer"] = timer
                timer.start()
                print(f"已将消息 {message_id} 添加到批处理队列中，并重置计时器。")
                
        return "Webhook processed.", 200

    return "No processable media in message.", 200