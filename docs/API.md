# API 文档

## 模块说明

### Summarizer (消息总结器)

核心总结模块，负责调用 AI 生成消息摘要。

#### 类

##### `Summarizer`

```python
class Summarizer:
    def __init__(self)
    async def summarize(self, messages: list[Message], language: str = "zh", max_tokens: int = 2000) -> SummaryResult
```

**方法：**

- `summarize(messages, language, max_tokens)` - 总结消息列表

**参数：**

- `messages`: Message 对象列表
- `language`: 语言 (zh/en)
- `max_tokens`: 最大 token 数

**返回：**

`SummaryResult` 对象，包含：
- `time_range`: 时间范围 (start, end)
- `total_messages`: 消息总数
- `total_users`: 用户总数
- `active_users`: 活跃用户列表
- `topics`: 话题列表
- `summary`: 总结文本
- `sentiment`: 情绪分析
- `highlights`: 关键亮点

---

### TopicExtractor (话题提取器)

负责从消息中提取和聚类话题。

#### 类

##### `TopicExtractor`

```python
class TopicExtractor:
    def __init__(self)
    def extract_topics(self, messages: list[Message], max_topics: int = 5, language: str = "zh") -> list[TopicCluster]
```

**方法：**

- `extract_topics(messages, max_topics, language)` - 提取话题聚类

**参数：**

- `messages`: Message 对象列表
- `max_topics`: 最大话题数
- `language`: 语言 (zh/en)

**返回：**

`TopicCluster` 对象列表，每个包含：
- `title`: 话题标题
- `keywords`: 关键词列表
- `message_count`: 相关消息数
- `messages`: 相关消息列表
- `summary`: 话题总结

---

### ImageGenerator (图片生成器)

负责生成总结图片。

#### 类

##### `ImageGenerator`

```python
class ImageGenerator:
    def __init__(self, theme: str = "dark", width: int = 800)
    async def generate(self, result: SummaryResult, language: str = "zh", title: str = None) -> BytesIO
```

**方法：**

- `generate(result, language, title)` - 生成总结图片

**参数：**

- `result`: SummaryResult 对象
- `language`: 语言 (zh/en)
- `title`: 自定义标题 (可选)

**返回：**

`BytesIO` 对象，包含 PNG 图片数据

**主题：**

- `dark`: 深色主题
- `light`: 浅色主题

---

### Scheduler (调度器)

负责定时任务管理。

#### 类

##### `Scheduler`

```python
class Scheduler:
    def __init__(self)
    def start(self)
    def stop(self)
    def add_daily_job(self, chat_id: int, job_time: time, callback: Callable, job_id: str = None)
    def add_weekly_job(self, chat_id: int, day_of_week: int, job_time: time, callback: Callable, job_id: str = None)
    def add_interval_job(self, chat_id: int, hours: int, callback: Callable, job_id: str = None)
    def remove_job(self, job_id: str)
    def get_jobs(self, chat_id: int = None) -> list[dict]
```

**方法：**

- `start()` - 启动调度器
- `stop()` - 停止调度器
- `add_daily_job(...)` - 添加每日定时任务
- `add_weekly_job(...)` - 添加每周定时任务
- `add_interval_job(...)` - 添加间隔定时任务
- `remove_job(job_id)` - 移除任务
- `get_jobs(chat_id)` - 获取任务列表

---

### Database (数据库)

负责数据持久化。

#### 类

##### `Database`

```python
class Database:
    def __init__(self, db_path: str = None)
    def connect(self)
    def close(self)
    def get_chat_config(self, chat_id: int) -> Optional[dict]
    def upsert_chat_config(self, chat_id: int, **kwargs)
    def add_summary_history(self, chat_id: int, summary_type: str, message_count: int, user_count: int, sentiment: str, summary: str)
    def get_summary_history(self, chat_id: int, limit: int = 10) -> list[dict]
    def add_scheduled_job(self, chat_id: int, job_type: str, job_config: str)
    def get_scheduled_jobs(self, chat_id: int = None) -> list[dict]
    def deactivate_scheduled_job(self, job_id: int)
```

**方法：**

- `connect()` - 连接数据库
- `close()` - 关闭连接
- `get_chat_config(chat_id)` - 获取群组配置
- `upsert_chat_config(chat_id, **kwargs)` - 更新群组配置
- `add_summary_history(...)` - 添加总结历史
- `get_summary_history(chat_id, limit)` - 获取总结历史
- `add_scheduled_job(...)` - 添加定时任务
- `get_scheduled_jobs(chat_id)` - 获取定时任务
- `deactivate_scheduled_job(job_id)` - 停用定时任务

---

### Utils (工具函数)

通用工具函数。

#### 函数

```python
def parse_time_string(time_str: str) -> Optional[timedelta]
def format_duration(td: timedelta, language: str = "zh") -> str
def format_number(num: int, language: str = "zh") -> str
def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str
def extract_urls(text: str) -> list[str]
def extract_mentions(text: str) -> list[str]
def extract_hashtags(text: str) -> list[str]
def sanitize_filename(filename: str) -> str
def calculate_engagement_rate(messages: int, users: int, total_members: int) -> float
def get_sentiment_emoji(sentiment: str) -> str
def generate_progress_bar(value: int, max_value: int, length: int = 10, filled: str = "█", empty: str = "░") -> str
```

---

## 数据结构

### Message

```python
@dataclass
class Message:
    id: int
    user_id: int
    username: str
    text: str
    timestamp: datetime
    reply_to: Optional[int] = None
```

### SummaryResult

```python
@dataclass
class SummaryResult:
    time_range: tuple[datetime, datetime]
    total_messages: int
    total_users: int
    active_users: list[dict]
    topics: list[dict]
    summary: str
    sentiment: str
    highlights: list[str]
```

### TopicCluster

```python
@dataclass
class TopicCluster:
    title: str
    keywords: list[str]
    message_count: int
    messages: list[Message]
    summary: Optional[str] = None
```

---

## 使用示例

### 基本总结

```python
from src.summarizer import Summarizer, Message

# 创建总结器
summarizer = Summarizer()

# 准备消息
messages = [
    Message(id=1, user_id=100, username="user1", text="消息1", timestamp=datetime.now()),
    Message(id=2, user_id=101, username="user2", text="消息2", timestamp=datetime.now()),
]

# 生成总结
result = await summarizer.summarize(messages, language="zh")

print(result.summary)
print(result.sentiment)
print(result.topics)
```

### 提取话题

```python
from src.topics import TopicExtractor

extractor = TopicExtractor()
topics = extractor.extract_topics(messages, max_topics=5, language="zh")

for topic in topics:
    print(f"{topic.title}: {topic.message_count} 条消息")
```

### 生成图片

```python
from src.image import ImageGenerator

gen = ImageGenerator(theme="dark")
image_buffer = await gen.generate(result, language="zh")

# 保存图片
with open("summary.png", "wb") as f:
    f.write(image_buffer.read())
```

### 使用数据库

```python
from src.database import Database

db = Database("data.db")
db.connect()

# 保存配置
db.upsert_chat_config(chat_id=123456, language="zh", enable_image=1)

# 获取配置
config = db.get_chat_config(123456)

# 保存总结历史
db.add_summary_history(
    chat_id=123456,
    summary_type="daily",
    message_count=100,
    user_count=20,
    sentiment="积极正面",
    summary="今天讨论很活跃"
)

db.close()
```
