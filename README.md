# Telegram to GitHub Releases Bot (Bot API Version)

这是一个自动化的机器人项目，它能接收你发送到 Telegram Bot 的文件，并自动将这些文件作为 Release Assets 上传到本 GitHub 仓库。

**注意**: 此版本使用标准的 Telegram Bot API，因此存在 **20MB** 的文件大小限制。对于需要处理大于 20MB 文件的场景，请考虑使用基于用户 API (Telethon/Pyrogram) 的方案。

## 工作流程

1.  **用户操作**: 你将一个文件（小于 20MB）发送给一个私有的 Telegram 机器人。
2.  **机器人后端 (Serverless)**: 部署在云平台（如 Vercel, Zeabur）的机器人后端通过 Webhook 接收到文件信息。
3.  **触发 Action**: 后端不直接处理文件，而是向本仓库发送一个 `repository_dispatch` 事件，触发 GitHub Action 工作流。
4.  **GitHub Action 执行**:
    *   被唤醒的 Action 工作流启动一个虚拟机。
    *   虚拟机中的脚本使用 **Bot API** 从 Telegram 下载文件。
    *   下载完成后，脚本将文件上传到一个按天组织的 GitHub Release 中。如果当天的 Release 已存在，则将文件追加为新的 Asset。

## 项目结构

```
.
├── .github/
│   └── workflows/
│       └── create_release_asset.yml  # GitHub Action 工作流
├── api/
│   └── index.py                      # 机器人后端 (Serverless Function)
├── Dockerfile                        # 用于云平台部署
├── download_script.py                # Action 下载脚本
├── requirements.txt                  # Python 依赖
└── README.md                         # 本文档
```

## 部署与配置指南

### 第一步：获取所有必需的凭证

在开始之前，请准备好以下信息：

1.  **Telegram Bot Token**: 从 [@BotFather](https://t.me/BotFather) 获取。
2.  **个人 Telegram ID**: 一个纯数字 ID，从 [@userinfobot](https://t.me/userinfobot) 获取。
3.  **GitHub Personal Access Token**: 一个拥有 `repo` 权限的 GitHub 个人访问令牌（Classic）。
4.  **GitHub 仓库名称**: 本仓库的名称，格式为 `你的用户名/你的仓库名`。

### 第二步：部署机器人后端

我们推荐使用 [Zeabur](https://zeabur.com/) 或 [Vercel](https://vercel.com/) 等支持 Serverless Function 的云平台进行部署。

1.  **关联 GitHub 仓库**: 在你选择的云平台上创建一个新项目，并关联此 GitHub 仓库。
2.  **设置环境变量**: 在平台的项目设置中，添加以下 **4 个**环境变量：
    *   `TELEGRAM_BOT_TOKEN`: (你的 Bot Token)
    *   `YOUR_TELEGRAM_ID`: (你的个人 Telegram ID)
    *   `GITHUB_REPO`: (你的仓库名称)
    *   `GITHUB_TOKEN`: (你的 GitHub PAT)
3.  **部署**: 平台会自动检测 `Dockerfile` (Zeabur) 或 `api/` 目录 (Vercel) 并完成部署。
4.  **获取域名**: 部署成功后，从平台获取一个公开的 URL (例如 `https://your-bot.zeabur.app`)。

### 第三步：配置 GitHub Actions

1.  进入本 GitHub 仓库的 `Settings` -> `Secrets and variables` -> `Actions`。
2.  添加一个名为 `TELEGRAM_BOT_TOKEN` 的 **Repository Secret**，值为你的机器人 Token。这是为了让 Action 能够下载文件。

### 第四步：设置 Telegram Webhook

这是连接 Telegram 和你的机器人后端的最后一步。构建以下 URL，并在浏览器中访问它一次：

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_DEPLOYED_URL>
```

将 `<YOUR_BOT_TOKEN>` 替换为你的机器人 Token，将 `<YOUR_DEPLOYED_URL>` 替换为你在第二步中获取的云平台域名。

如果浏览器返回 `{"ok":true, ...}`，则表示设置成功。

### 第五步：开始使用

一切就绪！现在，你可以直接向你的机器人发送文件（小于 20MB），它会自动出现在本仓库的 `Releases` 页面中。