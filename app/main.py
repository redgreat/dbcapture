from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta, datetime
import os

from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
)
from app.models.tasks import Task, Result, TaskLog, TaskStatus
from app.models.connections import Connection
from app.models.users import User
from app.services.task_service import DatabaseComparisonService
from app.services.report_service import ReportService
from app.services.wechat_service import WeChatNotificationService
from app.database import engine, SessionLocal
from app.schemas import task as schemas
from app.schemas import connection as db_schemas
from app.schemas import user as user_schemas


# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 创建数据库表
User.metadata.create_all(bind=engine)
Connection.metadata.create_all(bind=engine)
Task.metadata.create_all(bind=engine)

# 初始化admin用户


app = FastAPI(
    title=settings.APP_NAME,
    description="数据库结构对比工具API",
    version="1.0.0",
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# 注册路由（如有重复导入可去重）
from app.routers import auth, connections, comparisons

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    connections.router, prefix="/api/v1/db-connections", tags=["db-connections"]
)
app.include_router(
    comparisons.router, prefix="/api/v1/comparisons", tags=["comparisons"]
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 认证相关路由
@app.post("/api/v1/token", response_model=user_schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/v1/users", response_model=user_schemas.User)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, password_hash=hashed_password, is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 数据库连接管理API
@app.get("/api/v1/db-connections", response_model=List[db_schemas.DbConnectionOut])
def list_db_connections(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """获取所有数据库连接"""
    return db.query(DbConnection).all()


@app.post("/api/v1/db-connections", response_model=db_schemas.DbConnectionOut)
def create_db_connection(
    conn: db_schemas.DbConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """新增数据库连接"""
    db_conn = DbConnection(**conn.dict())
    db.add(db_conn)
    db.commit()
    db.refresh(db_conn)
    return db_conn


@app.put("/api/v1/db-connections/{conn_id}", response_model=db_schemas.DbConnectionOut)
def update_db_connection(
    conn_id: int,
    conn: db_schemas.DbConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新数据库连接"""
    db_conn = db.query(DbConnection).get(conn_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="DbConnection not found")
    for field, value in conn.dict(exclude_unset=True).items():
        setattr(db_conn, field, value)
    db.commit()
    db.refresh(db_conn)
    return db_conn


@app.delete("/api/v1/db-connections/{conn_id}")
def delete_db_connection(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除数据库连接"""
    db_conn = db.query(DbConnection).get(conn_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="DbConnection not found")
    db.delete(db_conn)
    db.commit()
    return {"message": "DbConnection deleted"}


# 比较任务管理API
@app.get("/api/v1/tasks", response_model=List[schemas.Task])
def list_tasks(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    return db.query(Task).all()


@app.post("/api/v1/tasks", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


# 初始化调度器
scheduler = None


@app.on_event("startup")
async def startup_event():
    global scheduler
    try:
        db = SessionLocal()
        scheduler = SchedulerService(db)
        scheduler.start()
    except Exception as e:
        import traceback

        print("Startup failed:", e)
        print(traceback.format_exc())
        raise


@app.on_event("shutdown")
async def shutdown_event():
    if scheduler:
        scheduler.stop()


@app.post("/api/v1/scheduled-tasks", response_model=schemas.ScheduledTaskInDB)
def create_scheduled_task(
    schedule: schemas.ScheduledTaskCreate, db: Session = Depends(get_db)
):
    scheduler = SchedulerService()
    job = scheduler.add_job(schedule)
    return job


@app.delete("/api/v1/scheduled-tasks/{job_id}")
def delete_scheduled_task(job_id: str):
    scheduler = SchedulerService()
    scheduler.remove_job(job_id)
    return {"message": "定时任务已删除"}


@app.get("/api/v1/scheduled-tasks", response_model=List[schemas.ScheduledTaskInDB])
def list_scheduled_tasks():
    scheduler = SchedulerService()
    return scheduler.get_jobs()


@app.get("/api/v1/comparisons/{comparison_id}/reports")
def get_comparison_reports(
    comparison_id: int, format: Optional[str] = None, db: Session = Depends(get_db)
):
    """获取比较报告"""
    comparison = db.query(Task).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    reports = comparison.reports
    if format:
        reports = [r for r in reports if r.format == format]

    return reports


@app.post("/api/v1/comparisons/{comparison_id}/notify")
def send_comparison_notification(comparison_id: int, db: Session = Depends(get_db)):
    """手动发送比较结果通知"""
    comparison = db.query(Task).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    wechat_service = WeChatNotificationService()
    success = wechat_service.send_comparison_result(comparison)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")

    return {"message": "Notification sent"}


# 保证直接运行 main.py 时可以启动
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
