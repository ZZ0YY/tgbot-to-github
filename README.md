# Telegram 全自动大文件备份工具 (v2.0 - 用户 API 版)

![Workflow Status](https://github.com/ZZ0YY/tgbot-to-github/actions/workflows/create_release_asset.yml/badge.svg)

本项目提供一个高度自动化的解决方案，能够将您在指定的 Telegram 私有群组中发送的任何大文件（最大 2GB），**全自动地**备份到本 GitHub 仓库的 **Releases** 页面。

## 核心特性

- ✅ **完全自动**: 您只需将文件发到指定的私有群组，后续所有流程自动完成，无需任何额外命令。
- ✅ **支持大文件**: 采用 Telegram 用户 API (通过 Telethon 库) 进行下载，轻松处理 20MB 以上，最大可达 2GB 的文件。
- ✅ **通用媒体捕获**: 支持文件、照片、视频、相册等多种媒体类型。
- ✅ **清晰的状态反馈**: 机器人在收到文件或相册后，会在群组中实时回复任务接收状态。
- ✅ **健壮可靠**: 下载脚本集成了重试机制，上传流程使用官方 GitHub Actions，确保了端到端的可靠性。
- ✅ **每日自动归档**: 所有文件会自动归类到以当天日期命名的 Release 中，方便查找和管理。
- ✅ **安全**: 您的个人账户凭证（会话字符串）仅存储在 GitHub Secrets 中，与后端服务完全隔离。

---

## ⚠️ 已知问题：非 ASCII 文件名兼容性

目前，本项目的核心功能已稳定运行，但存在一个已知的兼容性问题：

**当上传的文件名包含非 ASCII 字符（如中文、日文、特殊符号等）时，最终保存在 GitHub Releases 中的文件名会被“净化”，导致这些字符丢失或被替换。**

例如，`藏海传12集.mkv` 可能会被保存为 `12.mkv`。

我们已经尝试了多种编码和工具，但问题似乎源于 GitHub Actions 生态中某些底层工具对 UTF-8 文件名的处理方式。这是一个具有挑战性的问题，我们**非常欢迎社区的开发者们**能够提供解决方案。如果您有兴趣，请参考本仓库的 **[CONTRIBUTING.md](CONTRIBUTING.md)** 文档。

---

## 快速上手指南

### 第 1 步：准备工作 (Checklist)

在开始部署前，请确保您已获取以下 **6 项**凭证：

1.  **主号 API ID**: 从 [my.telegram.org](https://my.telegram.org) 获取。
2.  **主号 API Hash**: 同上。
3.  **主号 Session String**: 通过在本地电脑或 Termux 运行 `generate_session.py` 脚本生成（详见附录A）。
4.  **机器人 Bot Token**: 从 [@BotFather](https://t.me/BotFather) 创建机器人后获取。
5.  **GitHub Personal Access Token (PAT)**: 从您的 GitHub 账户生成，需要 `repo` 权限。
6.  **私有群组 ID**: 一个以 `-100...` 开头的数字 ID（详见附录B）。

### 第 2 步：部署后端服务

我们提供了两个推荐的免费 Serverless 平台：**Zeabur** 和 **Vercel**。

#### **方案 A: 部署到 Zeabur (推荐)**

Zeabur 对 Docker 有良好的支持，且网络在国内访问较为稳定。

1.  登录 [Zeabur](https://zeabur.com/) 并创建一个新项目。
2.  选择 `Deploy New Service` -> `Git` -> `GitHub`，然后选择您 Fork 或克隆的本仓库。
3.  Zeabur 会自动检测到项目中的 `Dockerfile` 并开始部署，您无需进行任何构建配置。
4.  部署完成后，进入服务的 `Variables` (变量) 标签页，添加以下 **4 个**环境变量：
    - `TELEGRAM_BOT_TOKEN`
    - `AUTHORIZED_CHAT_ID` (填入您的私有群组 ID)
    - `GITHUB_REPO` (您的仓库路径, 如 `ZZ0YY/tgbot-to-github`)
    - `GITHUB_TOKEN` (您的 PAT)
5.  进入 `Networking` (网络) 标签页，生成并复制您的公开域名 (如 `xxx.zeabur.app`)。

#### **方案 B: 部署到 Vercel**

Vercel 拥有强大的全球网络和极快的部署速度，但部分用户曾遇到 Telegram Webhook 请求无法到达的问题。

> **社区测试邀请**: 我们不确定 Vercel 无法响应的问题是暂时的，还是与特定网络区域有关。如果您选择使用 Vercel 并部署成功，欢迎在 [Issues](https://github.com/ZZ0YY/tgbot-to-github/issues) 中分享您的使用体验。

1.  点击下面的按钮一键部署到 Vercel：
    [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FZZ0YY%2Ftgbot-to-github)
2.  在 Vercel 的部署页面，展开 **Environment Variables** (环境变量) 区域，添加与 Zeabur 方案中完全相同的 **4 个**环境变量。
3.  点击 **Deploy**，等待部署完成，然后从 Vercel Dashboard 复制您的**应用域名** (如 `xxx.vercel.app`)。

### 第 3 步：配置 GitHub Secrets

在您的 GitHub 仓库中，进入 `Settings` -> `Secrets and variables` -> `Actions`，添加 **5 个** Secrets：
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_STRING`
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`

### 第 4 步：连接 Telegram 与后端

在浏览器中访问以下 URL，将 `<...>` 部分替换为您的真实信息，以设置 Webhook：
`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_DEPLOYED_DOMAIN>`
*(请使用您在第 2 步中从 Zeabur 或 Vercel 获取的域名)*

### 第 5 步：开始使用！

1.  将您的机器人和主号都添加到您之前创建的私有群组中。
2.  将机器人**设为群管理员**。
3.  现在，只需将任何文件（小于 2GB）发送或转发到这个群组，即可享受全自动的备份体验！

---

## 附录

### A: 如何生成 Session String

1.  在您的电脑上安装 Python 和 `telethon` (`pip install telethon`)。
2.  创建一个 `generate_session.py` 文件，填入以下内容，并将 `API_ID` 和 `API_HASH` 替换为您自己的：
    ```python
    import asyncio
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

    async def main():
        API_ID = 1234567 # 替换
        API_HASH = 'YOUR_API_HASH' # 替换
        async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
            print("Your session string is:\n", client.session.save())
    
    asyncio.run(main())
    ```
3.  运行 `python generate_session.py`，根据提示输入手机号、验证码和二次验证密码，即可获得 Session String。

### B: 如何获取私有群组 ID

1.  创建一个新的**私有群组**。
2.  将您的主号和机器人加入。
3.  将机器人**设为管理员**。
4.  在群组中发送一条任意消息。
5.  将这条消息转发给 **@userinfobot** 或 **@RawDataBot**。
6.  机器人回复的 `forward_from_chat` -> `id` 就是您的群组 ID (一个以 `-100...` 开头的负数)。

---
*本项目由 AI 辅助开发。欢迎社区贡献力量，共同解决已知问题。*