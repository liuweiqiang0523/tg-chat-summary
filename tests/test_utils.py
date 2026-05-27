"""测试工具函数模块"""

import pytest
from datetime import timedelta
from src.utils import (
    parse_time_string,
    format_duration,
    format_number,
    truncate_text,
    extract_urls,
    extract_mentions,
    extract_hashtags,
    sanitize_filename,
    calculate_engagement_rate,
    get_sentiment_emoji,
    generate_progress_bar,
)


class TestParseTimeString:
    """测试时间字符串解析"""

    def test_parse_hours(self):
        assert parse_time_string("2h") == timedelta(hours=2)

    def test_parse_minutes(self):
        assert parse_time_string("30m") == timedelta(minutes=30)

    def test_parse_days(self):
        assert parse_time_string("1d") == timedelta(days=1)

    def test_parse_combined(self):
        assert parse_time_string("2h30m") == timedelta(hours=2, minutes=30)

    def test_parse_complex(self):
        assert parse_time_string("1d2h") == timedelta(days=1, hours=2)

    def test_parse_empty(self):
        assert parse_time_string("") is None

    def test_parse_none(self):
        assert parse_time_string(None) is None

    def test_parse_invalid(self):
        assert parse_time_string("abc") is None

    def test_parse_no_unit(self):
        assert parse_time_string("123") is None


class TestFormatDuration:
    """测试时间间隔格式化"""

    def test_seconds_zh(self):
        td = timedelta(seconds=30)
        assert format_duration(td, "zh") == "30秒"

    def test_seconds_en(self):
        td = timedelta(seconds=30)
        assert format_duration(td, "en") == "30s"

    def test_minutes_zh(self):
        td = timedelta(minutes=45)
        assert format_duration(td, "zh") == "45分钟"

    def test_minutes_en(self):
        td = timedelta(minutes=45)
        assert format_duration(td, "en") == "45m"

    def test_hours_zh(self):
        td = timedelta(hours=3)
        assert format_duration(td, "zh") == "3小时"

    def test_hours_with_minutes_zh(self):
        td = timedelta(hours=2, minutes=30)
        assert format_duration(td, "zh") == "2小时30分钟"

    def test_hours_en(self):
        td = timedelta(hours=5)
        assert format_duration(td, "en") == "5h"

    def test_days_zh(self):
        td = timedelta(days=2)
        assert format_duration(td, "zh") == "2天"

    def test_days_with_hours_zh(self):
        td = timedelta(days=1, hours=6)
        assert format_duration(td, "zh") == "1天6小时"

    def test_days_en(self):
        td = timedelta(days=3)
        assert format_duration(td, "en") == "3d"


class TestFormatNumber:
    """测试数字格式化"""

    def test_small_number_zh(self):
        assert format_number(500, "zh") == "500"

    def test_thousand_zh(self):
        assert format_number(1500, "zh") == "1.5千"

    def test_ten_thousand_zh(self):
        assert format_number(15000, "zh") == "1.5万"

    def test_small_number_en(self):
        assert format_number(500, "en") == "500"

    def test_thousand_en(self):
        assert format_number(1500, "en") == "1.5K"

    def test_million_en(self):
        assert format_number(1500000, "en") == "1.5M"


