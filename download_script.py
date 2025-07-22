# /download_script.py

import os
import sys
import asyncio
import time
import json
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FileReferenceExpiredError

# --- 修改: 进度条回调函数现在需要一个锁来避免输出混乱 ---
async def progress_callback(current, total, start_time, file_name, lock):
    if total == 0: return
    elapsed_time = time.time() - start_time
    percentage = current * 100 / total
    speed = current / (elapsed_time + 1e-9) / (1024 * 1024)
    
    # 尝试获取锁，但如果获取不到就立即返回，避免阻塞下载
    if not lock.locked():
        async with lock:
            # 再次检查，因为在等待锁的时候可能有其他任务已经打印了
            if "last_print_time" not in progress_callback.__dict__:
                progress_callback.last_print_time = 0
            if time.time() - progress_callback.last_print_time > 1 or current == total:
                print(f"Downloading '{file_name}': {percentage:.1f}% ({current/(1024*1024):.2f}/{total/(1024*1024):.2f} MB) at {speed:.2f} MB/s")
                progress_callback.last_print_time = time.time()

# --- 新增: 封装单个文件下载逻辑的异步任务函数 ---
async def download_file_task(client, chat_id, message_id, lock):
    """
    一个独立的、可并发执行的任务，负责下载单个文件。
    成功则返回 (路径, 文件名)，失败则会抛出异常。
    """
    for retry in range(3):
        try:
            message = await client.get_messages(chat_id, ids=message_id)

            if not (message and message.media):
                raise ValueError(f"消息 {message_id} 中未找到媒体文件。")

            file_name = "unknown_file"
            if hasattr(message, 'file') and hasattr(message.file, 'name'):
                file_name = message.file.name
            elif hasattr(message.media, 'document') and hasattr(message.media.document, 'attributes'):
                for attr in message.media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        break
            
            print(f"任务启动: 准备下载 '{file_name}' (from message {message_id})")
            start_time = time.time()
            
            # 创建一个偏函数或 lambda 来传递额外的 `lock` 参数
            callback = lambda current, total: progress_callback(current, total, start_time, file_name, lock)
            
            downloaded_file_path = await client.download_media(
                message.media,
                file=file_name,
                progress_callback=callback
            )
            
            print(f"✅ 下载成功: '{file_name}' -> '{downloaded_file_path}'")
            return downloaded_file_path, file_name # 成功时返回元组

        except FileReferenceExpiredError:
            print(f"警告: 文件引用已过期 (消息ID {message_id})，将在3秒后重试... (尝试次数 {retry + 1}/3)")
            await asyncio.sleep(3)
        # 其他异常直接向上抛出，由 gather 捕获
        except Exception as e:
            # 抛出更具信息量的异常
            raise RuntimeError(f"处理消息ID {message_id} ('{file_name}') 时发生不可恢复的错误: {e}") from e

    # 如果三次重试都失败了
    raise RuntimeError(f"重试3次后仍然无法下载文件 (消息ID {message_id})。")

async def main_async():
    api_id, api_hash, session_string, chat_id_str, message_ids_json = (os.getenv(k) for k in ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_SESSION_STRING', 'CHAT_ID', 'MESSAGE_IDS'])

    if not all([api_id, api_hash, session_string, chat_id_str, message_ids_json]):
        print("错误: 缺少关键环境变量。", file=sys.stderr)
        return 1
    
    chat_id = int(chat_id_str)
    try:
        message_ids = json.loads(message_ids_json)
        if not isinstance(message_ids, list): raise ValueError()
    except (json.JSONDecodeError, ValueError):
        print(f"错误: MESSAGE_IDS 格式不正确。", file=sys.stderr)
        return 1

    downloaded_paths = []
    original_names = []
    
    # --- 新增: 用于同步打印进度的锁 ---
    progress_print_lock = asyncio.Lock()

    print("正在使用用户会话初始化 Telegram 客户端...")
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print(f"客户端创建成功。准备并发下载 {len(message_ids)} 个文件...")
        
        # --- 核心修改: 创建所有下载任务 ---
        tasks = [download_file_task(client, chat_id, msg_id, progress_print_lock) for msg_id in message_ids]
        
        # --- 核心修改: 并发执行所有任务，并允许部分任务失败 ---
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n--- 所有下载任务已完成，正在处理结果 ---")
        
        # --- 核心修改: 分类处理成功和失败的结果 ---
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                # 如果结果是一个异常，打印错误信息
                print(f"❌ 任务失败 (源消息ID: {message_ids[i]}): {res}", file=sys.stderr)
            else:
                # 如果结果是 (路径, 文件名) 元组，记录下来
                path, name = res
                downloaded_paths.append(path)
                original_names.append(name)

    if not downloaded_paths:
        print("\n所有文件都下载失败了，没有可上传的文件。", file=sys.stderr)
        # 即使全部失败，我们仍然认为脚本本身是成功运行的，所以返回0
        # GitHub Actions 工作流会因为没有资产可传而跳过上传步骤。
        return 0

    if output_file := os.getenv('GITHUB_OUTPUT'):
        with open(output_file, 'a') as f:
            delimiter = "---END_OF_FILE_PATH---"
            print(f"file_paths<<{delimiter}", file=f)
            for path in downloaded_paths:
                print(path, file=f)
            print(delimiter, file=f)
            
            print(f"original_names<<{delimiter}", file=f)
            for name in original_names:
                print(name, file=f)
            print(delimiter, file=f)

    total_count = len(message_ids)
    success_count = len(downloaded_paths)
    failure_count = total_count - success_count
    print(f"\n--- 最终报告 ---")
    print(f"总任务数: {total_count}")
    print(f"✅ 成功下载: {success_count}")
    print(f"❌ 失败: {failure_count}")
    print(f"------------------")

    # 脚本本身执行成功，返回0，让 runner 继续执行上传步骤
    return 0

if __name__ == '__main__':
    # 在 Windows 上，可能需要设置不同的事件循环策略，但在 GitHub Actions (Linux) 上默认即可
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main_async()))