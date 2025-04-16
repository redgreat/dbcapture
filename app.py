from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, DbConnection, Comparison
from app.schemas import UserCreate, UserResponse, DbConnectionCreate, DbConnectionResponse, ComparisonCreate, ComparisonResponse
from app.auth import get_current_user, create_access_token, verify_password, get_password_hash
from app.database import get_db
from app.routers import auth, db_connections, comparisons
import os

app = FastAPI(title="数据库结构对比系统")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(db_connections.router, prefix="/api/v1/db-connections", tags=["db-connections"])
app.include_router(comparisons.router, prefix="/api/v1/comparisons", tags=["comparisons"])

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 