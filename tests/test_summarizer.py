"""测试总结模块"""

import pytest
from datetime import datetime, timedelta
from src.summarizer import Summarizer, Message, SummaryResult


@pytest.fixture
def sample_messages():
    """示例消息"""
    now = datetime.now()
    return [
        Message(
            id=i,
            user_id=1000 + i % 5,
            username=f"user{i % 5}",
            text=f"这是第 {i} 条测试消息，讨论关于新版本的功能",
            timestamp=now - timedelta(minutes=100 - i)
        )
        for i in range(100)
    ]


@pytest.fixture
def summarizer():
    """总结器实例"""
    return Summarizer()


def test_message_creation():
    """测试消息创建"""
    msg = Message(
        id=1,
        user_id=1000,
        username="test_user",
        text="Hello World",
        timestamp=datetime.now()
    )
    assert msg.id == 1
    assert msg.username == "test_user"
    assert msg.text == "Hello World"
    assert msg.reply_to is None


def test_message_with_reply():
    """测试带回复的消息"""
    msg = Message(
        id=2,
        user_id=1001,
        username="user2",
        text="这是回复",
        timestamp=datetime.now(),
        reply_to=1
    )
    assert msg.reply_to == 1


def test_summary_result_structure():
    """测试总结结果结构"""
    now = datetime.now()
    result = SummaryResult(
        time_range=(now - timedelta(hours=1), now),
        total_messages=100,
        total_users=5,
        active_users=[
            {"username": "user1", "count": 30},
            {"username": "user2", "count": 20},
        ],
        topics=[
            {"title": "新版本讨论", "count": 50, "keywords": ["版本", "功能"]},
        ],
        summary="这是一段测试总结",
        sentiment="积极正面",
        highlights=["发现 3 个关键问题", "收集到 12 条建议"]
    )
    assert result.total_messages == 100
    assert result.total_users == 5
    assert len(result.active_users) == 2
    assert len(result.topics) == 1
    assert result.sentiment == "积极正面"


@pytest.mark.asyncio
async def test_summarizer_empty_messages(summarizer):
    """测试空消息列表"""
    with pytest.raises(ValueError, match="没有消息可总结"):
        await summarizer.summarize([])


@pytest.mark.asyncio
async def test_summarizer_with_messages(summarizer, sample_messages):
    """测试消息总结（需要 API key）"""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY 未设置")

    result = await summarizer.summarize(sample_messages, language="zh")
    assert result.total_messages == 100
    assert result.total_users == 5
    assert result.summary
    assert result.sentiment


def test_parse_topics_valid_json(summarizer):
    """测试解析有效的 JSON 话题"""
    response = '''[
        {"title": "话题1", "count": 10, "keywords": ["关键词1"]},
        {"title": "话题2", "count": 5, "keywords": ["关键词2"]}
    ]'''
    topics = summarizer._parse_topics(response)
    assert len(topics) == 2
    assert topics[0]["title"] == "话题1"


def test_parse_topics_invalid_json(summarizer):
    """测试解析无效的 JSON"""
    response = "这不是 JSON"
    topics = summarizer._parse_topics(response)
    assert len(topics) == 1
    assert topics[0]["title"] == "综合讨论"


def test_build_topic_prompt(summarizer, sample_messages):
    """测试构建话题提取 prompt"""
    prompt = summarizer._build_topic_prompt(sample_messages, "zh")
    assert "群聊消息" in prompt
    assert "JSON" in prompt


def test_build_summary_prompt(summarizer, sample_messages):
    """测试构建总结生成 prompt"""
    topics = [{"title": "测试话题", "count": 10, "keywords": ["测试"]}]
    prompt = summarizer._build_summary_prompt(sample_messages, topics, "zh")
    assert "总结" in prompt
    assert "测试话题" in prompt


def test_build_sentiment_prompt(summarizer, sample_messages):
    """测试构建情绪分析 prompt"""
    prompt = summarizer._build_sentiment_prompt(sample_messages, "zh")
    assert "情绪" in prompt


def test_build_highlights_prompt(summarizer, sample_messages):
    """测试构建亮点提取 prompt"""
    prompt = summarizer._build_highlights_prompt(
        sample_messages, "测试总结", "zh"
    )
    assert "亮点" in prompt
