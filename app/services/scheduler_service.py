from typing import Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.comparison import Comparison
from app.services.comparison_service import DatabaseComparisonService
from app.services.report_service import ReportService
from app.services.wechat_service import WeChatNotificationService


class SchedulerService:
    def __init__(self, db: Session):
        self.scheduler = BackgroundScheduler()
        self.db = db
        self.comparison_service = DatabaseComparisonService(db)
        self.report_service = ReportService()
        self.wechat_service = WeChatNotificationService()

    def start(self):
        """启动调度器"""
        if settings.SCHEDULER_ENABLED:
            self.scheduler.start()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def add_comparison_job(
        self,
        source_host: str,
        source_port: str,
        source_database: str,
        target_host: str,
        target_port: str,
        target_database: str,
        cron_expression: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> str:
        """添加定时比较任务"""
        if not cron_expression:
            cron_expression = settings.DEFAULT_COMPARISON_CRON

        if not job_id:
            job_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务函数
        def comparison_job():
            comparison = Comparison(
                source_host=source_host,
                source_port=source_port,
                source_database=source_database,
                target_host=target_host,
                target_port=target_port,
                target_database=target_database
            )
            self.db.add(comparison)
            self.db.commit()

            try:
                # 执行比较
                self.comparison_service.run_comparison(comparison.id)
                
                # 生成报告
                reports = self.report_service.generate_reports(comparison)
                self.db.add_all(reports)
                self.db.commit()
                
                # 发送通知
                self.wechat_service.send_comparison_result(comparison)
                
            except Exception as e:
                print(f"Scheduled comparison job failed: {str(e)}")

        # 添加任务
        self.scheduler.add_job(
            comparison_job,
            CronTrigger.from_crontab(cron_expression),
            id=job_id,
            replace_existing=True
        )

        return job_id

    def remove_comparison_job(self, job_id: str) -> bool:
        """移除定时比较任务"""
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def get_all_jobs(self):
        """获取所有定时任务"""
        return self.scheduler.get_jobs()

    def modify_job_schedule(self, job_id: str, cron_expression: str) -> bool:
        """修改任务调度时间"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.reschedule(CronTrigger.from_crontab(cron_expression))
                return True
            return False
        except Exception:
            return False 