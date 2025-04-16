import json
import requests
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.comparison import Comparison, ComparisonStatus


class WeChatNotificationService:
    def __init__(self):
        self.webhook_key = settings.WECHAT_WEBHOOK_KEY
        self.enabled = settings.WECHAT_ALERT_ENABLED

    def send_comparison_result(self, comparison: Comparison) -> bool:
        """发送数据库比较结果到企业微信机器人"""
        if not self.enabled or not self.webhook_key:
            return False

        webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.webhook_key}"
        
        # 构建消息内容
        message = self._build_comparison_message(comparison)
        
        try:
            response = requests.post(
                webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send WeChat notification: {str(e)}")
            return False

    def _build_comparison_message(self, comparison: Comparison) -> Dict[str, Any]:
        """构建企业微信消息"""
        status_emoji = {
            ComparisonStatus.COMPLETED: "✅",
            ComparisonStatus.FAILED: "❌",
            ComparisonStatus.RUNNING: "🔄",
            ComparisonStatus.PENDING: "⏳"
        }

        # 计算差异统计
        diff_stats = self._calculate_diff_stats(comparison)
        
        content = f"""数据库对比任务 {status_emoji.get(comparison.status, '❓')}

源数据库: {comparison.source_host}:{comparison.source_port}/{comparison.source_database}
目标数据库: {comparison.target_host}:{comparison.target_port}/{comparison.target_database}

状态: {comparison.status.value}
{f'错误信息: {comparison.error_message}' if comparison.error_message else ''}

差异统计:
- 配置差异: {diff_stats['config']}
- 表结构差异: {diff_stats['table']}
- 视图差异: {diff_stats['view']}
- 存储过程差异: {diff_stats['procedure']}
- 函数差异: {diff_stats['function']}
- 触发器差异: {diff_stats['trigger']}

详细报告请查看系统。"""

        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

    def _calculate_diff_stats(self, comparison: Comparison) -> Dict[str, int]:
        """计算各类型的差异数量"""
        stats = {
            "config": 0,
            "table": 0,
            "view": 0,
            "procedure": 0,
            "function": 0,
            "trigger": 0
        }
        
        for result in comparison.results:
            if result.has_differences:
                stats[result.type.value] += 1
                
        return stats 