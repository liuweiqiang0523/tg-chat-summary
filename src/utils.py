"""工具函数模块"""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    解析时间字符串为 timedelta

    支持格式:
    - "2h" -> 2 小时
    - "30m" -> 30 分钟
    - "1d" -> 1 天
    - "2h30m" -> 2 小时 30 分钟
    """
    if not time_str:
        return None

    time_str = time_str.strip().lower()
    total_seconds = 0

    # 匹配天数
    days_match = re.search(r'(\d+)d', time_str)
    if days_match:
        total_seconds += int(days_match.group(1)) * 86400

    # 匹配小时
    hours_match = re.search(r'(\d+)h', time_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600

    # 匹配分钟
    minutes_match = re.search(r'(\d+)m', time_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60

    if total_seconds == 0:
        return None

    return timedelta(seconds=total_seconds)


def format_duration(td: timedelta, language: str = "zh") -> str:
    """
    格式化时间间隔

    Args:
        td: 时间间隔
        language: 语言 (zh/en)

    Returns:
        格式化后的字符串
    """
    total_seconds = int(td.total_seconds())

    if total_seconds < 60:
        if language == "zh":
            return f"{total_seconds}秒"
        return f"{total_seconds}s"

    minutes = total_seconds // 60
    if minutes < 60:
        if language == "zh":
            return f"{minutes}分钟"
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours < 24:
        if language == "zh":
            if remaining_minutes > 0:
                return f"{hours}小时{remaining_minutes}分钟"
            return f"{hours}小时"
        if remaining_minutes > 0:
            return f"{hours}h{remaining_minutes}m"
        return f"{hours}h"

    days = hours // 24
    remaining_hours = hours % 24

    if language == "zh":
        if remaining_hours > 0:
            return f"{days}天{remaining_hours}小时"
        return f"{days}天"
    if remaining_hours > 0:
        return f"{days}d{remaining_hours}h"
    return f"{days}d"


def format_number(num: int, language: str = "zh") -> str:
    """
    格式化数字

    Args:
        num: 数字
        language: 语言 (zh/en)

    Returns:
        格式化后的字符串
    """
    if language == "zh":
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        if num >= 1000:
            return f"{num / 1000:.1f}千"
        return str(num)
    else:
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_urls(text: str) -> list[str]:
    """
    提取文本中的 URL

    Args:
        text: 文本

    Returns:
        URL 列表
    """
    url_pattern = r'https?://[^\s<>\"\'\)\]]+'
    return re.findall(url_pattern, text)


def extract_mentions(text: str) -> list[str]:
    """
    提取文本中的 @ 提及

    Args:
        text: 文本

    Returns:
        用户名列表 (不包含 @)
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)


def extract_hashtags(text: str) -> list[str]:
    """
    提取文本中的 # 标签

    Args:
        text: 文本

    Returns:
        标签列表 (不包含 #)
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, '_', filename)

    # 移除首尾空格和点
    sanitized = sanitized.strip('. ')

    # 限制长度
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    return sanitized or 'unnamed'


def calculate_engagement_rate(
    messages: int,
    users: int,
    total_members: int
) -> float:
    """
    计算参与率

    Args:
        messages: 消息数
        users: 参与用户数
        total_members: 总成员数

    Returns:
        参与率 (0-100)
    """
    if total_members == 0:
        return 0.0

    # 活跃用户比例
    active_rate = (users / total_members) * 100

    # 消息密度 (每人平均消息数)
    density = messages / users if users > 0 else 0

    # 综合参与率 (权重: 活跃比例 60%, 消息密度 40%)
    engagement = active_rate * 0.6 + min(density * 10, 40)

    return min(engagement, 100.0)


def get_sentiment_emoji(sentiment: str) -> str:
    """
    获取情绪对应的 emoji

    Args:
        sentiment: 情绪描述

    Returns:
        emoji 字符
    """
    sentiment_map = {
        "积极正面": "😊",
        "positive": "😊",
        "中性平淡": "😐",
        "neutral": "😐",
        "消极负面": "😔",
        "negative": "😔",
        "热烈讨论": "🔥",
        "heated": "🔥",
        "轻松愉快": "😄",
        "relaxed": "😄",
        "严肃认真": "🧐",
        "serious": "🧐",
    }

    for key, emoji in sentiment_map.items():
        if key in sentiment.lower():
            return emoji

    return "💬"


def generate_progress_bar(
    value: int,
    max_value: int,
    length: int = 10,
    filled: str = "█",
    empty: str = "░"
) -> str:
    """
    生成进度条

    Args:
        value: 当前值
        max_value: 最大值
        length: 进度条长度
        filled: 已填充字符
        empty: 未填充字符

    Returns:
        进度条字符串
    """
    if max_value == 0:
        return empty * length

    filled_length = int((value / max_value) * length)
    filled_length = min(filled_length, length)

    return filled * filled_length + empty * (length - filled_length)
