"""配置管理模块"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """应用配置"""

    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")

    # AI Provider
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")  # openai / anthropic / local
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    LOCAL_MODEL_URL: str = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")

    # 总结配置
    DEFAULT_MESSAGE_COUNT: int = int(os.getenv("DEFAULT_MESSAGE_COUNT", "100"))
    MAX_MESSAGE_COUNT: int = int(os.getenv("MAX_MESSAGE_COUNT", "1000"))
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "zh")

    # 图片生成
    ENABLE_IMAGE: bool = os.getenv("ENABLE_IMAGE", "true").lower() == "true"
    IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "800"))
    IMAGE_THEME: str = os.getenv("IMAGE_THEME", "dark")  # dark / light

    # 定时任务
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Shanghai")

    # 数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data.db")

    @classmethod
    def validate(cls) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN 未设置")
        if not cls.API_ID:
            errors.append("API_ID 未设置")
        if not cls.API_HASH:
            errors.append("API_HASH 未设置")
        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 未设置 (AI_PROVIDER=openai)")
        if cls.AI_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY 未设置 (AI_PROVIDER=anthropic)")
        return errors


config = Config()
