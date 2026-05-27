"""Bot 主程序"""

import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import config
from .summarizer import Summarizer, Message
from .image import ImageGenerator

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化模块
summarizer = Summarizer()
image_gen = ImageGenerator() if config.ENABLE_IMAGE else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    await update.message.reply_text(
        "👋 你好！我是群聊总结机器人。\n\n"
        "使用方法：\n"
        "/sum - 总结最近 100 条消息\n"
        "/sum 200 - 总结最近 200 条消息\n"
        "/sum 2h - 总结最近 2 小时的消息\n"
        "/daily - 生成今日群聊日报\n"
        "/weekly - 生成本周群聊周报\n"
        "/topics - 提取热门话题\n"
        "/stats - 群聊活跃度统计\n\n"
        "将我添加到群组即可使用！"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    await update.message.reply_text(
        "📖 命令列表：\n\n"
        "📊 总结命令：\n"
        "/sum - 总结最近 100 条消息\n"
        "/sum <数量> - 总结指定数量的消息\n"
        "/sum <时间> - 总结指定时间的消息 (如: 2h, 1d)\n"
        "/daily - 今日群聊日报\n"
        "/weekly - 本周群聊周报\n\n"
        "🔍 分析命令：\n"
        "/topics - 提取热门话题\n"
        "/stats - 活跃度统计\n\n"
        "⚙️ 设置命令：\n"
        "/setdaily <时间> - 设置每日总结时间\n"
        "/setweekly <星期> <时间> - 设置每周总结时间\n"
        "/lang <zh/en> - 设置语言"
    )


async def get_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    count: int = None,
    hours: int = None
) -> list[Message]:
    """获取群聊消息"""
    chat_id = update.effective_chat.id
    messages = []

    if hours:
        # 按时间获取
        since = datetime.now() - timedelta(hours=hours)
        async for message in context.bot.get_chat_history(
            chat_id=chat_id,
            offset_date=since
        ):
            if message.text:
                messages.append(Message(
                    id=message.id,
                    user_id=message.from_user.id if message.from_user else 0,
                    username=message.from_user.username or "unknown" if message.from_user else "unknown",
                    text=message.text,
                    timestamp=message.date,
                    reply_to=message.reply_to_message.id if message.reply_to_message else None
                ))
    else:
        # 按数量获取
        count = count or config.DEFAULT_MESSAGE_COUNT
        count = min(count, config.MAX_MESSAGE_COUNT)
        async for message in context.bot.get_chat_history(
            chat_id=chat_id,
            limit=count
        ):
            if message.text:
                messages.append(Message(
                    id=message.id,
                    user_id=message.from_user.id if message.from_user else 0,
                    username=message.from_user.username or "unknown" if message.from_user else "unknown",
                    text=message.text,
                    timestamp=message.date,
                    reply_to=message.reply_to_message.id if message.reply_to_message else None
                ))

    messages.reverse()  # 按时间正序
    return messages


def parse_time_arg(arg: str) -> tuple[int | None, int | None]:
    """解析时间参数，返回 (count, hours)"""
    if not arg:
        return config.DEFAULT_MESSAGE_COUNT, None

    arg = arg.strip().lower()

    # 小时
    if arg.endswith("h"):
        try:
            return None, int(arg[:-1])
        except ValueError:
            pass

    # 天
    if arg.endswith("d"):
        try:
            return None, int(arg[:-1]) * 24
        except ValueError:
            pass

    # 数量
    try:
        return int(arg), None
    except ValueError:
        return config.DEFAULT_MESSAGE_COUNT, None


async def format_summary(result, language: str = "zh") -> str:
    """格式化总结结果为文本"""
    start_time, end_time = result.time_range
    time_str = f"{start_time.strftime('%m-%d %H:%M')} - {end_time.strftime('%H:%M')}"

    if language == "zh":
        text = f"📊 群聊总结 | {time_str}\n\n"

        text += "📝 消息统计\n"
        text += f"├─ 总消息数: {result.total_messages} 条\n"
        text += f"├─ 参与人数: {result.total_users} 人\n"
        text += f"└─ 整体氛围: {result.sentiment}\n\n"

        if result.topics:
            text += "🔥 热门话题\n"
            for i, topic in enumerate(result.topics[:5], 1):
                keywords = ", ".join(topic.get("keywords", [])[:3])
                text += f"{i}. {topic['title']}"
                if keywords:
                    text += f" ({keywords})"
                text += "\n"
            text += "\n"

        if result.active_users:
            text += "👥 活跃用户 TOP 5\n"
            for i, user in enumerate(result.active_users[:5], 1):
                text += f"{i}. @{user['username']} - {user['count']} 条\n"
            text += "\n"

        text += "💡 总结\n"
        text += result.summary + "\n\n"

        if result.highlights:
            text += "✨ 亮点\n"
            for h in result.highlights:
                text += f"• {h}\n"
    else:
        text = f"📊 Chat Summary | {time_str}\n\n"
        text += f"📝 Stats: {result.total_messages} messages from {result.total_users} users\n"
        text += f"🎭 Vibe: {result.sentiment}\n\n"
        text += f"💡 Summary\n{result.summary}\n"

    return text


