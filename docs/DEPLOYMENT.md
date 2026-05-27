# Telegram Bot 部署指南

## 目录

- [环境要求](#环境要求)
- [获取凭证](#获取凭证)
- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [云服务器部署](#云服务器部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 环境要求

- Python 3.10+
- Telegram Bot Token
- Telegram API ID 和 Hash
- OpenAI API Key (或其他 AI 提供商)

## 获取凭证

### 1. Telegram Bot Token

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 按提示输入机器人名称和用户名
4. 获取 Bot Token

### 2. Telegram API ID 和 Hash

1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 使用手机号登录
3. 进入 "API development tools"
4. 填写应用信息（任意名称即可）
5. 获取 `api_id` 和 `api_hash`

### 3. OpenAI API Key

1. 访问 [https://platform.openai.com](https://platform.openai.com)
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新的 API Key

## 本地部署

### 1. 克隆项目

```bash
git clone https://github.com/liuweiqiang0523/tg-chat-summary.git
cd tg-chat-summary
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
BOT_TOKEN=your_b…here
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
OPENAI_API_KEY=sk-***
```

### 5. 运行 Bot

```bash
python -m src.bot
```

## Docker 部署

### 1. 构建镜像

```bash
docker build -t tg-chat-summary .
```

### 2. 运行容器

```bash
docker run -d \
  --name tg-summarizer \
  --env-file .env \
  --restart unless-stopped \
  tg-chat-summary
```

### 3. 查看日志

```bash
docker logs -f tg-summarizer
```

### 4. 停止容器

```bash
docker stop tg-summarizer
```

## 云服务器部署

### 使用 systemd (Linux)

1. 创建服务文件：

```bash
sudo nano /etc/systemd/system/tg-summarizer.service
```

2. 添加以下内容：

```ini
[Unit]
Description=TG Chat Summary Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/tg-chat-summary
Environment=PATH=/path/to/tg-chat-summary/venv/bin
ExecStart=/path/to/tg-chat-summary/venv/bin/python -m src.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. 启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable tg-summarizer
sudo systemctl start tg-summarizer
```

4. 查看状态：

```bash
sudo systemctl status tg-summarizer
sudo journalctl -u tg-summarizer -f
```

### 使用 PM2 (Node.js 环境)

如果你已有 Node.js 环境，可以使用 PM2：

```bash
pm2 start "python -m src.bot" --name tg-summarizer
pm2 save
pm2 startup
```

## 配置说明

### 环境变量

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `BOT_TOKEN` | ✅ | Telegram Bot Token | - |
| `API_ID` | ✅ | Telegram API ID | - |
| `API_HASH` | ✅ | Telegram API Hash | - |
| `AI_PROVIDER` | ❌ | AI 提供商 | `openai` |
| `OPENAI_API_KEY` | ⚠️ | OpenAI API Key | - |
| `ANTHROPIC_API_KEY` | ⚠️ | Anthropic API Key | - |
| `LOCAL_MODEL_URL` | ❌ | 本地模型 URL | `http://localhost:11434` |
| `DEFAULT_MESSAGE_COUNT` | ❌ | 默认消息数量 | `100` |
| `MAX_MESSAGE_COUNT` | ❌ | 最大消息数量 | `1000` |
| `DEFAULT_LANGUAGE` | ❌ | 默认语言 | `zh` |
| `ENABLE_IMAGE` | ❌ | 启用图片生成 | `true` |
| `IMAGE_WIDTH` | ❌ | 图片宽度 | `800` |
| `IMAGE_THEME` | ❌ | 图片主题 | `dark` |
| `TIMEZONE` | ❌ | 时区 | `Asia/Shanghai` |

### AI 提供商配置

#### OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-***
OPENAI_MODEL=gpt-4o-mini
```

#### Anthropic

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-***
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

#### 本地模型 (Ollama)

```env
AI_PROVIDER=local
LOCAL_MODEL_URL=http://localhost:11434
```

## 常见问题

### Bot 无法接收消息

1. 确保 Bot 已添加到群组
2. 确保 Bot 有读取消息的权限
3. 检查 Bot Token 是否正确

### 总结生成失败

1. 检查 AI API Key 是否有效
2. 检查网络连接
3. 查看日志获取详细错误信息

### 图片生成失败

1. 确保已安装 Pillow
2. 检查字体文件是否存在
3. 尝试禁用图片生成：`ENABLE_IMAGE=false`

### 内存占用过高

1. 减少 `MAX_MESSAGE_COUNT`
2. 使用更小的 AI 模型
3. 定期重启 Bot

## 更新

```bash
cd tg-chat-summary
git pull
pip install -r requirements.txt
# 重启 Bot
```

## 获取帮助

- 提交 [Issue](https://github.com/liuweiqiang0523/tg-chat-summary/issues)
- 查看 [Wiki](https://github.com/liuweiqiang0523/tg-chat-summary/wiki)
