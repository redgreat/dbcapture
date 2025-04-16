from sqlalchemy import String, JSON, Text, Boolean, ForeignKey, Enum, Integer, DateTime, Column
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum

from .base import Base
from .db_connection import DbConnection


class ComparisonStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ComparisonType(enum.Enum):
    CONFIG = "config"
    TABLE = "table"
    VIEW = "view"
    PROCEDURE = "procedure"
    FUNCTION = "function"
    TRIGGER = "trigger"


class Comparison(Base):
    """数据库比较任务主表"""
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_conn_id: Mapped[int] = mapped_column(Integer, ForeignKey("db_connection.id"), nullable=False, comment='源数据库连接ID')
    target_conn_id: Mapped[int] = mapped_column(Integer, ForeignKey("db_connection.id"), nullable=False, comment='目标数据库连接ID')
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 比较配置（忽略项等）
    status: Mapped[ComparisonStatus] = mapped_column(Enum(ComparisonStatus), default=ComparisonStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系定义
    source_conn = relationship("app.models.db_connection.DbConnection", foreign_keys=[source_conn_id])
    target_conn = relationship("app.models.db_connection.DbConnection", foreign_keys=[target_conn_id])
    results: Mapped[list["ComparisonResult"]] = relationship("ComparisonResult", back_populates="comparison")
    reports: Mapped[list["ComparisonReport"]] = relationship("ComparisonReport", back_populates="comparison")


class ComparisonResult(Base):
    """比较结果详情表"""
    __tablename__ = "comparison_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(Integer, ForeignKey("comparisons.id"), nullable=False)
    type: Mapped[ComparisonType] = mapped_column(Enum(ComparisonType), nullable=False)
    object_name: Mapped[str] = mapped_column(String(255), nullable=False)  # 对象名称（表名、视图名等）
    has_differences: Mapped[bool] = mapped_column(Boolean, default=False)
    source_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    difference_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    change_sql: Mapped[str | None] = mapped_column(Text, nullable=True)

    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="results")


class ComparisonReport(Base):
    """比较报告表"""
    __tablename__ = "comparison_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(Integer, ForeignKey("comparisons.id"), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # 'html' or 'pdf'
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)

    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="reports")