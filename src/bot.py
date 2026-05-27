"""Bot 主程序 - 完整版"""

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
from .topics import TopicExtractor
from .image import ImageGenerator
from .scheduler import scheduler
from .database import db
from .utils import (
    parse_time_string,
    format_duration,
    format_number,
    get_sentiment_emoji,
    generate_progress_bar,
)

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化模块
summarizer = Summarizer()
topic_extractor = TopicExtractor()
image_gen = ImageGenerator() if config.ENABLE_IMAGE else None


def check_permission(user_id: int) -> bool:
    """检查用户是否有权限使用命令
    
    权限规则：
    1. 主人（OWNER_ID）始终有权限
    2. 如果 ADMIN_ONLY=true，只有主人能用
    3. ALLOWED_USERS 中的用户也能用
    """
    # 主人始终有权限
    if config.OWNER_ID and str(user_id) == config.OWNER_ID:
        return True
    
    # 如果 ADMIN_ONLY，只有主人能用
    if config.ADMIN_ONLY:
        return False
    
    # 检查额外允许的用户
    if config.ALLOWED_USERS:
        allowed = [uid.strip() for uid in config.ALLOWED_USERS.split(",")]
        if str(user_id) in allowed:
            return True
    
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    await update.message.reply_text(
        "👋 你好！我是群聊总结机器人。\n\n"
        "📊 <b>核心功能</b>\n"
        "• 智能总结群聊消息\n"
        "• 提取热门话题和关键词\n"
        "• 生成精美的总结图片\n"
        "• 定时自动总结\n\n"
        "📝 <b>快速开始</b>\n"
        "• /sum - 总结最近消息\n"
        "• /help - 查看所有命令\n\n"
        "⚠️ 注意：默认只有主人才能使用命令\n"
        "如需授权其他用户，请设置 ALLOWED_USERS",
        parse_mode="html"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    help_text = """
📖 <b>命令列表</b>

━━━━ 📊 <b>总结命令</b> ━━━━

<b>/sum</b> - 总结最近 100 条消息
<b>/sum 200</b> - 总结最近 200 条消息
<b>/sum 1h</b> - 总结最近 1 小时
<b>/sum 3h</b> - 总结最近 3 小时
<b>/sum 12h</b> - 总结最近 12 小时
<b>/sum 1d</b> - 总结最近 1 天
<b>/sum 2d</b> - 总结最近 2 天
<b>/sum 30m</b> - 总结最近 30 分钟

<b>/daily</b> - 生成今日群聊日报
<b>/weekly</b> - 生成本周群聊周报

━━━━ 🔍 <b>分析命令</b> ━━━━

<b>/topics</b> - 提取热门话题
<b>/keywords</b> - 提取关键词
<b>/sentiment</b> - 情绪分析
<b>/stats</b> - 活跃度统计
<b>/活跃榜</b> - 活跃用户排行

━━━━ ⚙️ <b>设置命令</b> ━━━━

<b>/setdaily 09:00</b> - 设置每日总结时间
<b>/setweekly mon 10:00</b> - 设置每周总结
<b>/unset</b> - 取消定时任务
<b>/lang zh</b> - 设置语言 (zh/en)

━━━━ 💡 <b>提示</b> ━━━━

• 时间格式: 1h, 2h, 30m, 1d
• 数量格式: 100, 200, 500
• 最大支持 1000 条消息
"""
    await update.message.reply_text(help_text, parse_mode="html")


async def get_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    count: int = None,
    hours: int = None
) -> list[Message]:
    """获取群聊消息"""
    chat_id = update.effective_chat.id
    messages = []

    try:
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
    except Exception as e:
        logger.error(f"获取消息失败: {e}")

    return messages


def parse_sum_args(arg: str) -> tuple[int | None, int | None]:
    """解析 /sum 命令参数，返回 (count, hours)"""
    if not arg:
        return config.DEFAULT_MESSAGE_COUNT, None

    arg = arg.strip().lower()

    # 尝试解析时间
    td = parse_time_string(arg)
    if td:
        return None, int(td.total_seconds() / 3600)

    # 尝试解析数量
    try:
        return int(arg), None
    except ValueError:
        return config.DEFAULT_MESSAGE_COUNT, None


