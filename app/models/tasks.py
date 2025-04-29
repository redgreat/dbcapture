from sqlalchemy import (
    String,
    JSON,
    Text,
    Boolean,
    ForeignKey,
    Enum,
    Integer,
    BigInteger,
    Float,
)
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultType(enum.Enum):
    CONFIG = "config"
    TABLE = "table"
    VIEW = "view"
    PROCEDURE = "procedure"
    FUNCTION = "function"
    TRIGGER = "trigger"


class Task(Base):
    """数据库比较任务主表"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
        comment="自增主键"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="任务名称"
    )
    description: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="任务描述"
    )
    source_conn_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        ForeignKey("connections.id"),
        nullable=False,
        comment="源数据库连接ID",
    )
    source_conn_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=False,
        comment="源数据库连接名称",
    )
    target_conn_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        ForeignKey("connections.id"),
        nullable=False,
        comment="目标数据库连接ID",
    )
    target_conn_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=False,
        comment="目标数据库连接名称",
    )
    config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="比较配置（忽略项等）",
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING,
        comment="任务状态"
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


class TaskLog(Base):
    """数据库任务执行日志表"""

    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
        comment="自增主键"
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
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
    result_url: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="报告文件路径"
    )
    cost_time: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="执行耗时（秒）"
    )

    # 关系定义
    task = relationship(
        "app.models.tasks.Task",
        foreign_keys=[task_id],
        primaryjoin="TaskLog.task_id==Task.id",
        uselist=False,
    )
    results = relationship(
        "app.models.tasks.Result",
        back_populates="task_log",
        cascade="all, delete-orphan"
    )


class Result(Base):
    """比较结果详情表"""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        primary_key=True,
        autoincrement=True,
        comment="自增主键"
    )
    task_log_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(MYSQL_BIGINT(unsigned=True), "mysql"),
        ForeignKey("task_logs.id"),
        nullable=False,
        comment="任务执行日志表Id",
    )
    type: Mapped[ResultType] = mapped_column(
        Enum(ResultType), nullable=False, comment="结果类型"
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

    # 关系定义
    task_log = relationship(
        "app.models.tasks.TaskLog",
        foreign_keys=[task_log_id],
        primaryjoin="Result.task_log_id==TaskLog.id",
        back_populates="results",
        uselist=False,
    )