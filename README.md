# Telegram 全自动大文件备份工具 (最终版)

本工具提供一个“一劳永逸”的解决方案，能够将您在指定的 Telegram 私有群组中发送的任何大文件（最大 2GB/4GB），**全自动地**、**无需任何命令地**，备份到本 GitHub 仓库的 Releases 页面。

## 核心特性

- **完全自动**: 您只需将文件发到群组，后续所有流程自动完成。
- **支持大文件**: 轻松处理最大 2GB/4GB 的文件。
- **通用媒体捕获**: 支持文件、照片、视频、相册等多种媒体类型。
- **清晰的状态反馈**: 机器人会在群组中实时回复任务接收状态，让您对流程了如指掌。
- **健壮可靠**: 下载脚本集成了重试机制，上传流程使用官方 GitHub Actions，确保了端到端的可靠性。
- **每日自动归档**: 所有文件会自动归类到以当天日期命名的 Release 中。
- **安全**: 您的个人账户凭证（会话字符串）仅存储在 GitHub Secrets 中，与后端服务完全隔离。

## 工作流程

1.  **建立工作空间**: 您需要创建一个私有群组，并将您的主号和机器人加入，同时将机器人设为管理员。
2.  **触发**: 您将任何媒体文件或相册发送/转发到此私有群组。
3.  **Webhook (机器人)**: 作为群管理员，机器人立即检测到新消息并通过 Webhook 通知后端服务。
4.  **调度 (后端)**: 后端验证消息来自授权的群组，然后为每个媒体文件触发一次 GitHub Action，并**在群组中回复状态消息**。
5.  **下载 (用户 API)**: Action 使用您的主号 API 凭证登录，进入该群组，找到指定的消息并高速下载文件。
6.  **上传 (官方 Action)**: Action 使用官方工具创建或更新当天的 Release，并将下载好的文件作为 Asset 上传。

## 部署与配置指南

### 第 1 步：准备凭证
- **主号凭证**: `API ID`, `API Hash`, `Session String`。
- **机器人凭证**: `Bot Token`。
- **GitHub 凭证**: `Personal Access Token (PAT)` (需 `repo` 权限)。
- **群组 ID**: 一个以 `-` 开头的负数，通过将群内消息转发给 `@userinfobot` 获取。

### 第 2 步：部署后端服务 (Vercel/Zeabur)
1.  关联此 GitHub 仓库到您的云平台。
2.  在项目的**环境变量**中，添加 4 个变量：
    - `TELEGRAM_BOT_TOKEN`
    - `AUTHORIZED_CHAT_ID` (您的私有群组 ID)
    - `GITHUB_REPO` (本仓库路径, `用户名/仓库名`)
    - `GITHUB_TOKEN` (您的 PAT)
3.  部署服务并获取其**公开 URL**。

### 第 3 步：配置 GitHub Secrets
在您的 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions` 中，添加 5 个 Secrets：
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_STRING`
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`

### 第 4 步：设置 Telegram Webhook
在浏览器中访问以下 URL (替换 `<...>` 部分)：
`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_DEPLOYED_URL>`

### 第 5 步：开始使用
现在，只需将任何文件或相册发送到您的私有群组，即可享受全自动的备份体验！