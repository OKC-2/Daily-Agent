"""
数据库模块

提供数据库连接、会话管理和模型定义
"""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, pool, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/intern_agent"
)

# 连接池配置
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1小时回收连接
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

# 创建引擎（带连接池）
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境关闭 SQL 日志
    poolclass=pool.QueuePool,
    pool_size=POOL_SIZE,
    pool_recycle=POOL_RECYCLE,
    pool_timeout=POOL_TIMEOUT,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接前检查可用性
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 模型基类
Base = declarative_base()


class DailyLog(Base):
    """每日学习记录模型"""
    __tablename__ = "daily_logs"

    id = Column(String(36), primary_key=True)
    date = Column(DateTime, default=datetime.now, index=True)  # 添加索引
    tasks = Column(Text, comment="任务列表（JSON）")
    learnings = Column(Text, comment="学习内容（JSON）")
    attachments = Column(Text, comment="附件列表（JSON）")
    tags = Column(Text, comment="标签列表（JSON）")
    ai_summary = Column(Text, nullable=True, comment="AI 生成的摘要")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<DailyLog(id={self.id}, date={self.date})>"


class Tag(Base):
    """标签模型"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True, comment="标签名称")
    category = Column(String(50), comment="标签分类：tech/business/tool/soft_skill")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


def init_db():
    """
    初始化数据库表
    
    创建所有定义的表结构
    """
    try:
        logger.info("开始初始化数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_db():
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话实例
        
    使用示例:
        with get_db() as db:
            db.query(DailyLog).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库操作异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_connection():
    """
    测试数据库连接
    
    Returns:
        bool: 连接成功返回 True，否则返回 False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("数据库连接测试成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False


if __name__ == "__main__":
    # 测试数据库连接
    test_connection()