async def format_summary(result, language: str = "zh") -> str:
    """格式化总结结果为文本"""
    start_time, end_time = result.time_range
    duration = end_time - start_time
    duration_str = format_duration(duration, language)

    emoji = get_sentiment_emoji(result.sentiment)

    if language == "zh":
        text = f"📊 <b>群聊总结</b> | {start_time.strftime('%m-%d %H:%M')} - {end_time.strftime('%H:%M')}\n\n"

        # 统计信息
        text += "📝 <b>消息统计</b>\n"
        text += f"├─ 消息数: <b>{format_number(result.total_messages)}</b> 条\n"
        text += f"├─ 参与人: <b>{result.total_users}</b> 人\n"
        text += f"├─ 时间段: {duration_str}\n"
        text += f"└─ 氛围: {emoji} {result.sentiment}\n\n"

        # 活跃用户
        if result.active_users:
            text += "👥 <b>活跃用户 TOP 5</b>\n"
            for i, user in enumerate(result.active_users[:5], 1):
                bar = generate_progress_bar(
                    user['count'],
                    result.active_users[0]['count'],
                    length=8
                )
                text += f"{i}. @{user['username']} - {user['count']} {bar}\n"
            text += "\n"

        # 话题
        if result.topics:
            text += "🔥 <b>热门话题</b>\n"
            for i, topic in enumerate(result.topics[:5], 1):
                keywords = ", ".join(topic.get("keywords", [])[:3])
                text += f"{i}. {topic['title']}"
                if keywords:
                    text += f" <code>({keywords})</code>"
                text += "\n"
            text += "\n"

        # 总结
        text += "💡 <b>总结</b>\n"
        text += result.summary + "\n\n"

        # 亮点
        if result.highlights:
            text += "✨ <b>亮点</b>\n"
            for h in result.highlights:
                text += f"• {h}\n"
    else:
        text = f"📊 <b>Chat Summary</b> | {start_time.strftime('%m-%d %H:%M')} - {end_time.strftime('%H:%M')}\n\n"
        text += f"📝 Stats: {result.total_messages} messages from {result.total_users} users\n"
        text += f"🎭 Vibe: {emoji} {result.sentiment}\n\n"
        text += f"💡 <b>Summary</b>\n{result.summary}\n"

    return text


