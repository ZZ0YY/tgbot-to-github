# Telegram 大文件转存至 GitHub Releases (用户 API 最终版)

本项目提供一个高度自动化、健壮可靠的解决方案，能够将您发送到 Telegram Bot 的大文件（最大 2GB/4GB），稳定地转存到本 GitHub 仓库的 Releases 页面。

本项目采用 **Telegram 用户 API (通过 Telethon 库)** 进行文件下载，从而完美绕过了 Bot API 的 20MB 文件大小限制。后端触发器采用无服务器架构 (Serverless)，实现了低成本、免维护的 7x24 小时运行。

## 工作流程

1.  **触发**: 您（使用主号）将任何含有媒体的消息发送或转发给您的私人 Telegram 机器人。
2.  **Webhook (云平台)**: 部署在 Vercel 或 Zeabur 上的轻量级 Python 后端，通过 Webhook 即时接收到消息，并验证消息来源。
3.  **调度 (Dispatch)**: 后端提取**消息 ID** 和**机器人自身的用户名**，然后安全地触发 GitHub Action 工作流。
4.  **下载 (GitHub Action)**:
    - Action 启动一个虚拟机，并安装 `Telethon` 库。
    - 一个 Python 脚本 (`download_script.py`) 读取您存储在 GitHub Secrets 中的**主号** API 凭证。
    - 脚本以您的名义登录 Telegram，并在**与指定机器人的对话**中找到该消息，然后以高速下载大文件，并提供实时进度。
5.  **上传 (GitHub Action)**:
    - Action 使用官方的 `actions/create-release` 和 `actions/upload-release-asset` 工具。
    - 它会创建或更新一个以当天日期命名的 Release，并将下载好的文件作为 Asset 上传。

## 部署与配置指南

### 第 1 步：准备所有凭证
- **主号凭证**: `API ID`, `API Hash` (来自 `my.telegram.org`), `Session String` (通过 `generate_session.py` 生成)。
- **机器人凭证**: `Bot Token` (来自 `@BotFather`), `机器人用户名` (例如 `@your_bot_name`)。
- **GitHub 凭证**: 拥有 `repo` 权限的 `Personal Access Token (PAT)`。
- **您的 Telegram ID**: `个人数字ID` (来自 `@userinfobot`)。

### 第 2 步：部署后端服务 (Vercel/Zeabur)
1.  选择一个云平台并关联此 GitHub 仓库。
2.  在项目的**环境变量**设置中，添加以下 **5 个**变量：
    - `TELEGRAM_BOT_TOKEN`
    - `YOUR_TELEGRAM_ID`
    - `GITHUB_REPO` (本仓库路径, `用户名/仓库名`)
    - `GITHUB_TOKEN` (您的 PAT)
    - `BOT_USERNAME` (您的机器人用户名, 如 `@my_bot`)
3.  部署服务并获取其**公开 URL**。

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

### 第 5 步：开始使用
一切就绪！现在，您可以向您的机器人发送任何大文件，稍等片刻，即可在本仓库的 **Releases** 页面看到它们被成功归档。