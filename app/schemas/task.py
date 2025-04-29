from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.models.tasks import TaskStatus, ResultType
from app.schemas.connection import ConnectionOut


class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_conn_id: int
    source_conn_name: str
    target_conn_id: int
    target_conn_name: str
    config: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_conn_id: int
    target_conn_id: int
    config: Optional[Dict[str, Any]] = None


class ResultBase(BaseModel):
    object_name: str
    has_differences: bool
    source_definition: Optional[str] = None
    target_definition: Optional[str] = None
    difference_details: Optional[Dict[str, Any]] = None
    change_sql: Optional[str] = None
    file_path: Optional[str] = None
    cost_time: Optional[float] = None


class TaskResult(ResultBase):
    id: int
    task_log_id: int
    type: ResultType
    create_at: datetime
    update_at: datetime
    delete_at: Optional[datetime] = None
    deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class Task(TaskBase):
    id: int
    status: TaskStatus
    source_conn: ConnectionOut
    target_conn: ConnectionOut
    results: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    deleted: bool = False

    model_config = ConfigDict(from_attributes=True)
