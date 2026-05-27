"""测试图片生成模块"""

import pytest
from datetime import datetime, timedelta
from src.image import ImageGenerator
from src.summarizer import SummaryResult


@pytest.fixture
def sample_result():
    """示例总结结果"""
    now = datetime.now()
    return SummaryResult(
        time_range=(now - timedelta(hours=2), now),
        total_messages=342,
        total_users=18,
        active_users=[
            {"username": "user1", "count": 67},
            {"username": "user2", "count": 45},
            {"username": "user3", "count": 38},
        ],
        topics=[
            {"title": "新版本发布讨论", "count": 45, "keywords": ["版本", "发布"]},
            {"title": "Bug 反馈与修复", "count": 32, "keywords": ["Bug", "修复"]},
            {"title": "功能建议收集", "count": 28, "keywords": ["功能", "建议"]},
        ],
        summary="团队对新版本反馈积极，发现 3 个关键 bug 已安排修复，收集到 12 条功能建议。",
        sentiment="积极正面",
        highlights=["新版本获得好评", "3 个 bug 已确认修复", "12 条功能建议待评估"]
    )


@pytest.fixture
def image_gen_dark():
    """深色主题图片生成器"""
    return ImageGenerator(theme="dark", width=800)


@pytest.fixture
def image_gen_light():
    """浅色主题图片生成器"""
    return ImageGenerator(theme="light", width=800)


def test_image_generator_init():
    """测试图片生成器初始化"""
    gen = ImageGenerator()
    assert gen.width == 800
    assert gen.padding == 30
    assert gen.card_padding == 20


def test_image_generator_themes():
    """测试主题配置"""
    gen = ImageGenerator(theme="dark")
    assert gen.theme["bg"] == "#1a1a2e"
    assert gen.theme["text"] == "#ffffff"

    gen = ImageGenerator(theme="light")
    assert gen.theme["bg"] == "#f5f5f5"
    assert gen.theme["text"] == "#333333"


def test_image_generator_invalid_theme():
    """测试无效主题"""
    gen = ImageGenerator(theme="invalid")
    # 应该使用默认的 dark 主题
    assert gen.theme["bg"] == "#1a1a2e"


def test_estimate_text_height(image_gen_dark):
    """测试文字高度估算"""
    short_text = "短文本"
    long_text = "这是一段很长的文本" * 50

    height1 = image_gen_dark._estimate_text_height(short_text, 700)
    height2 = image_gen_dark._estimate_text_height(long_text, 700)

    assert height2 > height1
    assert height1 > 0


def test_calculate_height(image_gen_dark, sample_result):
    """测试图片高度计算"""
    height = image_gen_dark._calculate_height(sample_result, "zh")
    assert height > 0
    assert height > 500  # 应该有足够的高度


@pytest.mark.asyncio
async def test_generate_image(image_gen_dark, sample_result):
    """测试生成图片"""
    buffer = await image_gen_dark.generate(sample_result, "zh")
    assert buffer is not None
    assert buffer.read()  # 应该有内容


@pytest.mark.asyncio
async def test_generate_image_with_title(image_gen_dark, sample_result):
    """测试生成带标题的图片"""
    buffer = await image_gen_dark.generate(
        sample_result, "zh", title="测试标题"
    )
    assert buffer is not None


@pytest.mark.asyncio
async def test_generate_image_light_theme(image_gen_light, sample_result):
    """测试浅色主题图片"""
    buffer = await image_gen_light.generate(sample_result, "zh")
    assert buffer is not None


def test_parse_day_of_week(image_gen_dark):
    """测试星期解析"""
    # 这个方法在 Scheduler 类中，这里测试类似的逻辑
    days = {
        "mon": 0, "周一": 0,
        "tue": 1, "周二": 1,
        "wed": 2, "周三": 2,
        "thu": 3, "周四": 3,
        "fri": 4, "周五": 4,
        "sat": 5, "周六": 5,
        "sun": 6, "周日": 6,
    }

    assert days.get("周一") == 0
    assert days.get("sun") == 6
    assert days.get("invalid") is None
