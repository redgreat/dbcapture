from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DbConnectionBase(BaseModel):
    name: str = Field(..., description="连接名称")
    host: str = Field(..., description="主机地址")
    port: str = Field(..., description="端口")
    user: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    database: str = Field(..., description="数据库名")
    description: Optional[str] = Field(None, description="描述")

class DbConnectionCreate(DbConnectionBase):
    pass

class DbConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    description: Optional[str] = None

class DbConnectionOut(DbConnectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
