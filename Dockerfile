# 使用官方的轻量级 Python 镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件到工作目录
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码到工作目录
COPY . .

# 启动应用的命令
# 使用 shell form (不带方括号和引号)，这样环境变量才能被正确解析
CMD gunicorn --bind "0.0.0.0:${PORT:-8080}" api.index:app