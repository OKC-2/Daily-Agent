"""
实习学习记录 Agent API

提供学习记录的 CRUD 操作、AI 摘要生成、图片识别等功能
"""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import redis
from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth import verify_api_key
from db import init_db, get_db, DailyLog
from schemas import DailyLogCreate, DailyLogResponse, LogUpdate
from agent import generate_summary, suggest_tags, recognize_image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis 配置（用于限流）
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis 连接成功")
except Exception as e:
    logger.warning(f"Redis 连接失败，限流将使用内存存储: {e}")
    redis_client = None

# 限流配置
limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL if redis_client else "memory://")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")
    yield
    # 关闭时
    logger.info("应用正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="实习学习记录 Agent API",
    description="""
    AI 辅助的每日学习记录工具，提供以下功能：
    
    - 学习记录的增删改查
    - AI 自动生成学习摘要
    - 智能标签推荐
    - 图片内容识别
    
    ## 认证
    所有 API 请求需要在 Header 中携带 API Key：
    ```
    Authorization: Bearer YOUR_API_KEY
    ```
    """,
    version="1.0.0",
    lifespan=lifespan
)

# 添加限流中间件
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置 - 从环境变量读取允许的源
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理"""
    logger.error(f"数据库错误: {str(exc)} - {request.url}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "数据库操作失败", "status_code": 500}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "服务器内部错误", "status_code": 500}
    )


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查端点
    
    检查服务状态和数据库连接
    """
    try:
        # 检查数据库连接
        from db import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


