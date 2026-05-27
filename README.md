# TG Chat Summary 🤖

Telegram 群聊消息智能总结机器人

## ✨ 功能

- 📊 群聊消息智能总结
- ⏰ 支持指定时间范围（最近 N 小时/消息条数）
- 🏷️ 自动提取关键话题
- 👥 活跃用户统计
- 📈 群聊活跃度分析
- 🌍 多语言支持（中/英文）
- 🖼️ 生成精美的总结图片
- ⏱️ 定时自动总结（每日/每周）

## 🚀 快速开始

### 1. 获取 Telegram Bot Token

1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建机器人
3. 获取 Bot Token

### 2. 获取 API ID 和 Hash

1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 登录后进入 "API development tools"
3. 创建应用获取 `api_id` 和 `api_hash`

### 3. 安装

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/tg-chat-summary.git
cd tg-chat-summary

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置
```

### 4. 运行

```bash
python -m src.bot
```

## 📝 使用方法

### 命令

| 命令 | 说明 |
|------|------|
| `/sum` | 总结最近 100 条消息 |
| `/sum 200` | 总结最近 200 条消息 |
| `/sum 1h` | 总结最近 1 小时 |
| `/sum 3h` | 总结最近 3 小时 |
| `/sum 12h` | 总结最近 12 小时 |
| `/sum 1d` | 总结最近 1 天 |
| `/sum 2d` | 总结最近 2 天 |
| `/sum 30m` | 总结最近 30 分钟 |
| `/daily` | 生成今日群聊日报 |
| `/weekly` | 生成本周群聊周报 |
| `/topics` | 提取热门话题 |
| `/keywords` | 提取关键词 |
| `/sentiment` | 情绪分析 |
| `/stats` | 群聊活跃度统计 |
| `/活跃榜` | 活跃用户排行 |
| `/setdaily 09:00` | 设置每日总结时间 |
| `/setweekly mon 10:00` | 设置每周总结 |
| `/unset` | 取消定时任务 |
| `/lang zh` | 设置语言 (zh/en) |

### 管理命令

| 命令 | 说明 |
|------|------|
| `/setdaily 09:00` | 设置每日总结时间 |
| `/setweekly sun 10:00` | 设置每周总结时间 |
| `/lang zh` | 设置语言为中文 |
| `/lang en` | 设置语言为英文 |

## 🏗️ 项目结构

```
tg-chat-summary/
├── src/
│   ├── __init__.py
│   ├── bot.py          # Bot 主程序
│   ├── config.py       # 配置管理
│   ├── summarizer.py   # 消息总结核心
│   ├── topics.py       # 话题聚类
│   ├── image.py        # 图片生成
│   ├── scheduler.py    # 定时任务
│   ├── database.py     # 数据库管理
│   └── utils.py        # 工具函数
├── tests/
│   ├── test_summarizer.py
│   ├── test_config.py
│   ├── test_image.py
│   └── test_scheduler.py
├── docs/
│   └── API.md
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── Dockerfile
└── README.md
```

## ⚙️ 配置说明

```env
# Telegram 配置
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id
API_HASH=your_api_hash

# AI 配置 (支持多种后端)
AI_PROVIDER=openai  # openai / anthropic / local
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-xxx
LOCAL_MODEL_URL=http://localhost:11434

# 总结配置
DEFAULT_MESSAGE_COUNT=100
MAX_MESSAGE_COUNT=1000
DEFAULT_LANGUAGE=zh

# 图片生成
ENABLE_IMAGE=true
IMAGE_WIDTH=800
IMAGE_THEME=dark  # dark / light
```

## 📊 输出示例

### 文字版
```
📊 群聊总结 | 2026-05-27 14:00 - 16:00

📝 消息统计
├─ 总消息数: 342 条
├─ 参与人数: 18 人
└─ 活跃时段: 14:30 - 15:45

🔥 热门话题
1. 新版本发布讨论 (45 条)
2. Bug 反馈与修复 (32 条)
3. 功能建议收集 (28 条)

👥 活跃用户 TOP 5
1. @user1 - 67 条
2. @user2 - 45 条
3. @user3 - 38 条

💡 关键结论
- 团队对新版本反馈积极
- 发现 3 个关键 bug 已安排修复
- 收集到 12 条功能建议
```

### 图片版
生成精美的总结图片，可直接分享到其他平台

## 🐳 Docker 部署

```bash
docker build -t tg-chat-summary .
docker run -d --name tg-summarizer --env-file .env tg-chat-summary
```

## 🧪 开发

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest
```

### 代码风格

```bash
# 格式化
black src/ tests/

# 检查
flake8 src/ tests/

# 类型检查
mypy src/
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

## ⭐ Star History

如果觉得有用，请给个 Star ⭐

## 📄 License

[MIT License](LICENSE)
