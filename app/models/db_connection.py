from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base

class DbConnection(Base):
    __tablename__ = 'db_connection'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment='连接名称')
    host: Mapped[str] = mapped_column(String(128), nullable=False, comment='主机地址')
    port: Mapped[str] = mapped_column(String(16), nullable=False, comment='端口')
    user: Mapped[str] = mapped_column(String(64), nullable=False, comment='用户名')
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment='密码')
    database: Mapped[str] = mapped_column(String(64), nullable=False, comment='数据库名')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='描述')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