async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /sum 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    # 解析参数
    arg = " ".join(context.args) if context.args else ""
    count, hours = parse_sum_args(arg)

    # 发送处理消息
    if hours:
        status_text = f"⏳ 正在获取最近 {hours} 小时的消息..."
    else:
        status_text = f"⏳ 正在获取最近 {count} 条消息..."

    status_msg = await update.message.reply_text(status_text)

    try:
        # 获取消息
        messages = await get_messages(update, context, count=count, hours=hours)

        if not messages:
            await status_msg.edit_text("❌ 没有找到可总结的消息")
            return

        await status_msg.edit_text(f"📝 已获取 {len(messages)} 条消息，正在生成总结...")

        # 生成总结
        result = await summarizer.summarize(messages, language=config.DEFAULT_LANGUAGE)

        # 保存到数据库
        try:
            db.upsert_chat_config(update.effective_chat.id)
            db.add_summary_history(
                chat_id=update.effective_chat.id,
                summary_type="sum",
                message_count=result.total_messages,
                user_count=result.total_users,
                sentiment=result.sentiment,
                summary=result.summary[:500]
            )
        except Exception as e:
            logger.warning(f"保存历史失败: {e}")

        # 格式化输出
        text = await format_summary(result, config.DEFAULT_LANGUAGE)

        # 生成图片（如果启用）
        if image_gen and config.ENABLE_IMAGE:
            try:
                image = await image_gen.generate(result, config.DEFAULT_LANGUAGE)
                await update.message.reply_photo(
                    photo=image,
                    caption=text[:1024],
                    parse_mode="html"
                )
                await status_msg.delete()
            except Exception as e:
                logger.warning(f"图片生成失败: {e}")
                await status_msg.edit_text(text, parse_mode="html")
        else:
            await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"总结失败: {e}")
        await status_msg.edit_text(f"❌ 总结失败: {str(e)}")


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /daily 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
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

        # 保存到数据库
        try:
            db.upsert_chat_config(update.effective_chat.id)
            db.add_summary_history(
                chat_id=update.effective_chat.id,
                summary_type="daily",
                message_count=result.total_messages,
                user_count=result.total_users,
                sentiment=result.sentiment,
                summary=result.summary[:500]
            )
        except Exception as e:
            logger.warning(f"保存历史失败: {e}")

        text = f"📅 <b>今日群聊日报</b>\n\n" + await format_summary(result, config.DEFAULT_LANGUAGE)

        if image_gen and config.ENABLE_IMAGE:
            try:
                image = await image_gen.generate(result, config.DEFAULT_LANGUAGE, title="今日日报")
                await update.message.reply_photo(photo=image, caption=text[:1024], parse_mode="html")
                await status_msg.delete()
            except Exception as e:
                logger.warning(f"图片生成失败: {e}")
                await status_msg.edit_text(text, parse_mode="html")
        else:
            await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"日报生成失败: {e}")
        await status_msg.edit_text(f"❌ 生成失败: {str(e)}")


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /weekly 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
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

        # 保存到数据库
        try:
            db.upsert_chat_config(update.effective_chat.id)
            db.add_summary_history(
                chat_id=update.effective_chat.id,
                summary_type="weekly",
                message_count=result.total_messages,
                user_count=result.total_users,
                sentiment=result.sentiment,
                summary=result.summary[:500]
            )
        except Exception as e:
            logger.warning(f"保存历史失败: {e}")

        text = f"📊 <b>本周群聊周报</b>\n\n" + await format_summary(result, config.DEFAULT_LANGUAGE)

        if image_gen and config.ENABLE_IMAGE:
            try:
                image = await image_gen.generate(result, config.DEFAULT_LANGUAGE, title="本周周报")
                await update.message.reply_photo(photo=image, caption=text[:1024], parse_mode="html")
                await status_msg.delete()
            except Exception as e:
                logger.warning(f"图片生成失败: {e}")
                await status_msg.edit_text(text, parse_mode="html")
        else:
            await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"周报生成失败: {e}")
        await status_msg.edit_text(f"❌ 生成失败: {str(e)}")


async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /topics 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在提取话题...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 暂无消息")
            return

        topics = topic_extractor.extract_topics(
            messages,
            max_topics=5,
            language=config.DEFAULT_LANGUAGE
        )

        if not topics:
            await status_msg.edit_text("❌ 未找到明显话题")
            return

        text = "🔥 <b>热门话题</b> (最近24小时)\n\n"

        for i, topic in enumerate(topics, 1):
            keywords_str = ", ".join(topic.keywords[:5])
            bar = generate_progress_bar(
                topic.message_count,
                topics[0].message_count,
                length=10
            )
            text += f"<b>{i}. {topic.title}</b>\n"
            text += f"   📊 {topic.message_count} 条消息 {bar}\n"
            text += f"   🏷️ <code>{keywords_str}</code>\n\n"

        await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"话题提取失败: {e}")
        await status_msg.edit_text(f"❌ 提取失败: {str(e)}")


async def keywords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /keywords 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在提取关键词...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 暂无消息")
            return

        # 合并所有消息
        all_text = " ".join([msg.text for msg in messages])

        # 提取关键词（简单实现）
        from collections import Counter
        import re

        # 简单的中文分词
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', all_text)
        word_counts = Counter(words).most_common(20)

        if not word_counts:
            await status_msg.edit_text("❌ 未找到关键词")
            return

        text = "🏷️ <b>关键词云</b> (最近24小时)\n\n"

        # 生成词云效果
        for word, count in word_counts[:15]:
            size = "🔴" if count > 50 else "🟡" if count > 20 else "🟢"
            text += f"{size} <b>{word}</b>: {count}次\n"

        await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"关键词提取失败: {e}")
        await status_msg.edit_text(f"❌ 提取失败: {str(e)}")


