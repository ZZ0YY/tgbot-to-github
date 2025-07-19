# /download_script.py

import os
import sys
import asyncio
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FileReferenceExpiredError

def progress_callback(current, total, start_time, file_name):
    """一个用于在 Action 日志中打印下载进度的回调函数。"""
    if total == 0: return
    elapsed_time = time.time() - start_time
    percentage = current * 100 / total
    speed = current / (elapsed_time + 1e-9) / (1024 * 1024)
    if "last_print_time" not in progress_callback.__dict__: progress_callback.last_print_time = 0
    if time.time() - progress_callback.last_print_time > 2 or current == total:
        print(f"Downloading '{file_name}': {percentage:.1f}% ({current/(1024*1024):.2f}/{total/(1024*1024):.2f} MB) at {speed:.2f} MB/s")
        progress_callback.last_print_time = time.time()

async def main_async():
    """主异步函数，负责认证、重试和下载。"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_string = os.getenv('TELEGRAM_SESSION_STRING')
    bot_username = os.getenv('BOT_USERNAME') # 新增：获取机器人用户名
    message_id_str = os.getenv('MESSAGE_ID')

    if not all([api_id, api_hash, session_string, bot_username, message_id_str]):
        print("错误: 缺少关键环境变量 (需要 BOT_USERNAME)。", file=sys.stderr)
        return 1
        
    message_id = int(message_id_str)

    print("正在使用用户会话初始化 Telegram 客户端...")
    
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("客户端创建成功。")
        for retry in range(3):
            try:
                # --- 核心修改：使用机器人用户名作为聊天的实体 ---
                print(f"正在与机器人 '{bot_username}' 的聊天中获取消息 ID: {message_id}...")
                message = await client.get_messages(bot_username, ids=message_id)

                if not message:
                    print("错误: 无法获取到消息对象。", file=sys.stderr)
                    return 1

                print(f"\n--- 消息对象简报 ---\n{message.text or message.caption or 'No Text'}\n---------------------\n")

                if message.media:
                    file_name = "unknown_file"
                    if hasattr(message, 'file') and hasattr(message.file, 'name'):
                        file_name = message.file.name
                    elif hasattr(message.media, 'document') and hasattr(message.media.document, 'attributes'):
                        for attr in message.media.document.attributes:
                            if hasattr(attr, 'file_name'):
                                file_name = attr.file_name
                                break
                    
                    print(f"找到媒体文件: '{file_name}'")
                    start_time = time.time()
                    downloaded_file_path = await client.download_media(
                        message.media,
                        file=file_name,
                        progress_callback=lambda current, total: progress_callback(current, total, start_time, file_name)
                    )
                    
                    print(f"\n文件下载成功，本地路径: '{downloaded_file_path}'")
                    if output_file := os.getenv('GITHUB_OUTPUT'):
                        with open(output_file, 'a') as f:
                            print(f"file_path={downloaded_file_path}", file=f)
                            print(f"original_name={file_name}", file=f)
                    return 0
                else:
                    print("错误: 在消息中未找到媒体。", file=sys.stderr)
                    return 1

            except FileReferenceExpiredError:
                print(f"警告: 文件引用已过期，将在3秒后重试... (尝试次数 {retry + 1}/3)")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"错误: Telethon 操作失败 - {e}", file=sys.stderr)
                return 1
        print("错误: 重试3次后仍然无法下载文件。", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main_async()))