from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Connection(Base):
    __tablename__ = "connections"

    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="连接名称"
    )
    host: Mapped[str] = mapped_column(String(200), nullable=False, comment="主机地址")
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="端口")
    user: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(50), nullable=False, comment="密码")
    database: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="数据库名"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