class TestTruncateText:
    """测试文本截断"""

    def test_short_text(self):
        assert truncate_text("短文本", 10) == "短文本"

    def test_long_text(self):
        result = truncate_text("这是一段很长的文本" * 10, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_custom_suffix(self):
        result = truncate_text("这是一段很长的文本" * 10, 20, suffix="…")
        assert result.endswith("…")

    def test_exact_length(self):
        text = "恰好十个字符的文本"
        assert truncate_text(text, len(text)) == text


class TestExtractUrls:
    """测试 URL 提取"""

    def test_single_url(self):
        text = "访问 https://example.com 了解更多"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "https://example.com"

    def test_multiple_urls(self):
        text = "https://a.com 和 https://b.com"
        urls = extract_urls(text)
        assert len(urls) == 2

    def test_no_urls(self):
        text = "没有链接的文本"
        urls = extract_urls(text)
        assert len(urls) == 0

    def test_complex_url(self):
        text = "https://example.com/path?query=1&other=2#fragment"
        urls = extract_urls(text)
        assert len(urls) == 1


class TestExtractMentions:
    """测试 @ 提及提取"""

    def test_single_mention(self):
        text = "你好 @user1"
        mentions = extract_mentions(text)
        assert mentions == ["user1"]

    def test_multiple_mentions(self):
        text = "@user1 和 @user2"
        mentions = extract_mentions(text)
        assert mentions == ["user1", "user2"]

    def test_no_mentions(self):
        text = "没有提及"
        mentions = extract_mentions(text)
        assert mentions == []


class TestExtractHashtags:
    """测试 # 标签提取"""

    def test_single_hashtag(self):
        text = "这是 #topic1"
        hashtags = extract_hashtags(text)
        assert hashtags == ["topic1"]

    def test_multiple_hashtags(self):
        text = "#topic1 #topic2"
        hashtags = extract_hashtags(text)
        assert hashtags == ["topic1", "topic2"]

    def test_no_hashtags(self):
        text = "没有标签"
        hashtags = extract_hashtags(text)
        assert hashtags == []


class TestSanitizeFilename:
    """测试文件名清理"""

    def test_normal_filename(self):
        assert sanitize_filename("normal.txt") == "normal.txt"

    def test_illegal_chars(self):
        assert sanitize_filename('file<>:"/\\|?*.txt') == "file_________.txt"

    def test_spaces(self):
        assert sanitize_filename("  file.txt  ") == "file.txt"

    def test_dots(self):
        assert sanitize_filename("...file...") == "file"

    def test_long_filename(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 255

    def test_empty_filename(self):
        assert sanitize_filename("") == "unnamed"


class TestCalculateEngagementRate:
    """测试参与率计算"""

    def test_high_engagement(self):
        rate = calculate_engagement_rate(
            messages=100,
            users=50,
            total_members=100
        )
        assert rate > 50

    def test_low_engagement(self):
        rate = calculate_engagement_rate(
            messages=10,
            users=5,
            total_members=1000
        )
        assert rate < 10

    def test_zero_members(self):
        rate = calculate_engagement_rate(100, 50, 0)
        assert rate == 0.0

    def test_max_100(self):
        rate = calculate_engagement_rate(1000, 100, 100)
        assert rate <= 100.0


class TestGetSentimentEmoji:
    """测试情绪 emoji 获取"""

    def test_positive_zh(self):
        assert get_sentiment_emoji("积极正面") == "😊"

    def test_positive_en(self):
        assert get_sentiment_emoji("positive") == "😊"

    def test_neutral_zh(self):
        assert get_sentiment_emoji("中性平淡") == "😐"

    def test_negative_zh(self):
        assert get_sentiment_emoji("消极负面") == "😔"

    def test_heated_zh(self):
        assert get_sentiment_emoji("热烈讨论") == "🔥"

    def test_unknown(self):
        assert get_sentiment_emoji("未知情绪") == "💬"


class TestGenerateProgressBar:
    """测试进度条生成"""

    def test_full_progress(self):
        bar = generate_progress_bar(100, 100, length=10)
        assert bar == "█" * 10

    def test_empty_progress(self):
        bar = generate_progress_bar(0, 100, length=10)
        assert bar == "░" * 10

    def test_half_progress(self):
        bar = generate_progress_bar(50, 100, length=10)
        assert bar == "█" * 5 + "░" * 5

    def test_custom_chars(self):
        bar = generate_progress_bar(50, 100, length=10, filled="#", empty="-")
        assert bar == "#####" + "-----"

    def test_zero_max(self):
        bar = generate_progress_bar(0, 0, length=10)
        assert bar == "░" * 10

    def test_overflow(self):
        bar = generate_progress_bar(200, 100, length=10)
        assert bar == "█" * 10
