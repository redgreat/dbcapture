from datetime import datetime
from typing import Any
import pytz

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


def get_now_in_east8():
    return datetime.now(pytz.timezone("Asia/Shanghai"))


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_now_in_east8, nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_now_in_east8, onupdate=get_now_in_east8, nullable=False, comment="更新时间")
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="删除时间")
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否删除")
