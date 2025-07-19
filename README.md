# Telegram 大文件转存至 GitHub Releases 工具

这是一个高度自动化、健壮可靠的解决方案，能够将您在 Telegram 上收到的大文件（最大 2GB/4GB）转存到本 GitHub 仓库的 Releases 页面。

本项目采用 **Telegram 用户 API (通过 Telethon 库)** 进行文件下载，从而完美绕过了 Bot API 的 20MB 文件大小限制。后端触发器采用无服务器架构 (Serverless)，实现了低成本、免维护的 7x24 小时运行。

## 核心特性

- **支持大文件**: 轻松处理超过 20MB，最大可达 2GB (或 Premium 用户的 4GB) 的文件。
- **通用媒体捕获**: 能自动处理文件、照片、视频、音频等各类媒体消息。
- **实时进度反馈**: 在 GitHub Actions 的日志中，可以实时查看大文件的下载进度。
- **健壮的下载逻辑**: 集成了重试机制，能有效应对“文件引用过期”等临时性网络问题。
- **每日自动归档**: 所有文件会自动归类到以当天日期命名的 Release 中，方便查找和管理。
- **安全可靠**: 敏感的个人账户凭证（会话字符串）仅存储在 GitHub Secrets 中，代码和后端服务均不接触。

## 工作流程

1.  **触发**: 您（使用主号）将任何含有媒体的消息发送或转发给您的私人 Telegram 机器人。
2.  **Webhook (云平台)**: 部署在 Vercel 或 Zeabur 上的轻量级 Python 后端，通过 Webhook 即时接收到消息，并验证消息来源。
3.  **调度 (Dispatch)**: 后端提取消息的 `chat_id` 和 `message_id`，然后向本仓库发送一个 `repository_dispatch` 事件，触发 GitHub Action。
4.  **下载 (GitHub Action)**:
    - Action 启动一个虚拟机，并安装 `Telethon` 库。
    - 一个 Python 脚本 (`download_script.py`) 读取您存储在 GitHub Secrets 中的**主号** API 凭证。
    - 脚本以您的名义登录 Telegram，找到指定消息，并以高速下载大文件。
5.  **上传 (GitHub Action)**:
    - Action 使用官方的 `actions/create-release` 和 `actions/upload-release-asset` 工具。
    - 它会创建或更新一个以当天日期命名的 Release，并将下载好的文件作为 Asset 上传。

## 部署与配置指南

### 第 1 步：准备所有凭证
在开始前，请确保您已获取以下 **5 项**来自您**主号**的凭证：
- `Telegram API ID` (来自 `my.telegram.org`)
- `Telegram API Hash` (来自 `my.telegram.org`)
- `Telegram Session String` (通过在本地运行 `generate_session.py` 脚本生成)
- `Telegram Bot Token` (来自 `@BotFather`)
- `GitHub Personal Access Token (PAT)` (拥有 `repo` 权限)

### 第 2 步：部署后端服务 (Vercel/Zeabur)
1.  选择一个云平台并用 GitHub 账户登录。
2.  创建一个新项目，并关联此 GitHub 仓库。
3.  在项目的**环境变量**设置中，添加以下 4 个变量：
    - `TELEGRAM_BOT_TOKEN`: 你的机器人 Token
    - `YOUR_TELEGRAM_ID`: 你的**主号**的数字 ID
    - `GITHUB_REPO`: 本仓库的路径 (格式: `你的用户名/仓库名`)
    - `GITHUB_TOKEN`: 你的 GitHub PAT
4.  部署服务并获取其**公开 URL**。

### 第 3 步：配置 GitHub Secrets
在您的 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions` 中，添加 **5 个** Secrets：
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_STRING`
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`

### 第 4 步：设置 Telegram Webhook
在浏览器中访问以下 URL，将 `<...>` 部分替换为您的真实信息：
`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_DEPLOYED_URL>`
看到 `{"ok":true}` 即表示成功。

### 第 5 步：开始使用
一切就绪！现在，您可以向您的机器人发送任何大文件，稍等片刻，即可在本仓库的 **Releases** 页面看到它们被成功归档。