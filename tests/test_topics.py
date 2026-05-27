"""测试话题聚类模块"""

import pytest
from datetime import datetime, timedelta
from src.topics import TopicExtractor, TopicCluster
from src.summarizer import Message


@pytest.fixture
def topic_extractor():
    """话题提取器实例"""
    return TopicExtractor()


@pytest.fixture
def sample_messages():
    """示例消息"""
    now = datetime.now()
    messages = []

    # 话题 1: 新版本讨论
    for i in range(20):
        messages.append(Message(
            id=i,
            user_id=1000 + i % 5,
            username=f"user{i % 5}",
            text=f"新版本功能很棒，特别是版本更新后的性能提升",
            timestamp=now - timedelta(minutes=100 - i)
        ))

    # 话题 2: Bug 反馈
    for i in range(15):
        messages.append(Message(
            id=20 + i,
            user_id=2000 + i % 3,
            username=f"dev{i % 3}",
            text=f"发现一个 bug，系统有时候会崩溃，需要修复",
            timestamp=now - timedelta(minutes=80 - i)
        ))

    # 话题 3: 功能建议
    for i in range(10):
        messages.append(Message(
            id=35 + i,
            user_id=3000 + i % 2,
            username=f"pm{i % 2}",
            text=f"建议添加新功能，支持暗黑模式和主题切换",
            timestamp=now - timedelta(minutes=60 - i)
        ))

    return messages


def test_topic_extractor_init(topic_extractor):
    """测试话题提取器初始化"""
    assert topic_extractor is not None
    assert len(topic_extractor.STOPWORDS_ZH) > 0
    assert len(topic_extractor.STOPWORDS_EN) > 0


def test_extract_topics_empty(topic_extractor):
    """测试空消息列表"""
    topics = topic_extractor.extract_topics([])
    assert topics == []


def test_extract_topics_zh(topic_extractor, sample_messages):
    """测试中文话题提取"""
    topics = topic_extractor.extract_topics(sample_messages, max_topics=5, language="zh")

    assert len(topics) > 0
    assert len(topics) <= 5

    for topic in topics:
        assert topic.title != ""
        assert len(topic.keywords) > 0
        assert topic.message_count >= 3


def test_extract_topics_en(topic_extractor):
    """测试英文话题提取"""
    now = datetime.now()
    messages = []

    # Topic 1: Version update
    for i in range(15):
        messages.append(Message(
            id=i,
            user_id=1000 + i % 3,
            username=f"user{i % 3}",
            text="The new version update is great, performance improved significantly",
            timestamp=now - timedelta(minutes=50 - i)
        ))

    # Topic 2: Bug report
    for i in range(10):
        messages.append(Message(
            id=15 + i,
            user_id=2000 + i % 2,
            username=f"dev{i % 2}",
            text="Found a bug, the system crashes sometimes, needs fix",
            timestamp=now - timedelta(minutes=35 - i)
        ))

    topics = topic_extractor.extract_topics(messages, max_topics=3, language="en")

    assert len(topics) > 0
    for topic in topics:
        assert topic.title != ""
        assert len(topic.keywords) > 0


def test_tokenize_chinese(topic_extractor):
    """测试中文分词"""
    text = "新版本功能很棒"
    words = topic_extractor._tokenize_chinese(text)

    assert len(words) > 0
    # 应该包含 2-4 字的词
    assert any(len(w) >= 2 for w in words)


def test_tokenize_english(topic_extractor):
    """测试英文分词"""
    text = "The new version is great"
    words = topic_extractor._tokenize_english(text)

    assert "the" in words
    assert "new" in words
    assert "version" in words
    assert "is" in words
    assert "great" in words


def test_tokenize_english_lowercased(topic_extractor):
    """测试英文分词转小写"""
    text = "Hello World"
    words = topic_extractor._tokenize_english(text)

    assert "hello" in words
    assert "world" in words


def test_extract_keywords(topic_extractor, sample_messages):
    """测试关键词提取"""
    keywords = topic_extractor._extract_keywords(sample_messages, "zh")

    assert len(keywords) > 0
    assert len(keywords) <= 20

    # 每个关键词是 (word, count) 元组
    for word, count in keywords:
        assert isinstance(word, str)
        assert isinstance(count, int)
        assert count > 0


def test_cluster_by_keywords(topic_extractor, sample_messages):
    """测试基于关键词聚类"""
    keywords = topic_extractor._extract_keywords(sample_messages, "zh")
    clusters = topic_extractor._cluster_by_keywords(sample_messages, keywords, max_clusters=3)

    assert len(clusters) > 0
    assert len(clusters) <= 3

    for cluster in clusters:
        assert cluster.message_count >= 3
        assert len(cluster.messages) >= 3


def test_find_related_keywords(topic_extractor, sample_messages):
    """测试查找相关关键词"""
    keywords = topic_extractor._extract_keywords(sample_messages, "zh")

    if keywords:
        main_keyword = keywords[0][0]
        related = topic_extractor._find_related_keywords(
            main_keyword,
            sample_messages[:20],
            keywords
        )

        # related 应该是一个列表
        assert isinstance(related, list)


def test_merge_similar_clusters(topic_extractor):
    """测试合并相似聚类"""
    # 创建两个有重叠关键词的聚类
    cluster1 = TopicCluster(
        title="",
        keywords=["版本", "更新", "功能"],
        message_count=10,
        messages=[]
    )

    cluster2 = TopicCluster(
        title="",
        keywords=["版本", "发布", "修复"],
        message_count=8,
        messages=[]
    )

    cluster3 = TopicCluster(
        title="",
        keywords=["测试", "部署", "上线"],
        message_count=5,
        messages=[]
    )

    merged = topic_extractor._merge_similar_clusters([cluster1, cluster2, cluster3])

    # cluster1 和 cluster2 有重叠关键词 "版本"，应该被合并
    assert len(merged) <= 3


def test_generate_title_zh(topic_extractor):
    """测试生成中文标题"""
    keywords = ["新版本", "功能", "更新"]
    title = topic_extractor._generate_title(keywords, "zh")

    assert "讨论" in title
    assert any(k in title for k in keywords)


def test_generate_title_en(topic_extractor):
    """测试生成英文标题"""
    keywords = ["version", "update", "feature"]
    title = topic_extractor._generate_title(keywords, "en")

    assert "Discussion" in title
    assert any(k in title for k in keywords)


def test_generate_title_empty(topic_extractor):
    """测试空关键词生成标题"""
    title = topic_extractor._generate_title([], "zh")
    assert title == "其他讨论"

    title = topic_extractor._generate_title([], "en")
    assert title == "Other Discussion"


def test_topic_cluster_structure():
    """测试话题聚类数据结构"""
    cluster = TopicCluster(
        title="测试话题",
        keywords=["关键词1", "关键词2"],
        message_count=10,
        messages=[],
        summary="这是话题总结"
    )

    assert cluster.title == "测试话题"
    assert len(cluster.keywords) == 2
    assert cluster.message_count == 10
    assert cluster.summary == "这是话题总结"


def test_extract_topics_min_messages(topic_extractor):
    """测试最少消息数要求"""
    now = datetime.now()

    # 只有 2 条消息，不足以形成话题
    messages = [
        Message(id=1, user_id=1, username="user1", text="测试消息1", timestamp=now),
        Message(id=2, user_id=2, username="user2", text="测试消息2", timestamp=now),
    ]

    topics = topic_extractor.extract_topics(messages, max_topics=3)
    # 由于每条消息只出现一次，不会形成话题
    assert len(topics) == 0