async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /sum 命令"""
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    # 解析参数
    arg = " ".join(context.args) if context.args else ""
    count, hours = parse_time_arg(arg)

    # 发送处理消息
    status_msg = await update.message.reply_text("⏳ 正在获取消息并生成总结...")

    try:
        # 获取消息
        messages = await get_messages(update, context, count=count, hours=hours)

        if not messages:
            await status_msg.edit_text("❌ 没有找到可总结的消息")
            return

        await status_msg.edit_text(f"📝 已获取 {len(messages)} 条消息，正在生成总结...")

        # 生成总结
        result = await summarizer.summarize(messages, language=config.DEFAULT_LANGUAGE)

        # 格式化输出
        text = await format_summary(result, config.DEFAULT_LANGUAGE)

        # 生成图片（如果启用）
        if image_gen and config.ENABLE_IMAGE:
            image = await image_gen.generate(result, config.DEFAULT_LANGUAGE)
            await update.message.reply_photo(
                photo=image,
                caption=text[:1024]  # Telegram 限制 caption 长度
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"总结失败: {e}")
        await status_msg.edit_text(f"❌ 总结失败: {str(e)}")


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /daily 命令"""
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在生成今日日报...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 今日暂无消息")
            return

        result = await summarizer.summarize(messages, language=config.DEFAULT_LANGUAGE)
        text = f"📅 今日群聊日报\n\n" + await format_summary(result, config.DEFAULT_LANGUAGE)

        if image_gen and config.ENABLE_IMAGE:
            image = await image_gen.generate(result, config.DEFAULT_LANGUAGE, title="今日日报")
            await update.message.reply_photo(photo=image, caption=text[:1024])
            await status_msg.delete()
        else:
            await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"日报生成失败: {e}")
        await status_msg.edit_text(f"❌ 生成失败: {str(e)}")


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /weekly 命令"""
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在生成本周周报...")

    try:
        messages = await get_messages(update, context, hours=168)  # 7 天
        if not messages:
            await status_msg.edit_text("❌ 本周暂无消息")
            return

        result = await summarizer.summarize(messages, language=config.DEFAULT_LANGUAGE)
        text = f"📊 本周群聊周报\n\n" + await format_summary(result, config.DEFAULT_LANGUAGE)

        if image_gen and config.ENABLE_IMAGE:
            image = await image_gen.generate(result, config.DEFAULT_LANGUAGE, title="本周周报")
            await update.message.reply_photo(photo=image, caption=text[:1024])
            await status_msg.delete()
        else:
            await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"周报生成失败: {e}")
        await status_msg.edit_text(f"❌ 生成失败: {str(e)}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /stats 命令"""
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在统计...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 今日暂无消息")
            return

        # 统计数据
        users = {}
        hours = {}
        for msg in messages:
            users[msg.username] = users.get(msg.username, 0) + 1
            hour = msg.timestamp.hour
            hours[hour] = hours.get(hour, 0) + 1

        active_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
        peak_hour = max(hours.items(), key=lambda x: x[1])

        text = "📊 群聊统计 (最近24小时)\n\n"
        text += f"📝 总消息数: {len(messages)} 条\n"
        text += f"👥 参与人数: {len(users)} 人\n"
        text += f"⏰ 最活跃时段: {peak_hour[0]}:00 ({peak_hour[1]} 条)\n\n"

        text += "🏆 活跃排行榜\n"
        for i, (username, count) in enumerate(active_users, 1):
            bar = "█" * min(count // 5, 20)
            text += f"{i}. @{username}: {count} {bar}\n"

        await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"统计失败: {e}")
        await status_msg.edit_text(f"❌ 统计失败: {str(e)}")


async def post_init(application: Application):
    """Bot 初始化后执行"""
    # 设置命令菜单
    commands = [
        BotCommand("sum", "总结群聊消息"),
        BotCommand("daily", "今日群聊日报"),
        BotCommand("weekly", "本周群聊周报"),
        BotCommand("topics", "提取热门话题"),
        BotCommand("stats", "群聊活跃度统计"),
        BotCommand("help", "查看帮助"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot 已启动")


def main():
    """主函数"""
    # 验证配置
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"配置错误: {error}")
        return

    # 创建应用
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sum", sum_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("weekly", weekly_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # 启动 Bot
    logger.info("Bot 启动中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
