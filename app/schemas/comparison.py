from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.comparison import ComparisonStatus, ComparisonType
from app.schemas.db_connection import DbConnectionOut


class ComparisonBase(BaseModel):
    source_conn_id: int
    target_conn_id: int
    config: Optional[Dict[str, Any]] = None


class ComparisonCreate(ComparisonBase):
    pass


class ComparisonResultBase(BaseModel):
    type: ComparisonType
    object_name: str
    has_differences: bool
    source_definition: Optional[str] = None
    target_definition: Optional[str] = None
    difference_details: Optional[Dict[str, Any]] = None
    change_sql: Optional[str] = None


class ComparisonResult(ComparisonResultBase):
    id: int
    comparison_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComparisonReportBase(BaseModel):
    format: str
    file_path: str


class ComparisonReport(ComparisonReportBase):
    id: int
    comparison_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Comparison(ComparisonBase):
    id: int
    status: ComparisonStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    results: List[ComparisonResult] = []
    reports: List[ComparisonReport] = []
    source_conn: DbConnectionOut
    target_conn: DbConnectionOut

    model_config = ConfigDict(from_attributes=True)


class ScheduledComparisonCreate(ComparisonBase):
    cron_expression: Optional[str] = Field(
        default=None,
        description="Cron表达式，例如：'0 0 * * *' 表示每天凌晨执行"
    )


class ScheduledComparison(BaseModel):
    job_id: str
    next_run_time: Optional[datetime]
    comparison: ComparisonBase

    model_config = ConfigDict(from_attributes=True) 