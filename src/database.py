"""数据库模型模块"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import config


class Database:
    """数据库管理"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "data.db"
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self):
        """创建表"""
        cursor = self.conn.cursor()

        # 群组配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_config (
                chat_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'zh',
                daily_time TEXT,
                weekly_day INTEGER,
                weekly_time TEXT,
                enable_image INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 总结历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summary_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                summary_type TEXT NOT NULL,
                message_count INTEGER,
                user_count INTEGER,
                sentiment TEXT,
                summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_config(chat_id)
            )
        ''')

        # 定时任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                job_type TEXT NOT NULL,
                job_config TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_config(chat_id)
            )
        ''')

        self.conn.commit()

    def get_chat_config(self, chat_id: int) -> Optional[dict]:
        """获取群组配置"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM chat_config WHERE chat_id = ?',
            (chat_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def upsert_chat_config(self, chat_id: int, **kwargs):
        """更新或插入群组配置"""
        cursor = self.conn.cursor()

        # 检查是否存在
        existing = self.get_chat_config(chat_id)

        if existing:
            # 更新
            set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
            values = list(kwargs.values()) + [chat_id]
            cursor.execute(
                f'UPDATE chat_config SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?',
                values
            )
        else:
            # 插入
            kwargs['chat_id'] = chat_id
            columns = ', '.join(kwargs.keys())
            placeholders = ', '.join(['?'] * len(kwargs))
            cursor.execute(
                f'INSERT INTO chat_config ({columns}) VALUES ({placeholders})',
                list(kwargs.values())
            )

        self.conn.commit()

    def add_summary_history(
        self,
        chat_id: int,
        summary_type: str,
        message_count: int,
        user_count: int,
        sentiment: str,
        summary: str
    ):
        """添加总结历史"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO summary_history
            (chat_id, summary_type, message_count, user_count, sentiment, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chat_id, summary_type, message_count, user_count, sentiment, summary))
        self.conn.commit()

    def get_summary_history(
        self,
        chat_id: int,
        limit: int = 10
    ) -> list[dict]:
        """获取总结历史"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM summary_history
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (chat_id, limit))
        return [dict(row) for row in cursor.fetchall()]

    def add_scheduled_job(
        self,
        chat_id: int,
        job_type: str,
        job_config: str
    ):
        """添加定时任务"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO scheduled_jobs (chat_id, job_type, job_config)
            VALUES (?, ?, ?)
        ''', (chat_id, job_type, job_config))
        self.conn.commit()

    def get_scheduled_jobs(self, chat_id: int = None) -> list[dict]:
        """获取定时任务"""
        cursor = self.conn.cursor()
        if chat_id:
            cursor.execute(
                'SELECT * FROM scheduled_jobs WHERE chat_id = ? AND is_active = 1',
                (chat_id,)
            )
        else:
            cursor.execute(
                'SELECT * FROM scheduled_jobs WHERE is_active = 1'
            )
        return [dict(row) for row in cursor.fetchall()]

    def deactivate_scheduled_job(self, job_id: int):
        """停用定时任务"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE scheduled_jobs SET is_active = 0 WHERE id = ?',
            (job_id,)
        )
        self.conn.commit()


# 全局数据库实例
db = Database()
