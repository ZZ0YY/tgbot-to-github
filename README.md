# Telegram 到 GitHub Releases 的通用媒体备份工具 (Rclone 增强版)

本项目提供一个高度自动化、极其健壮的解决方案，能够将您发送到 Telegram Bot 的**几乎所有类型**的媒体文件，以其**原始文件名（完美支持中文和特殊字符）**，可靠地上传到本 GitHub 仓库的 Releases 页面。

它通过集成强大的命令行工具 **Rclone**，彻底解决了文件名乱码、上传不可靠等痛点。

## 核心特性

- **通用媒体捕获**: 能自动处理文件、照片、视频、音频、GIF动图，甚至链接预览中的图片。
- **完美文件名支持**: 无论文件名包含中文、空格还是特殊符号，都能在 Release 中被正确显示。
- **工业级可靠性**: 使用 Rclone 进行文件上传，确保了传输的稳定性和健壮性。
- **每日自动归档**: 所有文件会自动归类到以当天日期命名的 Release 中，方便查找和管理。
- **无服务器架构**: 后端部署在 Vercel 或 Zeabur 等平台的免费套餐上，无需您维护服务器。

## 工作流程

1.  **触发**: 您将任何含有媒体的消息转发给您的私人 Telegram 机器人。
2.  **Webhook (云平台)**: 部署在云平台的轻量级 Python 后端，通过 Webhook 即时接收到消息。
3.  **信息提取与调度**: 后端智能地从消息中提取出媒体的 `file_id` 和原始文件名，然后安全地触发 GitHub Action 工作流。
4.  **下载 (GitHub Action)**: Action 启动一个虚拟机，运行 Python 脚本，通过 Bot API 将文件以其原始名称下载到临时目录。
5.  **通过 Rclone 同步**: Action 接着安装并动态配置 Rclone，用一条 `rclone copy` 命令，将下载好的文件高效、可靠地同步到 GitHub Releases。

## 部署与配置指南

### 第 1 步：准备工作
确保您已获取以下凭证：
1.  **Telegram Bot Token** (来自 `@BotFather`)
2.  您的个人 **Telegram 用户 ID** (数字，来自 `@userinfobot`)
3.  拥有 `repo` 权限的 **GitHub 个人访问令牌 (PAT)**

### 第 2 步：部署后端服务
1.  选择一个云平台 (如 Vercel, Zeabur)。
2.  创建一个新项目，并关联此 GitHub 仓库。
3.  在项目的**环境变量**设置中，添加以下 4 个变量：
    - `TELEGRAM_BOT_TOKEN`
    - `YOUR_TELEGRAM_ID`
    - `GITHUB_REPO` (本仓库的路径，如 `your-name/repo-name`)
    - `GITHUB_TOKEN` (您的 PAT)
4.  部署服务并获取其公开 URL。

### 第 3 步：配置 GitHub Secrets
在您的 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions` 中，添加 2 个 Secrets：
- `TELEGRAM_BOT_TOKEN`
- `GITHUB_TOKEN`

### 第 4 步：设置 Telegram Webhook
在浏览器中访问以下 URL，将 `<...>` 部分替换为您的真实信息：
`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_DEPLOYED_URL>`

### 第 5 步：开始使用
一切就绪！现在，您可以向您的机器人发送任何包含媒体文件的消息，稍等片刻，即可在本仓库的 **Releases** 页面看到它们被完美地归档。