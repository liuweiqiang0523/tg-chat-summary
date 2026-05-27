"""定时任务调度模块"""

import logging
from datetime import datetime, time
from typing import Optional, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import config

logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
        self.jobs: dict[str, dict] = {}

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")

    def add_daily_job(
        self,
        chat_id: int,
        job_time: time,
        callback: Callable[..., Awaitable],
        job_id: str = None
    ):
        """添加每日定时任务"""
        job_id = job_id or f"daily_{chat_id}"

        # 移除已存在的任务
        self.remove_job(job_id)

        # 添加新任务
        self.scheduler.add_job(
            callback,
            trigger=CronTrigger(
                hour=job_time.hour,
                minute=job_time.minute,
                timezone=config.TIMEZONE
            ),
            id=job_id,
            kwargs={"chat_id": chat_id},
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "daily",
            "chat_id": chat_id,
            "time": job_time.strftime("%H:%M"),
            "created_at": datetime.now()
        }

        logger.info(f"添加每日任务: {job_id} at {job_time}")

    def add_weekly_job(
        self,
        chat_id: int,
        day_of_week: int,
        job_time: time,
        callback: Callable[..., Awaitable],
        job_id: str = None
    ):
        """添加每周定时任务"""
        job_id = job_id or f"weekly_{chat_id}"

        # 移除已存在的任务
        self.remove_job(job_id)

        # 添加新任务
        self.scheduler.add_job(
            callback,
            trigger=CronTrigger(
                day_of_week=day_of_week,
                hour=job_time.hour,
                minute=job_time.minute,
                timezone=config.TIMEZONE
            ),
            id=job_id,
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "weekly",
            "chat_id": chat_id,
            "day_of_week": day_of_week,
            "time": job_time.strftime("%H:%M"),
            "created_at": datetime.now()
        }

        logger.info(f"添加每周任务: {job_id} on day {day_of_week} at {job_time}")

    def add_interval_job(
        self,
        chat_id: int,
        hours: int,
        callback: Callable[..., Awaitable],
        job_id: str = None
    ):
        """添加间隔定时任务"""
        job_id = job_id or f"interval_{chat_id}"

        # 移除已存在的任务
        self.remove_job(job_id)

        # 添加新任务
        self.scheduler.add_job(
            callback,
            trigger=IntervalTrigger(hours=hours),
            id=job_id,
            kwargs={"chat_id": chat_id},
            replace_existing=True
        )

        self.jobs[job_id] = {
            "type": "interval",
            "chat_id": chat_id,
            "hours": hours,
            "created_at": datetime.now()
        }

        logger.info(f"添加间隔任务: {job_id} every {hours}h")

    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            self.jobs.pop(job_id, None)
            logger.info(f"移除任务: {job_id}")
        except Exception:
            pass

    def get_jobs(self, chat_id: int = None) -> list[dict]:
        """获取任务列表"""
        if chat_id:
            return [
                {"id": k, **v}
                for k, v in self.jobs.items()
                if v.get("chat_id") == chat_id
            ]
        return [{"id": k, **v} for k, v in self.jobs.items()]

    def parse_day_of_week(self, day_str: str) -> Optional[int]:
        """解析星期几"""
        days = {
            "mon": 0, "周一": 0, "monday": 0,
            "tue": 1, "周二": 1, "tuesday": 1,
            "wed": 2, "周三": 2, "wednesday": 2,
            "thu": 3, "周四": 3, "thursday": 3,
            "fri": 4, "周五": 4, "friday": 4,
            "sat": 5, "周六": 5, "saturday": 5,
            "sun": 6, "周日": 6, "sunday": 6,
        }
        return days.get(day_str.lower())

    def parse_time(self, time_str: str) -> Optional[time]:
        """解析时间字符串 (HH:MM)"""
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return time(hour, minute)
        except (ValueError, IndexError):
            pass
        return None


# 全局调度器实例
scheduler = Scheduler()
