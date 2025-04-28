from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskLog
from app.schemas import task as task_schemas
from app.main import get_db
from app.services.task_service import DatabaseComparisonService
from app.models.connections import Connection
from fastapi import Query
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/tasks", response_model=List[task_schemas.Task])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@router.get("/tasks/{task_id}", response_model=task_schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.status

@router.get("/task_logs")
def get_task_logs(
    task_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(TaskLog).filter(TaskLog.task_id == task_id)
    total = query.count()
    logs = (
        query.order_by(TaskLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = [
        {
            'task_id': log.task_id,
            'status': log.status.value if hasattr(log.status, 'value') else str(log.status),
            'error_message': log.error_message,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(log, 'created_at') and log.created_at else '',
            'result_url': log.result_url
        }
        for log in logs
    ]
    return JSONResponse(content={"total": total, "items": result})

@router.post("/tasks", response_model=task_schemas.Task)
def create_task(task_in: task_schemas.TaskCreate, db: Session = Depends(get_db)):
    # 名称唯一性校验
    exists = db.query(Task).filter(Task.name == task_in.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="任务名称已存在，请更换名称")
    # 查找源库和目标库名称
    source_conn = db.query(Connection).get(task_in.source_conn_id)
    target_conn = db.query(Connection).get(task_in.target_conn_id)
    if not source_conn or not target_conn:
        raise HTTPException(status_code=400, detail="源库或目标库不存在")
    # 只保留模型定义的字段
    task_data = {
        'name': task_in.name,
        'description': task_in.description,
        'source_conn_id': task_in.source_conn_id,
        'source_conn_name': source_conn.name,
        'target_conn_id': task_in.target_conn_id,
        'target_conn_name': target_conn.name,
        'config': task_in.config,
        # status等由模型默认
    }
    task = Task(**task_data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/tasks/{task_id}", response_model=task_schemas.Task)
def update_task(task_id: int, task_in: task_schemas.TaskCreate, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # 只允许修改名称、描述、config
    if task_in.name:
        exists = db.query(Task).filter(Task.name == task_in.name, Task.id != task_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="任务名称已存在，请更换名称")
        task.name = task_in.name
    if task_in.description is not None:
        task.description = task_in.description
    if hasattr(task_in, 'config') and task_in.config is not None:
        task.config = task_in.config
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


# 推荐使用异步接口（见 task_execute_async.py）
# 保留原接口，但仅作兼容用途
@router.post("/tasks/{task_id}/execute")
def execute_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """执行数据库对比，生成报告（异步）"""
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # 后台异步执行
    background_tasks.add_task(_run_comparison_and_notify, task_id)
    return {"message": "任务已提交执行，报告生成中。"}

def _run_comparison_and_notify(task_id: int):
    db = next(get_db())
    try:
        comparison_service = DatabaseComparisonService(db)
        comparison_service.run_comparison(task_id)
    finally:
        db.close()
