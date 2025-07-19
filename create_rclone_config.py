# /create_rclone_config.py

import os

def main():
    """
    在 GitHub Actions 环境中，动态创建 Rclone 的配置文件。
    """
    rclone_token = os.getenv('RCLONE_GITHUB_TOKEN')

    if not rclone_token:
        print("::error::RCLONE_GITHUB_TOKEN is not set in environment variables!")
        exit(1)

    # 获取用户的主目录，确保路径的正确性
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".config", "rclone")
    config_file_path = os.path.join(config_dir, "rclone.conf")

    # 创建配置目录，如果它不存在
    os.makedirs(config_dir, exist_ok=True)
    
    # 定义配置文件的内容
    config_content = f"""
[github]
type = github
token = {rclone_token}
"""
    
    # 将配置内容写入文件
    try:
        with open(config_file_path, "w") as f:
            f.write(config_content)
        print(f"Successfully created rclone config at: {config_file_path}")
    except Exception as e:
        print(f"::error::Failed to write rclone config file: {e}")
        exit(1)

if __name__ == "__main__":
    main()