from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.models.tasks import Task
from app.main import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/tasks/{task_id}/reports")
def get_comparison_reports(
    task_id: int, format: Optional[str] = None, db: Session = Depends(get_db)
):
    """获取比较报告"""
    comparison = db.query(Task).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    reports = comparison.reports
    if format:
        reports = [r for r in reports if r.format == format]

    return reports
