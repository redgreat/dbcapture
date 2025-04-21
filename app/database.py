from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建结果数据库引擎
engine = create_engine(
    settings.DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
