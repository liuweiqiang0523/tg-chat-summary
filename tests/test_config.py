"""测试配置模块"""

import os
import pytest
from src.config import Config


def test_config_default_values():
    """测试默认配置值"""
    assert Config.DEFAULT_MESSAGE_COUNT == 100
    assert Config.MAX_MESSAGE_COUNT == 1000
    assert Config.DEFAULT_LANGUAGE == "zh"
    assert Config.ENABLE_IMAGE is True
    assert Config.IMAGE_WIDTH == 800
    assert Config.IMAGE_THEME == "dark"
    assert Config.TIMEZONE == "Asia/Shanghai"


def test_config_validation_missing_bot_token():
    """测试缺少 BOT_TOKEN"""
    errors = Config.validate()
    # 如果 BOT_TOKEN 未设置，应该有错误
    if not Config.BOT_TOKEN:
        assert any("BOT_TOKEN" in e for e in errors)


def test_config_validation_missing_api_id():
    """测试缺少 API_ID"""
    if not Config.API_ID:
        errors = Config.validate()
        assert any("API_ID" in e for e in errors)


def test_config_validation_missing_api_hash():
    """测试缺少 API_HASH"""
    if not Config.API_HASH:
        errors = Config.validate()
        assert any("API_HASH" in e for e in errors)
