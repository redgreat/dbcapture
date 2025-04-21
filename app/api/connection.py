from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.core.security import get_current_active_user
from app.models.connections import Connection as DbConnection
from app.schemas import connection as db_schemas
from app.models.users import User
from app.main import get_db

router = APIRouter()

@router.get("/connections", response_model=List[db_schemas.ConnectionOut])
def list_db_connections(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """获取所有数据库连接"""
    return db.query(DbConnection).all()

from sqlalchemy.exc import IntegrityError

@router.post("/connections", response_model=db_schemas.ConnectionOut)
def create_db_connection(
    conn: db_schemas.ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """新增数据库连接"""
    db_conn = DbConnection(**conn.dict())
    db.add(db_conn)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e.orig):
            raise HTTPException(status_code=400, detail="连接名称已存在，请更换名称。")
        raise HTTPException(status_code=400, detail="数据库唯一约束冲突。")
    db.refresh(db_conn)
    return db_conn

@router.put("/connections/{conn_id}", response_model=db_schemas.ConnectionOut)
def update_db_connection(
    conn_id: int,
    conn: db_schemas.ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新数据库连接"""
    db_conn = db.query(DbConnection).get(conn_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="DbConnection not found")
    for field, value in conn.dict(exclude_unset=True).items():
        setattr(db_conn, field, value)
    db.commit()
    db.refresh(db_conn)
    return db_conn

@router.delete("/connections/{conn_id}")
def delete_db_connection(
    conn_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user),
):
    """删除数据库连接"""
    db_conn = db.query(DbConnection).get(conn_id)
    if not db_conn:
        raise HTTPException(status_code=404, detail="DbConnection not found")
    db.delete(db_conn)
    db.commit()
    return {"message": "DbConnection deleted"}
