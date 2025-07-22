# /download_script.py

import os
import sys
import asyncio
import time
import json # <--- 新增
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FileReferenceExpiredError

# progress_callback 函数保持不变...
def progress_callback(current, total, start_time, file_name):
    if total == 0: return
    elapsed_time = time.time() - start_time
    percentage = current * 100 / total
    speed = current / (elapsed_time + 1e-9) / (1024 * 1024)
    if "last_print_time" not in progress_callback.__dict__: progress_callback.last_print_time = 0
    if time.time() - progress_callback.last_print_time > 2 or current == total:
        print(f"Downloading '{file_name}': {percentage:.1f}% ({current/(1024*1024):.2f}/{total/(1024*1024):.2f} MB) at {speed:.2f} MB/s")
        progress_callback.last_print_time = time.time()

async def main_async():
    # --- 修改: 读取 MESSAGE_IDS (复数) ---
    api_id, api_hash, session_string, chat_id_str, message_ids_json = (os.getenv(k) for k in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_SESSION_STRING', 'CHAT_ID', 'MESSAGE_IDS'])

    if not all([api_id, api_hash, session_string, chat_id_str, message_ids_json]):
        print("错误: 缺少关键环境变量。需要 ... CHAT_ID, MESSAGE_IDS", file=sys.stderr)
        return 1
    
    chat_id = int(chat_id_str)
    # --- 修改: 解析 JSON 字符串为 Python 列表 ---
    try:
        message_ids = json.loads(message_ids_json)
        if not isinstance(message_ids, list): raise ValueError()
    except (json.JSONDecodeError, ValueError):
        print(f"错误: MESSAGE_IDS 格式不正确。应为一个JSON数组，但收到了: {message_ids_json}", file=sys.stderr)
        return 1

    downloaded_paths = []
    original_names = []

    print(f"正在使用用户会话初始化 Telegram 客户端...")
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("客户端创建成功。")
        # --- 修改: 循环处理所有 message_id ---
        for index, message_id in enumerate(message_ids):
            print(f"\n--- 正在处理文件 {index + 1}/{len(message_ids)} (Message ID: {message_id}) ---")
            for retry in range(3):
                try:
                    print(f"正在从聊天 {chat_id} 中获取消息 ID: {message_id}...")
                    message = await client.get_messages(chat_id, ids=message_id)

                    if not (message and message.media):
                        print(f"警告: 在消息 {message_id} 中未找到媒体文件。跳过。", file=sys.stderr)
                        break # 跳出重试循环，处理下一个 message_id

                    file_name = "unknown_file"
                    if hasattr(message, 'file') and hasattr(message.file, 'name'):
                        file_name = message.file.name
                    elif hasattr(message.media, 'document') and hasattr(message.media.document, 'attributes'):
                        for attr in message.media.document.attributes:
                            if hasattr(attr, 'file_name'):
                                file_name = attr.file_name; break

                    print(f"找到媒体文件: '{file_name}'")
                    start_time = time.time()
                    downloaded_file_path = await client.download_media(
                        message.media, file=file_name,
                        progress_callback=lambda current, total: progress_callback(current, total, start_time, file_name)
                    )
                    print(f"\n文件下载成功，本地路径: '{downloaded_file_path}'")
                    
                    downloaded_paths.append(downloaded_file_path)
                    original_names.append(file_name)
                    break # 成功，跳出重试循环

                except FileReferenceExpiredError:
                    print(f"警告: 文件引用已过期，将在3秒后重试... (尝试次数 {retry + 1}/3)")
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"错误: Telethon 操作失败 (消息ID {message_id}) - {e}", file=sys.stderr)
                    break # 发生其他错误，跳过此文件
            else: # 如果重试循环正常结束（即3次都失败）
                print(f"错误: 重试3次后仍然无法下载文件 (消息ID {message_id})。", file=sys.stderr)

    # --- 修改: 将所有结果写入 GITHUB_OUTPUT ---
    if output_file := os.getenv('GITHUB_OUTPUT'):
        with open(output_file, 'a') as f:
            # 使用多行字符串和特定分隔符来确保文件名中的空格等不会造成问题
            delimiter = "---END_OF_FILE_PATH---"
            print(f"file_paths<<{delimiter}", file=f)
            for path in downloaded_paths:
                print(path, file=f)
            print(delimiter, file=f)
            
            print(f"original_names<<{delimiter}", file=f)
            for name in original_names:
                print(name, file=f)
            print(delimiter, file=f)

    print(f"\n--- 所有任务处理完毕。共成功下载 {len(downloaded_paths)} 个文件。 ---")
    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main_async()))