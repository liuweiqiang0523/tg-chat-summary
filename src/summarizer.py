"""消息总结核心模块"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from .config import config


@dataclass
class Message:
    """消息数据结构"""
    id: int
    user_id: int
    username: str
    text: str
    timestamp: datetime
    reply_to: Optional[int] = None


@dataclass
class SummaryResult:
    """总结结果"""
    time_range: tuple[datetime, datetime]
    total_messages: int
    total_users: int
    active_users: list[dict]
    topics: list[dict]
    summary: str
    sentiment: str
    highlights: list[str]


class Summarizer:
    """消息总结器"""

    def __init__(self):
        self.provider = config.AI_PROVIDER

    async def summarize(
        self,
        messages: list[Message],
        language: str = "zh",
        max_tokens: int = 2000
    ) -> SummaryResult:
        """总结消息列表"""
        if not messages:
            raise ValueError("没有消息可总结")

        # 统计基础数据
        total_messages = len(messages)
        users = {}
        for msg in messages:
            if msg.username not in users:
                users[msg.username] = 0
            users[msg.username] += 1

        active_users = sorted(
            [{"username": k, "count": v} for k, v in users.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # 提取话题
        topics = await self._extract_topics(messages, language)

        # 生成总结
        summary = await self._generate_summary(messages, topics, language, max_tokens)

        # 情绪分析
        sentiment = await self._analyze_sentiment(messages, language)

        # 关键亮点
        highlights = await self._extract_highlights(messages, summary, language)

        time_range = (messages[0].timestamp, messages[-1].timestamp)

        return SummaryResult(
            time_range=time_range,
            total_messages=total_messages,
            total_users=len(users),
            active_users=active_users,
            topics=topics,
            summary=summary,
            sentiment=sentiment,
            highlights=highlights
        )

    async def _extract_topics(self, messages: list[Message], language: str) -> list[dict]:
        """提取关键话题"""
        prompt = self._build_topic_prompt(messages, language)
        response = await self._call_ai(prompt, max_tokens=500)
        return self._parse_topics(response)

    async def _generate_summary(
        self,
        messages: list[Message],
        topics: list[dict],
        language: str,
        max_tokens: int
    ) -> str:
        """生成总结文本"""
        prompt = self._build_summary_prompt(messages, topics, language)
        return await self._call_ai(prompt, max_tokens=max_tokens)

    async def _analyze_sentiment(self, messages: list[Message], language: str) -> str:
        """分析整体情绪"""
        prompt = self._build_sentiment_prompt(messages, language)
        response = await self._call_ai(prompt, max_tokens=100)
        return response.strip()

    async def _extract_highlights(
        self,
        messages: list[Message],
        summary: str,
        language: str
    ) -> list[str]:
        """提取关键亮点"""
        prompt = self._build_highlights_prompt(messages, summary, language)
        response = await self._call_ai(prompt, max_tokens=300)
        return [h.strip() for h in response.split("\n") if h.strip()]

    async def _call_ai(self, prompt: str, max_tokens: int = 1000) -> str:
        """调用 AI API"""
        if self.provider == "openai":
            return await self._call_openai(prompt, max_tokens)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, max_tokens)
        elif self.provider == "local":
            return await self._call_local(prompt, max_tokens)
        else:
            raise ValueError(f"不支持的 AI 提供商: {self.provider}")

    async def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """调用 OpenAI API"""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的群聊消息分析助手。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """调用 Anthropic API"""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    async def _call_local(self, prompt: str, max_tokens: int) -> str:
        """调用本地模型"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.LOCAL_MODEL_URL}/api/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "stream": False
                }
            ) as resp:
                data = await resp.json()
                return data.get("response", "")

    def _build_topic_prompt(self, messages: list[Message], language: str) -> str:
        """构建话题提取 prompt"""
        text = "\n".join([f"[{m.username}]: {m.text}" for m in messages[-200:]])
        lang_hint = "请用中文回答" if language == "zh" else "Please respond in English"

        return f"""分析以下群聊消息，提取 3-5 个主要话题。

每个话题包含：
- title: 话题标题
- count: 相关消息数量
- keywords: 关键词列表

消息内容：
{text}

{lang_hint}

请用 JSON 格式输出话题列表。"""

    def _build_summary_prompt(
        self,
        messages: list[Message],
        topics: list[dict],
        language: str
    ) -> str:
        """构建总结生成 prompt"""
        text = "\n".join([f"[{m.username}]: {m.text}" for m in messages[-500:]])
        topics_text = "\n".join([f"- {t['title']}" for t in topics])
        lang_hint = "请用中文总结" if language == "zh" else "Please summarize in English"

        return f"""根据以下群聊消息和话题，生成一份简洁的总结。

主要话题：
{topics_text}

消息内容：
{text}

总结要求：
1. 概括讨论的主要内容
2. 指出关键决策或结论
3. 提及重要的问题或争议
4. 保持客观中立

{lang_hint}"""

    def _build_sentiment_prompt(self, messages: list[Message], language: str) -> str:
        """构建情绪分析 prompt"""
        text = "\n".join([f"[{m.username}]: {m.text}" for m in messages[-100:]])
        lang_hint = "用中文回答" if language == "zh" else "Answer in English"

        return f"""分析以下群聊消息的整体情绪氛围。

消息内容：
{text}

请选择一个最符合的描述：
- 积极正面
- 中性平淡
- 消极负面
- 热烈讨论
- 轻松愉快
- 严肃认真

{lang_hint}，只输出情绪描述，不要其他内容。"""

    def _build_highlights_prompt(
        self,
        messages: list[Message],
        summary: str,
        language: str
    ) -> str:
        """构建亮点提取 prompt"""
        text = "\n".join([f"[{m.username}]: {m.text}" for m in messages[-200:]])
        lang_hint = "用中文回答" if language == "zh" else "Answer in English"

        return f"""根据以下群聊消息和总结，提取 3-5 个关键亮点或重要信息。

总结内容：
{summary}

消息内容：
{text}

每个亮点一行，简洁明了。
{lang_hint}"""

    def _parse_topics(self, response: str) -> list[dict]:
        """解析话题 JSON"""
        import json
        try:
            # 尝试提取 JSON 部分
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end != -1:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return [{"title": "综合讨论", "count": 0, "keywords": []}]
