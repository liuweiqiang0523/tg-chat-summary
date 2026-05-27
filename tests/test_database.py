"""测试数据库模块"""

import pytest
import sqlite3
from src.database import Database


@pytest.fixture
def db(tmp_path):
    """测试数据库"""
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    database.connect()
    yield database
    database.close()


def test_database_connect(db):
    """测试数据库连接"""
    assert db.conn is not None


def test_database_close(tmp_path):
    """测试关闭数据库"""
    db_path = str(tmp_path / "test_close.db")
    database = Database(db_path)
    database.connect()
    assert database.conn is not None

    database.close()
    assert database.conn is None


def test_create_tables(db):
    """测试创建表"""
    cursor = db.conn.cursor()

    # 检查 chat_config 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_config'")
    assert cursor.fetchone() is not None

    # 检查 summary_history 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='summary_history'")
    assert cursor.fetchone() is not None

    # 检查 scheduled_jobs 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_jobs'")
    assert cursor.fetchone() is not None


def test_upsert_chat_config_insert(db):
    """测试插入群组配置"""
    chat_id = 123456
    db.upsert_chat_config(chat_id, language="zh", enable_image=1)

    config = db.get_chat_config(chat_id)
    assert config is not None
    assert config["chat_id"] == chat_id
    assert config["language"] == "zh"
    assert config["enable_image"] == 1


def test_upsert_chat_config_update(db):
    """测试更新群组配置"""
    chat_id = 123456

    # 插入
    db.upsert_chat_config(chat_id, language="zh")
    config = db.get_chat_config(chat_id)
    assert config["language"] == "zh"

    # 更新
    db.upsert_chat_config(chat_id, language="en")
    config = db.get_chat_config(chat_id)
    assert config["language"] == "en"


def test_get_chat_config_not_exists(db):
    """测试获取不存在的群组配置"""
    config = db.get_chat_config(999999)
    assert config is None


def test_add_summary_history(db):
    """测试添加总结历史"""
    chat_id = 123456
    db.upsert_chat_config(chat_id)

    db.add_summary_history(
        chat_id=chat_id,
        summary_type="daily",
        message_count=100,
        user_count=20,
        sentiment="积极正面",
        summary="这是一段测试总结"
    )

    history = db.get_summary_history(chat_id)
    assert len(history) == 1
    assert history[0]["summary_type"] == "daily"
    assert history[0]["message_count"] == 100


def test_get_summary_history_multiple(db):
    """测试获取多条总结历史"""
    chat_id = 123456
    db.upsert_chat_config(chat_id)

    for i in range(5):
        db.add_summary_history(
            chat_id=chat_id,
            summary_type="sum",
            message_count=100 + i,
            user_count=20,
            sentiment="中性",
            summary=f"总结 {i}"
        )

    history = db.get_summary_history(chat_id, limit=3)
    assert len(history) == 3

    history = db.get_summary_history(chat_id, limit=10)
    assert len(history) == 5


def test_get_summary_history_order(db):
    """测试总结历史排序"""
    chat_id = 123456
    db.upsert_chat_config(chat_id)

    db.add_summary_history(chat_id, "sum", 100, 20, "中性", "第一条")
    db.add_summary_history(chat_id, "sum", 200, 30, "积极", "第二条")

    history = db.get_summary_history(chat_id)
    assert history[0]["summary"] == "第二条"  # 最新的在前
    assert history[1]["summary"] == "第一条"


def test_add_scheduled_job(db):
    """测试添加定时任务"""
    chat_id = 123456
    db.upsert_chat_config(chat_id)

    db.add_scheduled_job(chat_id, "daily", '{"time": "09:00"}')

    jobs = db.get_scheduled_jobs(chat_id)
    assert len(jobs) == 1
    assert jobs[0]["job_type"] == "daily"


def test_get_scheduled_jobs_all(db):
    """测试获取所有定时任务"""
    db.upsert_chat_config(111)
    db.upsert_chat_config(222)

    db.add_scheduled_job(111, "daily", '{"time": "09:00"}')
    db.add_scheduled_job(222, "weekly", '{"day": "mon", "time": "10:00"}')

    jobs = db.get_scheduled_jobs()
    assert len(jobs) == 2


def test_get_scheduled_jobs_by_chat(db):
    """测试按群组获取定时任务"""
    db.upsert_chat_config(111)
    db.upsert_chat_config(222)

    db.add_scheduled_job(111, "daily", '{"time": "09:00"}')
    db.add_scheduled_job(222, "weekly", '{"day": "mon", "time": "10:00"}')

    jobs = db.get_scheduled_jobs(111)
    assert len(jobs) == 1
    assert jobs[0]["job_type"] == "daily"


def test_deactivate_scheduled_job(db):
    """测试停用定时任务"""
    chat_id = 123456
    db.upsert_chat_config(chat_id)

    db.add_scheduled_job(chat_id, "daily", '{"time": "09:00"}')
    jobs = db.get_scheduled_jobs(chat_id)
    assert len(jobs) == 1

    job_id = jobs[0]["id"]
    db.deactivate_scheduled_job(job_id)

    jobs = db.get_scheduled_jobs(chat_id)
    assert len(jobs) == 0


def test_multiple_chat_configs(db):
    """测试多个群组配置"""
    for i in range(10):
        chat_id = 100000 + i
        db.upsert_chat_config(chat_id, language="zh" if i % 2 == 0 else "en")

    assert db.get_chat_config(100000)["language"] == "zh"
    assert db.get_chat_config(100001)["language"] == "en"
    assert db.get_chat_config(100009)["language"] == "en"
