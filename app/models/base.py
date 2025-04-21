from datetime import datetime
from typing import Any
import pytz

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime, Integer, Boolean


def get_now_in_east8():
    return datetime.now(pytz.timezone("Asia/Shanghai"))


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, comment="自增主键"
    )
    created_at = Column(
        DateTime, default=get_now_in_east8, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=get_now_in_east8,
        onupdate=get_now_in_east8,
        nullable=False,
        comment="更新时间",
    )
    deleted_at = Column(
        DateTime, default=get_now_in_east8, nullable=False, comment="删除时间"
    )
    deleted = Column(Boolean, default=False, nullable=False, comment="是否删除")
