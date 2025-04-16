from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
import os

from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.comparison import Comparison
from app.models.db_connection import DbConnection
from app.models.user import User
from app.services.comparison_service import DatabaseComparisonService
from app.services.scheduler_service import SchedulerService
from app.services.report_service import ReportService
from app.services.wechat_service import WeChatNotificationService
from app.database import engine, SessionLocal
from app.schemas import comparison as schemas
from app.schemas import db_connection as db_schemas
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
DbConnection.metadata.create_all(bind=engine)
Comparison.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="数据库结构对比工具API",
    version="1.0.0",
)

# 获取静态文件目录的绝对路径
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 初始化模板
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 认证相关路由
@app.post("/api/v1/token", response_model=user_schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
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
        username=user.username,
        password_hash=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 数据库连接管理API
@app.get("/api/v1/db-connections", response_model=List[db_schemas.DbConnectionOut])
def list_db_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有数据库连接"""
    return db.query(DbConnection).all()

@app.post("/api/v1/db-connections", response_model=db_schemas.DbConnectionOut)
def create_db_connection(
    conn: db_schemas.DbConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
):
    """删除数据库连接"""
    db_conn = db.query(DbConnection).get(conn_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="DbConnection not found")
    db.delete(db_conn)
    db.commit()
    return {"message": "DbConnection deleted"}

# 比较任务管理API
@app.get("/api/v1/comparisons")
def list_comparisons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有比较任务"""
    import traceback
    try:
        comparisons = db.query(Comparison).all()
        result = []
        for c in comparisons:
            # 跳过无效任务（连接ID为None或找不到连接的任务）
            if not c.source_conn_id or not c.target_conn_id:
                continue
            source_conn = db.query(DbConnection).get(c.source_conn_id)
            target_conn = db.query(DbConnection).get(c.target_conn_id)
            if not source_conn or not target_conn:
                continue
            # 转为 Pydantic schema
            from app.schemas.db_connection import DbConnectionOut
            source_conn_out = DbConnectionOut.model_validate(source_conn)
            target_conn_out = DbConnectionOut.model_validate(target_conn)
            # dict化
            c_dict = c.__dict__.copy()
            c_dict['source_conn'] = source_conn_out
            c_dict['target_conn'] = target_conn_out
            # 移除老字段（如有）
            for k in ['source_host','source_port','source_database','target_host','target_port','target_database']:
                c_dict.pop(k, None)
            # 处理 results/reports
            c_dict['results'] = list(getattr(c, 'results', []))
            c_dict['reports'] = list(getattr(c, 'reports', []))
            result.append(schemas.Comparison.model_validate(c_dict))
        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/api/v1/comparisons", response_model=schemas.Comparison)
def create_comparison(
    comparison: schemas.ComparisonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        comparison_service = DatabaseComparisonService(db)
        db_comparison = comparison_service.create_comparison(comparison)
        return db_comparison
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e) + '\n' + traceback.format_exc())

@app.post("/api/v1/comparisons/{comparison_id}/run")
def run_comparison(
    comparison_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """手动运行比较任务并生成报告"""
    try:
        print(f"====[API: 开始执行比较任务 {comparison_id}]====")
        comparison_service = DatabaseComparisonService(db)
        report_service = ReportService()
        
        # 验证比较任务是否存在
        comparison = db.query(Comparison).get(comparison_id)
        if not comparison:
            print(f"错误：找不到比较任务 {comparison_id}")
            raise HTTPException(status_code=404, detail=f"比较任务 {comparison_id} 不存在")
            
        print(f"找到比较任务，源数据库ID：{comparison.source_conn_id}，目标数据库ID：{comparison.target_conn_id}")
        
        # 执行比较
        comparison_service.run_comparison(comparison_id)
        
        # 生成并保存报告
        print("开始生成报告...")
        reports = report_service.generate_reports(comparison)
        db.add_all(reports)
        db.commit()
        print("报告生成完成")
        
        return {"message": "Comparison executed and report generated."}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"执行比较任务时发生错误：{str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

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

@app.post("/api/v1/scheduled-comparisons")
def create_scheduled_comparison(
    schedule: schemas.ScheduledComparisonCreate,
    db: Session = Depends(get_db)
):
    """创建定时比较任务"""
    job_id = scheduler.add_comparison_job(
        source_host=schedule.source_host,
        source_port=schedule.source_port,
        source_database=schedule.source_database,
        target_host=schedule.target_host,
        target_port=schedule.target_port,
        target_database=schedule.target_database,
        cron_expression=schedule.cron_expression
    )
    return {"job_id": job_id}

@app.delete("/api/v1/scheduled-comparisons/{job_id}")
def delete_scheduled_comparison(job_id: str):
    """删除定时比较任务"""
    success = scheduler.remove_comparison_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled comparison not found")
    return {"message": "Scheduled comparison removed"}

@app.get("/api/v1/scheduled-comparisons")
def list_scheduled_comparisons():
    """列出所有定时比较任务"""
    jobs = scheduler.get_all_jobs()
    return [{"job_id": job.id, "next_run_time": job.next_run_time} for job in jobs]

@app.get("/api/v1/comparisons/{comparison_id}/reports")
def get_comparison_reports(
    comparison_id: int,
    format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取比较报告"""
    comparison = db.query(Comparison).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    reports = comparison.reports
    if format:
        reports = [r for r in reports if r.format == format]
    
    return reports

@app.post("/api/v1/comparisons/{comparison_id}/notify")
def send_comparison_notification(comparison_id: int, db: Session = Depends(get_db)):
    """手动发送比较结果通知"""
    comparison = db.query(Comparison).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    wechat_service = WeChatNotificationService()
    success = wechat_service.send_comparison_result(comparison)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")
    
    return {"message": "Notification sent"} 