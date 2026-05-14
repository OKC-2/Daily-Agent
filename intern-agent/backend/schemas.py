"""
数据模型定义

定义 API 请求和响应的数据结构
"""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Task(BaseModel):
    """任务模型"""
    id: str = Field(..., min_length=1, max_length=100, description="任务 ID")
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    status: str = Field("completed", pattern="^(pending|in_progress|completed)$", description="任务状态")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """验证标题"""
        if not v or not v.strip():
            raise ValueError('任务标题不能为空')
        return v.strip()


class Learning(BaseModel):
    """学习内容模型"""
    id: str = Field(..., min_length=1, max_length=100, description="学习记录 ID")
    content: str = Field(..., min_length=1, max_length=2000, description="学习内容")
    category: str = Field("tech", pattern="^(tech|business|tool|soft_skill)$", description="内容分类")
    keywords: List[str] = Field(default_factory=list, max_length=10, description="关键词列表")
    source: Optional[str] = Field(None, max_length=500, description="学习来源")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """验证内容"""
        if not v or not v.strip():
            raise ValueError('学习内容不能为空')
        return v.strip()

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        """验证关键词"""
        # 过滤空关键词并限制长度
        return [kw.strip() for kw in v if kw and kw.strip()][:10]


class DailyLogCreate(BaseModel):
    """创建学习记录请求"""
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="日期（YYYY-MM-DD）")
    tasks: List[Task] = Field(default_factory=list, max_length=50, description="任务列表")
    learnings: List[Learning] = Field(default_factory=list, max_length=50, description="学习内容列表")
    attachments: List[str] = Field(default_factory=list, max_length=20, description="附件列表")
    tags: List[str] = Field(default_factory=list, max_length=20, description="标签列表")

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """验证日期格式"""
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError('日期格式无效，应为 YYYY-MM-DD')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签"""
        # 过滤空标签并限制长度
        valid_tags = []
        for tag in v:
            if tag and tag.strip():
                tag_clean = tag.strip()
                if len(tag_clean) <= 50:  # 限制单个标签长度
                    valid_tags.append(tag_clean)
        return valid_tags[:20]


class DailyLogResponse(BaseModel):
    """学习记录响应"""
    id: str
    date: datetime
    tasks: List[Task] = []
    learnings: List[Learning] = []
    attachments: List[str] = []
    tags: List[str] = []
    ai_summary: Optional[str] = None

    class Config:
        from_attributes = True


class LogUpdate(BaseModel):
    """更新学习记录请求"""
    tasks: Optional[List[Task]] = Field(None, max_length=50, description="任务列表")
    learnings: Optional[List[Learning]] = Field(None, max_length=50, description="学习内容列表")
    attachments: Optional[List[str]] = Field(None, max_length=20, description="附件列表")
    tags: Optional[List[str]] = Field(None, max_length=20, description="标签列表")
    ai_summary: Optional[str] = Field(None, max_length=2000, description="AI 摘要")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签"""
        if v is not None:
            valid_tags = []
            for tag in v:
                if tag and tag.strip():
                    tag_clean = tag.strip()
                    if len(tag_clean) <= 50:
                        valid_tags.append(tag_clean)
            return valid_tags[:20]
        return v


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    status_code: int
    detail: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    database: Optional[str] = None
    error: Optional[str] = None
