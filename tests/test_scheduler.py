"""测试定时任务模块"""

import pytest
from datetime import time
from src.scheduler import Scheduler


@pytest.fixture
def scheduler():
    """调度器实例"""
    return Scheduler()


def test_scheduler_init(scheduler):
    """测试调度器初始化"""
    assert scheduler.scheduler is not None
    assert scheduler.jobs == {}


def test_parse_time_valid(scheduler):
    """测试解析有效时间"""
    t = scheduler.parse_time("09:30")
    assert t is not None
    assert t.hour == 9
    assert t.minute == 30

    t = scheduler.parse_time("23:59")
    assert t is not None
    assert t.hour == 23
    assert t.minute == 59

    t = scheduler.parse_time("00:00")
    assert t is not None
    assert t.hour == 0
    assert t.minute == 0


def test_parse_time_invalid(scheduler):
    """测试解析无效时间"""
    assert scheduler.parse_time("25:00") is None
    assert scheduler.parse_time("12:60") is None
    assert scheduler.parse_time("abc") is None
    assert scheduler.parse_time("12") is None
    assert scheduler.parse_time("") is None


def test_parse_day_of_week_valid(scheduler):
    """测试解析有效星期"""
    assert scheduler.parse_day_of_week("mon") == 0
    assert scheduler.parse_day_of_week("周一") == 0
    assert scheduler.parse_day_of_week("monday") == 0

    assert scheduler.parse_day_of_week("tue") == 1
    assert scheduler.parse_day_of_week("周二") == 1

    assert scheduler.parse_day_of_week("wed") == 2
    assert scheduler.parse_day_of_week("周三") == 2

    assert scheduler.parse_day_of_week("thu") == 3
    assert scheduler.parse_day_of_week("周四") == 3

    assert scheduler.parse_day_of_week("fri") == 4
    assert scheduler.parse_day_of_week("周五") == 4

    assert scheduler.parse_day_of_week("sat") == 5
    assert scheduler.parse_day_of_week("周六") == 5

    assert scheduler.parse_day_of_week("sun") == 6
    assert scheduler.parse_day_of_week("周日") == 6


def test_parse_day_of_week_invalid(scheduler):
    """测试解析无效星期"""
    assert scheduler.parse_day_of_week("monday2") is None
    assert scheduler.parse_day_of_week("xyz") is None
    assert scheduler.parse_day_of_week("") is None


def test_parse_day_of_week_case_insensitive(scheduler):
    """测试星期解析大小写不敏感"""
    assert scheduler.parse_day_of_week("Mon") == 0
    assert scheduler.parse_day_of_week("MON") == 0
    assert scheduler.parse_day_of_week("Mon") == 0


@pytest.mark.asyncio
async def test_add_daily_job(scheduler):
    """测试添加每日任务"""
    async def dummy_callback(chat_id):
        pass

    scheduler.add_daily_job(
        chat_id=123456,
        job_time=time(9, 0),
        callback=dummy_callback
    )

    jobs = scheduler.get_jobs(123456)
    assert len(jobs) == 1
    assert jobs[0]["type"] == "daily"
    assert jobs[0]["time"] == "09:00"


@pytest.mark.asyncio
async def test_add_weekly_job(scheduler):
    """测试添加每周任务"""
    async def dummy_callback(chat_id):
        pass

    scheduler.add_weekly_job(
        chat_id=123456,
        day_of_week=0,
        job_time=time(10, 0),
        callback=dummy_callback
    )

    jobs = scheduler.get_jobs(123456)
    assert len(jobs) == 1
    assert jobs[0]["type"] == "weekly"
    assert jobs[0]["day_of_week"] == 0
    assert jobs[0]["time"] == "10:00"


@pytest.mark.asyncio
async def test_add_interval_job(scheduler):
    """测试添加间隔任务"""
    async def dummy_callback(chat_id):
        pass

    scheduler.add_interval_job(
        chat_id=123456,
        hours=6,
        callback=dummy_callback
    )

    jobs = scheduler.get_jobs(123456)
    assert len(jobs) == 1
    assert jobs[0]["type"] == "interval"
    assert jobs[0]["hours"] == 6


def test_remove_job(scheduler):
    """测试移除任务"""
    async def dummy_callback(chat_id):
        pass

    scheduler.add_daily_job(
        chat_id=123456,
        job_time=time(9, 0),
        callback=dummy_callback,
        job_id="test_job"
    )

    assert len(scheduler.get_jobs(123456)) == 1

    scheduler.remove_job("test_job")
    assert len(scheduler.get_jobs(123456)) == 0


def test_remove_nonexistent_job(scheduler):
    """测试移除不存在的任务"""
    # 不应该抛出异常
    scheduler.remove_job("nonexistent_job")


def test_get_jobs_by_chat_id(scheduler):
    """测试按 chat_id 获取任务"""
    async def dummy_callback(chat_id):
        pass

    scheduler.add_daily_job(
        chat_id=111,
        job_time=time(9, 0),
        callback=dummy_callback
    )

    scheduler.add_daily_job(
        chat_id=222,
        job_time=time(10, 0),
        callback=dummy_callback
    )

    assert len(scheduler.get_jobs(111)) == 1
    assert len(scheduler.get_jobs(222)) == 1
    assert len(scheduler.get_jobs()) == 2


def test_get_jobs_empty(scheduler):
    """测试获取空任务列表"""
    assert scheduler.get_jobs() == []
    assert scheduler.get_jobs(999) == []