@app.get("/", tags=["系统"])
def root():
    """API 根路径"""
    return {
        "message": "Intern Learning Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# 图像识别请求模型（添加验证）
class ImageRecognizeRequest(BaseModel):
    """图像识别请求"""
    image_base64: str = Field(..., min_length=100, description="Base64 编码的图片数据")
    
    @field_validator('image_base64')
    @classmethod
    def validate_base64(cls, v):
        """验证 base64 数据格式"""
        if not v or len(v) < 100:
            raise ValueError('图片数据无效或过小')
        return v


# API 端点
@app.post("/logs", response_model=DailyLogResponse, tags=["学习记录"])
@limiter.limit("10/minute")
def create_log(
    request: Request,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    创建每日学习记录
    
    - 自动生成 AI 摘要
    - 智能推荐标签
    - 合并用户标签和 AI 标签
    """
    try:
        log_id = str(uuid.uuid4())
        logger.info(f"创建学习记录: {log_id}")

        # 使用 Agent 生成摘要和标签
        log_dict = log_data.model_dump()
        
        try:
            ai_summary = generate_summary(log_dict)
            ai_tags = suggest_tags(log_dict)
        except Exception as e:
            logger.error(f"AI 生成失败: {e}")
            ai_summary = None
            ai_tags = []

        # 合并手动标签和 AI 推荐标签
        all_tags = list(set(log_data.tags + ai_tags)) if log_data.tags else ai_tags

        # 使用用户选择的日期，如果未提供则使用当前日期
        log_date = datetime.strptime(log_data.date, "%Y-%m-%d") if log_data.date else datetime.now()

        db_log = DailyLog(
            id=log_id,
            date=log_date,
            tasks=json.dumps([t.model_dump() for t in log_data.tasks], ensure_ascii=False),
            learnings=json.dumps([l.model_dump() for l in log_data.learnings], ensure_ascii=False),
            attachments=json.dumps(log_data.attachments, ensure_ascii=False),
            tags=json.dumps(all_tags, ensure_ascii=False),
            ai_summary=ai_summary
        )

        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        logger.info(f"学习记录创建成功: {log_id}")
        return _parse_log_response(db_log)
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建学习记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建学习记录失败: {str(e)}"
        )


@app.get("/logs", response_model=List[DailyLogResponse], tags=["学习记录"])
@limiter.limit("30/minute")
def get_logs(
    request: Request,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(30, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    获取学习记录列表
    
    - 支持分页
    - 按日期倒序排列
    """
    try:
        logs = db.query(DailyLog).order_by(DailyLog.date.desc()).offset(skip).limit(limit).all()
        logger.info(f"获取学习记录列表: skip={skip}, limit={limit}, count={len(logs)}")
        return [_parse_log_response(log) for log in logs]
    except Exception as e:
        logger.error(f"获取学习记录列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习记录失败: {str(e)}"
        )


@app.get("/logs/{log_id}", response_model=DailyLogResponse, tags=["学习记录"])
@limiter.limit("30/minute")
def get_log(
    request: Request,
    log_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    获取单条学习记录
    
    - 通过 ID 查询
    """
    try:
        log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
        if not log:
            logger.warning(f"学习记录不存在: {log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习记录不存在"
            )
        logger.info(f"获取学习记录: {log_id}")
        return _parse_log_response(log)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习记录失败: {str(e)}"
        )


@app.put("/logs/{log_id}", response_model=DailyLogResponse, tags=["学习记录"])
@limiter.limit("10/minute")
def update_log(
    request: Request,
    log_id: str,
    update_data: LogUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    更新学习记录
    
    - 部分更新支持
    - 自动更新修改时间
    """
    try:
        log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
        if not log:
            logger.warning(f"学习记录不存在: {log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习记录不存在"
            )

        if update_data.tasks is not None:
            log.tasks = json.dumps([t.model_dump() for t in update_data.tasks], ensure_ascii=False)
        if update_data.learnings is not None:
            log.learnings = json.dumps([l.model_dump() for l in update_data.learnings], ensure_ascii=False)
        if update_data.attachments is not None:
            log.attachments = json.dumps(update_data.attachments, ensure_ascii=False)
        if update_data.tags is not None:
            log.tags = json.dumps(update_data.tags, ensure_ascii=False)
        if update_data.ai_summary is not None:
            log.ai_summary = update_data.ai_summary

        log.updated_at = datetime.now()
        db.commit()
        db.refresh(log)
        
        logger.info(f"更新学习记录: {log_id}")
        return _parse_log_response(log)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新学习记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新学习记录失败: {str(e)}"
        )


@app.delete("/logs/{log_id}", tags=["学习记录"])
@limiter.limit("10/minute")
def delete_log(
    request: Request,
    log_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    删除学习记录
    
    - 不可恢复
    """
    try:
        log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
        if not log:
            logger.warning(f"学习记录不存在: {log_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习记录不存在"
            )

        db.delete(log)
        db.commit()
        
        logger.info(f"删除学习记录: {log_id}")
        return {"message": "学习记录已删除", "id": log_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除学习记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除学习记录失败: {str(e)}"
        )


@app.get("/logs/stats/summary", tags=["统计"])
@limiter.limit("10/minute")
def get_stats_summary(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    获取统计摘要
    
    - 总记录数
    - 标签分布
    """
    try:
        total_logs = db.query(DailyLog).count()

        # 统计标签
        all_logs = db.query(DailyLog).all()
        tag_count = {}
        for log in all_logs:
            tags = json.loads(log.tags or "[]")
            for tag in tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1

        logger.info(f"获取统计摘要: total_logs={total_logs}")
        return {
            "total_logs": total_logs,
            "tag_distribution": tag_count
        }
    except Exception as e:
        logger.error(f"获取统计摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计摘要失败: {str(e)}"
        )


@app.post("/recognize-image", tags=["AI 功能"])
@limiter.limit("5/minute")
def recognize_image_endpoint(
    request: Request,
    data: ImageRecognizeRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    使用 GLM-4V 智能分析图片内容
    
    - 支持 base64 编码的图片
    - 返回图片内容的文字描述
    """
    try:
        logger.info("开始图片识别")
        text = recognize_image(data.image_base64)
        logger.info("图片识别成功")
        return {"text": text}
    except Exception as e:
        logger.error(f"图片识别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片识别失败: {str(e)}"
        )


def _parse_log_response(log: DailyLog) -> DailyLogResponse:
    """
    解析数据库记录为响应模型
    
    Args:
        log: 数据库模型实例
        
    Returns:
        DailyLogResponse: 响应模型
    """
    return DailyLogResponse(
        id=log.id,
        date=log.date,
        tasks=json.loads(log.tasks) if log.tasks else [],
        learnings=json.loads(log.learnings) if log.learnings else [],
        attachments=json.loads(log.attachments) if log.attachments else [],
        tags=json.loads(log.tags) if log.tags else [],
        ai_summary=log.ai_summary
    )


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
