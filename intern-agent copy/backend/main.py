import json
import uuid
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import init_db, get_db, DailyLog
from schemas import DailyLogCreate, DailyLogResponse, LogUpdate
from agent import generate_summary, suggest_tags, recognize_image

app = FastAPI(title="Intern Learning Agent API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """启动时初始化数据库"""
    init_db()


@app.get("/")
def root():
    return {"message": "Intern Learning Agent API", "status": "running"}


@app.post("/logs", response_model=DailyLogResponse)
def create_log(log_data: DailyLogCreate, db: Session = Depends(get_db)):
    """创建每日学习记录"""
    log_id = str(uuid.uuid4())

    # 使用Agent生成摘要和标签
    log_dict = log_data.model_dump()
    ai_summary = generate_summary(log_dict)
    ai_tags = suggest_tags(log_dict)

    # 合并手动标签和AI推荐标签
    all_tags = list(set(log_data.tags + ai_tags)) if log_data.tags else ai_tags

    # 使用用户选择的日期，如果未提供则使用当前日期
    log_date = datetime.strptime(log_data.date, "%Y-%m-%d") if log_data.date else datetime.now()

    db_log = DailyLog(
        id=log_id,
        date=log_date,
        tasks=json.dumps([t.model_dump() for t in log_data.tasks]),
        learnings=json.dumps([l.model_dump() for l in log_data.learnings]),
        attachments=json.dumps(log_data.attachments),
        tags=json.dumps(all_tags),
        ai_summary=ai_summary
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return _parse_log_response(db_log)


@app.get("/logs", response_model=list[DailyLogResponse])
def get_logs(skip: int = 0, limit: int = 30, db: Session = Depends(get_db)):
    """获取学习记录列表"""
    logs = db.query(DailyLog).order_by(DailyLog.date.desc()).offset(skip).limit(limit).all()
    return [_parse_log_response(log) for log in logs]


@app.get("/logs/{log_id}", response_model=DailyLogResponse)
def get_log(log_id: str, db: Session = Depends(get_db)):
    """获取单条学习记录"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, message="Log not found")
    return _parse_log_response(log)


@app.put("/logs/{log_id}", response_model=DailyLogResponse)
def update_log(log_id: str, update_data: LogUpdate, db: Session = Depends(get_db)):
    """更新学习记录"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, message="Log not found")

    if update_data.tasks is not None:
        log.tasks = json.dumps([t.model_dump() for t in update_data.tasks])
    if update_data.learnings is not None:
        log.learnings = json.dumps([l.model_dump() for l in update_data.learnings])
    if update_data.attachments is not None:
        log.attachments = json.dumps(update_data.attachments)
    if update_data.tags is not None:
        log.tags = json.dumps(update_data.tags)
    if update_data.ai_summary is not None:
        log.ai_summary = update_data.ai_summary

    log.updated_at = datetime.now()
    db.commit()
    db.refresh(log)

    return _parse_log_response(log)


@app.delete("/logs/{log_id}")
def delete_log(log_id: str, db: Session = Depends(get_db)):
    """删除学习记录"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, message="Log not found")

    db.delete(log)
    db.commit()
    return {"message": "Log deleted successfully"}


@app.get("/logs/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """获取统计摘要"""
    total_logs = db.query(DailyLog).count()

    # 统计标签
    all_logs = db.query(DailyLog).all()
    tag_count = {}
    for log in all_logs:
        tags = json.loads(log.tags or "[]")
        for tag in tags:
            tag_count[tag] = tag_count.get(tag, 0) + 1

    return {
        "total_logs": total_logs,
        "tag_distribution": tag_count
    }


class ImageRecognizeRequest(BaseModel):
    image_base64: str


@app.post("/recognize-image")
def recognize_image_endpoint(data: ImageRecognizeRequest):
    """使用GLM-4V Agent智能分析图片内容"""
    try:
        text = recognize_image(data.image_base64)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片识别失败: {str(e)}")


def _parse_log_response(log: DailyLog) -> DailyLogResponse:
    """解析数据库记录为响应模型"""
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
    uvicorn.run(app, host="0.0.0.0", port=8000)