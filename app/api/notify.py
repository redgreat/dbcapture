from fastapi import APIRouter, Depends, HTTPException
from app.models.tasks import Task
from app.services.wechat_service import WeChatNotificationService
from app.main import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/tasks/{comparison_id}/notify")
def send_comparison_notification(comparison_id: int, db: Session = Depends(get_db)):
    """手动发送比较结果通知"""
    comparison = db.query(Task).get(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    wechat_service = WeChatNotificationService()
    success = wechat_service.send_comparison_result(comparison)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")

    return {"message": "Notification sent"}
