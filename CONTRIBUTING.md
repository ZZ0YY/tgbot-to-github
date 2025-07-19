# 开发者与贡献指南

我们非常欢迎社区的开发者帮助我们改进这个项目，特别是解决当前存在的非 ASCII 文件名兼容性问题。

## 技术架构概览

本项目采用解耦的 Serverless 架构，主要由两部分组成：

1.  **Webhook 后端 (`/api/index.py`)**:
    - 一个轻量级的 Python Flask 应用。
    - 设计为部署在 Vercel 等 Serverless 平台。
    - **职责**: 接收 Telegram Bot 的 Webhook 更新，验证消息来源（是否来自授权的私有群组），提取 `chat_id` 和 `message_id`，然后通过 `repository_dispatch` 事件触发 GitHub Action。它不处理任何文件下载。

2.  **GitHub Action 工作流 (`.github/workflows/create_release_asset.yml`)**:
    - **职责**: 执行实际的文件处理任务。
    - **`download_script.py`**: 一个使用 `Telethon` 库的 Python 脚本，负责以用户身份登录 Telegram，下载指定的大文件。
    - **Release Management**: 使用 `actions/create-release` 和 `actions/upload-release-asset` 这两个 GitHub 官方 Action 来管理 Releases 的创建和文件上传。

## 核心挑战：非 ASCII 文件名处理

### 问题描述
当前系统的瓶颈在于，即使 `download_script.py` 在 Actions 虚拟机中成功创建了带有正确中文名的文件，但在调用 `actions/upload-release-asset` 进行上传时，最终保存在 Release 中的文件名中的中文字符会被移除或替换。

**日志证据**:
- 下载脚本成功将文件保存为 `./downloads/藏海传12集.mkv`。
- `upload-release-asset` 步骤的 `with.asset_name` 参数也正确接收到了 `藏海传12集.mkv` 这个字符串。
- 但最终上传到 Release 的文件名变为 `12.mkv`。

这强烈暗示问题出在 `actions/upload-release-asset` Action 的内部实现，或者是它所依赖的 GitHub API 上传接口与 shell 环境交互的某个环节。

### 潜在的解决方案方向

我们欢迎任何能够解决此问题的 Pull Request。一些可能的探索方向包括：

1.  **直接与 GitHub API 交互**: 放弃使用 `actions/upload-release-asset`，改用 `curl` 手动构建 `multipart/form-data` POST 请求。这需要非常精确地处理 HTTP Headers，特别是 `Content-Disposition` 中的 `filename*` 字段，以符合 RFC 5987/2231 对非 ASCII 字符的编码规范。我们之前的尝试失败了，但可能存在更精确的 `curl` 用法。

2.  **使用不同的上传工具**: 探索是否有其他 Action 或命令行工具在处理 UTF-8 文件名上传时表现更健壮。

3.  **文件名编码策略**: 在上传前，对文件名进行某种可逆的编码（如 Punycode），并在项目文档中提供一个解码工具/方法。这是一种妥协方案。

## 如何贡献

1.  **Fork 本仓库**。
2.  **从 `dev` 分支创建您自己的特性分支**:
    ```bash
    git checkout -b feature/fix-unicode-filenames dev
    ```
3.  **进行修改**: 在您的新分支上进行代码修改和测试。
4.  **提交 Pull Request**: 将您的特性分支向本仓库的 **`dev` 分支**发起 Pull Request。
5.  **描述您的解决方案**: 在 PR 的描述中，请清晰地解释您的改动、解决问题的思路，以及您是如何进行测试的。

我们期待您的贡献！