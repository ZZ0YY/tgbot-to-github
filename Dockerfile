# 使用官方的轻量级 Python 镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件到工作目录
COPY requirements.txt .

# 安装依赖
# --no-cache-dir 选项可以减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码到工作目录
COPY . .

# 暴露 Flask 默认的 5000 端口
EXPOSE 5000

# 启动应用的命令
# 使用 gunicorn 运行，并监听所有网络接口的 5000 端口
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api.index:app"]