from fastapi import APIRouter
from app.api import auth, connection, task, result, notify

api_router = APIRouter(prefix="/api/v1", tags=["api"])

api_router.include_router(auth.router, prefix="", tags=["auth"])
api_router.include_router(connection.router, prefix="", tags=["connection"])
api_router.include_router(task.router, prefix="", tags=["task"])
api_router.include_router(result.router, tags=["result"])
api_router.include_router(notify.router, tags=["notify"])
