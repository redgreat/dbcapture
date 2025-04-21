import json
import requests
from typing import Dict, Any

from app.core.config import settings
from app.models.tasks import TaskLog, TaskStatus, Result


def _calculate_diff_stats(results: list[Result]) -> dict:
    total = len(results)
    diff = sum(1 for r in results if getattr(r, "has_differences", False))
    no_diff = total - diff
    return {"total": total, "diff": diff, "no_diff": no_diff}


def _build_comparison_message(task_log: TaskLog) -> Dict[str, Any]:
    """构建企业微信消息"""
    status_emoji = {
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.PENDING: "⏳",
    }
    task = task_log.task
    results = task_log.results if hasattr(task_log, "results") else []
    diff_stats = _calculate_diff_stats(results)
    content = f"""数据库对比任务 {status_emoji.get(task_log.status, '❓')}
\n源数据库: {task.source_conn.host}:{task.source_conn.port}/{task.source_conn.database}
目标数据库: {task.target_conn.host}:{task.target_conn.port}/{task.target_conn.database}
\n总对象数: {diff_stats['total']}
有差异: {diff_stats['diff']}
无差异: {diff_stats['no_diff']}
\n任务状态: {task_log.status.value}
开始时间: {getattr(task_log, 'created_at', '')}\n"""
    if getattr(task_log, "error_message", None):
        content += f"\n错误信息: {task_log.error_message}\n"
    return {"msgtype": "markdown", "markdown": {"content": content}}


class WeChatNotificationService:
    def __init__(self):
        self.webhook_key = settings.WECHAT_WEBHOOK_KEY
        self.enabled = settings.WECHAT_ALERT_ENABLED

    def send_comparison_result(self, task_log: TaskLog) -> bool:
        """发送数据库比较结果到企业微信机器人"""
        if not self.enabled or not self.webhook_key:
            return False

        webhook_url = (
            f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.webhook_key}"
        )

        message = _build_comparison_message(task_log)

        try:
            response = requests.post(
                webhook_url, json=message, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send WeChat notification: {str(e)}")
            return False