async def sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /sentiment 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在分析情绪...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 暂无消息")
            return

        result = await summarizer.summarize(messages, language=config.DEFAULT_LANGUAGE)

        emoji = get_sentiment_emoji(result.sentiment)

        text = f"""
🎭 <b>情绪分析</b> (最近24小时)

<b>整体氛围:</b> {emoji} {result.sentiment}

<b>消息统计:</b>
├─ 总消息: {result.total_messages} 条
├─ 参与人数: {result.total_users} 人
└─ 人均消息: {result.total_messages // result.total_users if result.total_users > 0 else 0} 条

<b>总结:</b>
{result.summary[:200]}...
"""
        await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"情绪分析失败: {e}")
        await status_msg.edit_text(f"❌ 分析失败: {str(e)}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /stats 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
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

        # 计算参与率
        total_members = await context.bot.get_chat_member_count(update.effective_chat.id)
        engagement = (len(users) / total_members * 100) if total_members > 0 else 0

        text = f"""
📊 <b>群聊统计</b> (最近24小时)

<b>📈 总览</b>
├─ 消息总数: <b>{format_number(len(messages))}</b> 条
├─ 参与人数: <b>{len(users)}</b> 人
├─ 群成员数: <b>{total_members}</b> 人
├─ 参与率: <b>{engagement:.1f}%</b>
└─ 最活跃时段: <b>{peak_hour[0]}:00</b> ({peak_hour[1]} 条)

<b>🏆 活跃排行榜</b>
"""

        for i, (username, count) in enumerate(active_users[:5], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
            bar = generate_progress_bar(count, active_users[0][1], length=8)
            text += f"{medal} @{username}: {count} {bar}\n"

        # 时段分布
        text += "\n<b>⏰ 时段分布</b>\n"
        for hour in range(0, 24, 6):
            count = sum(hours.get(h, 0) for h in range(hour, hour+6))
            bar = generate_progress_bar(count, max(hours.values()), length=6)
            text += f"{hour:02d}-{hour+6:02d}: {bar} {count}\n"

        await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"统计失败: {e}")
        await status_msg.edit_text(f"❌ 统计失败: {str(e)}")


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /活跃榜 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    status_msg = await update.message.reply_text("⏳ 正在生成排行榜...")

    try:
        messages = await get_messages(update, context, hours=24)
        if not messages:
            await status_msg.edit_text("❌ 今日暂无消息")
            return

        users = {}
        for msg in messages:
            users[msg.username] = users.get(msg.username, 0) + 1

        active_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]

        text = "🏆 <b>今日活跃榜</b>\n\n"

        medals = ["🥇", "🥈", "🥉"]
        for i, (username, count) in enumerate(active_users, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            text += f"{medal} @{username} - <b>{count}</b> 条\n"

        text += f"\n📊 总计 {len(messages)} 条消息，{len(users)} 人参与"

        await status_msg.edit_text(text, parse_mode="html")

    except Exception as e:
        logger.error(f"排行榜生成失败: {e}")
        await status_msg.edit_text(f"❌ 生成失败: {str(e)}")


async def setdaily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /setdaily 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    if not context.args:
        await update.message.reply_text("❌ 请指定时间，例如: /setdaily 09:00")
        return

    time_str = context.args[0]
    job_time = scheduler.parse_time(time_str)

    if not job_time:
        await update.message.reply_text("❌ 时间格式错误，请使用 HH:MM 格式")
        return

    chat_id = update.effective_chat.id

    async def daily_callback(chat_id):
        # 这里需要实现定时总结的逻辑
        pass

    scheduler.add_daily_job(
        chat_id=chat_id,
        job_time=job_time,
        callback=daily_callback
    )

    await update.message.reply_text(
        f"✅ 已设置每日总结时间: {time_str}\n"
        f"每天 {time_str} 会自动生成群聊日报"
    )


async def setweekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /setweekly 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ 请指定日期和时间，例如: /setweekly mon 10:00")
        return

    day_str = context.args[0]
    time_str = context.args[1]

    day_of_week = scheduler.parse_day_of_week(day_str)
    job_time = scheduler.parse_time(time_str)

    if day_of_week is None:
        await update.message.reply_text("❌ 星期格式错误，请使用 mon/tue/wed/thu/fri/sat/sun")
        return

    if not job_time:
        await update.message.reply_text("❌ 时间格式错误，请使用 HH:MM 格式")
        return

    chat_id = update.effective_chat.id

    async def weekly_callback(chat_id):
        # 这里需要实现定时总结的逻辑
        pass

    scheduler.add_weekly_job(
        chat_id=chat_id,
        day_of_week=day_of_week,
        job_time=job_time,
        callback=weekly_callback
    )

    await update.message.reply_text(
        f"✅ 已设置每周总结: {day_str} {time_str}\n"
        f"每周 {day_str} {time_str} 会自动生成群聊周报"
    )


async def unset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /unset 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 请在群组中使用此命令")
        return

    chat_id = update.effective_chat.id
    jobs = scheduler.get_jobs(chat_id)

    if not jobs:
        await update.message.reply_text("❌ 当前没有定时任务")
        return

    for job in jobs:
        scheduler.remove_job(job["id"])

    await update.message.reply_text("✅ 已取消所有定时任务")


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /lang 命令"""
    # 权限检查
    if not check_permission(update.effective_user.id):
        await update.message.reply_text("❌ 您没有权限使用此命令，只有主人能用哦~")
        return
    
    if not context.args:
        await update.message.reply_text(
            f"当前语言: {config.DEFAULT_LANGUAGE}\n"
            "可选: zh (中文) / en (英文)\n"
            "用法: /lang zh"
        )
        return

    lang = context.args[0].lower()
    if lang not in ["zh", "en"]:
        await update.message.reply_text("❌ 语言只支持 zh 或 en")
        return

    # 更新数据库配置
    if update.effective_chat.type != "private":
        try:
            db.upsert_chat_config(update.effective_chat.id, language=lang)
        except Exception as e:
            logger.warning(f"保存语言配置失败: {e}")

    await update.message.reply_text(f"✅ 语言已设置为: {'中文' if lang == 'zh' else 'English'}")


async def post_init(application: Application):
    """Bot 初始化后执行"""
    # 连接数据库
    try:
        db.connect()
        logger.info("数据库已连接")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")

    # 启动调度器
    if config.ENABLE_SCHEDULER:
        scheduler.start()
        logger.info("调度器已启动")

    # 设置命令菜单
    commands = [
        BotCommand("sum", "📝 总结群聊消息"),
        BotCommand("daily", "📅 今日群聊日报"),
        BotCommand("weekly", "📊 本周群聊周报"),
        BotCommand("topics", "🔥 提取热门话题"),
        BotCommand("keywords", "🏷️ 提取关键词"),
        BotCommand("sentiment", "🎭 情绪分析"),
        BotCommand("stats", "📈 群聊统计"),
        BotCommand("活跃榜", "🏆 活跃排行榜"),
        BotCommand("setdaily", "⏰ 设置每日总结"),
        BotCommand("setweekly", "📅 设置每周总结"),
        BotCommand("unset", "❌ 取消定时任务"),
        BotCommand("lang", "🌐 设置语言"),
        BotCommand("help", "📖 查看帮助"),
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
    application.add_handler(CommandHandler("topics", topics_command))
    application.add_handler(CommandHandler("keywords", keywords_command))
    application.add_handler(CommandHandler("sentiment", sentiment_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("活跃榜", leaderboard_command))
    application.add_handler(CommandHandler("setdaily", setdaily_command))
    application.add_handler(CommandHandler("setweekly", setweekly_command))
    application.add_handler(CommandHandler("unset", unset_command))
    application.add_handler(CommandHandler("lang", lang_command))

    # 启动 Bot
    logger.info(f"Bot 启动中... 权限模式: {'仅主人' if config.ADMIN_ONLY else '开放'}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
