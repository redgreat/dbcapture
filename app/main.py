from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.models.tasks import Task
from app.models.connections import Connection
from app.models.users import User
from app.database import engine, SessionLocal
from app.scripts.create_admin import create_admin_user

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
create_admin_user()

app = FastAPI(
    title=settings.APP_NAME,
    description="数据库结构对比工具API",
    version="1.0.0",
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# 挂载报告文件目录
app.mount("/reports", StaticFiles(directory=settings.REPORT_OUTPUT_DIR), name="reports")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# 注册路由
from app.api.router import api_router

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 保证直接运行 main.py 时可以启动
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
