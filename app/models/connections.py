from sqlalchemy import String, Text, Integer, BigInteger
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from app.core.encrypt_util import encrypt_password, decrypt_password


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
        comment="自增主键"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="连接名称"
    )
    host: Mapped[str] = mapped_column(String(200), nullable=False, comment="主机地址")
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="端口")
    user: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名")
    password_encrypted: Mapped[str] = mapped_column(String(200), nullable=False, comment="加密密码")
    database: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="数据库名"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")

    @property
    def password(self) -> str:
        """
        获取解密后的密码
        """
        return decrypt_password(self.password_encrypted)

    @password.setter
    def password(self, value: str) -> None:
        """
        设置加密后的密码
        """
        self.password_encrypted = encrypt_password(value)
