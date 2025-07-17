# Telegram 通用媒体上传机器人

这是一个功能强大、健壮且自动化的机器人项目。它能够捕捉你发送到 Telegram 的几乎所有类型的媒体文件，并自动将它们上传到你的 GitHub Releases 页面，作为一个稳定可靠的个人媒体归档方案。

**核心特性**:
*   **通用媒体支持**: 能够智能处理各种媒体类型，包括但不限于：单张照片（带或不带说明文字）、文件、视频、GIF动图、音频、语音、贴纸，甚至能妥善处理相册（Media Group）以避免重复。
*   **智能文件名**: 会尝试使用媒体的说明文字（Caption）来生成更具可读性的文件名。
*   **部署灵活**: 提供两种部署方式，你可以根据自己的资源选择部署在**云平台 (PaaS)** 或你自己的**私有云服务器 (VPS)** 上。

**重要限制**: 此版本基于标准的 Telegram Bot API，因此在下载文件时存在 **20MB** 的大小限制。如需处理超大文件，需要切换到基于用户 API (Telethon) 的方案。

## 工作流程

1.  **触发**: 你（用主号）将任何包含媒体的消息转发给你的私人机器人。
2.  **Webhook 与媒体检测**: 部署在云端（PaaS 或 VPS）的机器人后端通过 Webhook 接收消息。其内置的通用捕获逻辑会识别媒体类型、提取 `file_id` 并生成文件名。
3.  **触发 Action**: 后端安全地触发一个 GitHub Action 工作流，并传递文件的关键信息。
4.  **下载与上传**: GitHub Action 被唤醒，运行脚本从 Telegram 下载媒体文件，然后将其上传到一个按日期自动管理的 GitHub Release 中。

---

## 部署与配置指南

### **第一步：准备所有凭证**

在开始之前，请确保你已准备好以下 **4 项**关键信息：
1.  **Telegram 机器人 Token** (从 `@BotFather` 获取)
2.  **你的个人 Telegram ID** (一个纯数字ID, 从 `@userinfobot` 获取)
3.  **GitHub 个人访问令牌 (PAT)** (一个拥有 `repo` 权限的 `ghp_` 开头的令牌)
4.  **当前 GitHub 仓库的名称** (格式为 `你的用户名/你的仓库名`)

### **第二步：配置 GitHub Secrets**

进入当前仓库的 `Settings` -> `Secrets and variables` -> `Actions`，添加 **1 个**仓库秘密（Secret）：
*   **`TELEGRAM_BOT_TOKEN`**: 值为你的机器人 Token。这是为了让 GitHub Action 能够下载文件。

---

### **第三步：部署机器人后端 (选择一种方式)**

你需要将机器人后端部署到公网可以访问的地方，以接收 Telegram 的 Webhook 请求。

#### **方式 A：部署到云平台 (PaaS - 推荐新手)**

此方式简单快捷，无需管理服务器。推荐使用 [Zeabur](https://zeabur.com/) 或 [Vercel](https://vercel.com/)。

1.  **关联 GitHub 仓库**: 在你选择的云平台上创建一个新项目，并关联此 GitHub 仓库。
2.  **设置环境变量**: 在平台的项目设置中，添加在**第一步**中准备好的全部 **4 个**凭证作为环境变量：
    *   `TELEGRAM_BOT_TOKEN`
    *   `YOUR_TELEGRAM_ID`
    *   `GITHUB_REPO`
    *   `GITHUB_TOKEN`
3.  **部署**: 平台会自动检测项目中的 `Dockerfile` 并完成部署。
4.  **获取公开域名**: 部署成功后，从平台获取一个公开的 URL (例如 `https://your-bot.zeabur.app`)。
5.  **部署完成后，请直接跳转到第四步**。

---

#### **方式 B：部署到你自己的云服务器 (VPS)**

此方式给予你完全的控制权，适合有服务器管理经验的用户。

1.  **准备服务器**:
    *   确保你有一台拥有公网 IP 的云服务器。
    *   在服务器上安装 `Docker` 和 `docker-compose`。对于基于 Debian/Ubuntu 的系统，命令如下：
        ```bash
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose
        sudo systemctl start docker
        sudo systemctl enable docker
        ```

2.  **克隆项目到服务器**:
    ```bash
    git clone https://github.com/你的用户名/你的仓库名.git
    cd 你的仓库名/
    ```

3.  **创建并配置环境变量文件**:
    *   复制示例文件：`cp .env.example .env`
    *   使用文本编辑器（如 `nano`）打开并编辑 `.env` 文件：`nano .env`
    *   在编辑器中，填入在**第一步**中准备好的全部 **4 个**凭证，然后保存退出 (`Ctrl+X`, `Y`, `Enter`)。

4.  **启动服务**:
    *   在项目根目录下，执行以下命令在后台启动服务：
        ```bash
        sudo docker-compose up -d
        ```
    *   服务将在容器内运行，并监听服务器的 `5000` 端口（可在 `docker-compose.yml` 中修改）。
    *   你可以使用 `sudo docker-compose logs -f` 查看实时日志以确认服务正常运行。

5.  **配置反向代理和域名 (强烈推荐)**:
    *   为了让 Webhook 稳定工作，你需要一个域名指向你服务器的公网 IP。
    *   使用 Nginx 或 Caddy 等 Web 服务器作为反向代理，将来自域名的 HTTPS (443) 请求安全地转发到本地的 `http://localhost:5000`。
    *   这将为你提供一个安全的公开 URL，例如 `https://your-domain.com`。
    *   **部署完成后，请直接跳转到第四步**。

---

### **第四步：设置 Telegram Webhook**

这是连接 Telegram 和你的机器人后端的最后一步。构建以下 URL，并在浏览器中访问它一次：

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<你的公开域名>
```

*   将 `<YOUR_BOT_TOKEN>` 替换为你的机器人 Token。
*   将 `<你的公开域名>` 替换为你在**第三步**中获取的 **PaaS 平台域名**或你**自己配置的服务器域名**。

浏览器返回 `{"ok":true, ...}` 即表示设置成功。

### **第五步：开始使用！**

一切就绪！现在，你可以向你的机器人发送任何包含媒体文件的消息，它们都会被自动、安全地归档到本仓库的 `Releases` 页面中。