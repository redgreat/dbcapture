from sqlalchemy import (
    String,
    JSON,
    Text,
    Boolean,
    ForeignKey,
    Enum,
    Integer,
    DateTime,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum

from .base import Base
from .connections import Connection


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    """数据库比较任务主表"""

    __tablename__ = "tasks"

    source_conn_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connections.id"),
        nullable=False,
        comment="源数据库连接ID",
    )
    source_conn_name: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("connections.id"),
        nullable=False,
        comment="源数据库连接名称",
    )
    target_conn_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connections.id"),
        nullable=False,
        comment="目标数据库连接ID",
    )
    target_conn_name: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("connections.id"),
        nullable=False,
        comment="目标数据库连接名称",
    )
    config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="比较配置（忽略项等）",
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING
    )

    # 关系定义
    source_conn = relationship(
        "app.models.connections.Connection",
        foreign_keys=[source_conn_id],
        primaryjoin="Task.source_conn_id==Connection.id",
        uselist=False,
    )
    target_conn = relationship(
        "app.models.connections.Connection",
        foreign_keys=[target_conn_id],
        primaryjoin="Task.target_conn_id==Connection.id",
        uselist=False,
    )
    results: Mapped[list["TaskStatus"]] = relationship(
        "TaskStatus", back_populates="task"
    )


class TaskLog(Base):
    """数据库任务执行日志表"""

    __tablename__ = "task_logs"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False,
        comment="任务信息表ID",
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="错误信息"
    )

    # 关系定义
    task = relationship(
        "app.models.tasks.Task",
        foreign_keys=[task_id],
        primaryjoin="TaskLog.task_id==Task.id",
        uselist=False,
    )
    results: Mapped[list["TaskStatus"]] = relationship(
        "TaskStatus", back_populates="task"
    )


class Result(Base):
    """比较结果详情表"""

    __tablename__ = "results"

    task_log_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_logs.id"),
        nullable=False,
        comment="任务执行日志表Id",
    )
    object_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="对象名称（表名、视图名等）",
    )
    has_differences: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否存在差异"
    )
    source_definition: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="源对象定义"
    )
    target_definition: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="目标对象定义"
    )
    difference_details: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="差异详情"
    )
    change_sql: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="变更SQL"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="差异文件路径"
    )

    # 关系定义
    task_log = relationship(
        "app.models.tasks.TaskLog",
        foreign_keys=[task_log_id],
        primaryjoin="Result.task_log_id==TaskLog.id",
        uselist=False,
    )
