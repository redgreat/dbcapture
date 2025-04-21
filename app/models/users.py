from sqlalchemy import String, BigInteger
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
        comment="自增主键"
    )
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="密码哈希"
    )
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
