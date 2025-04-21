import os
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.models.tasks import Result, TaskLog


class ReportService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "../templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.output_dir = settings.REPORT_OUTPUT_DIR

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_reports(self, task_log: TaskLog) -> List[Dict[str, Any]]:
        """生成比较报告"""
        reports = []

        if settings.HTML_ENABLED:
            html_report = self.generate_html_report(task_log)
            reports.append(html_report)

        return reports

    def generate_html_report(self, task_log: TaskLog) -> Dict[str, Any]:
        """生成HTML报告"""
        template = self.env.get_template("report.html")

        # 准备报告数据
        report_data = self._prepare_report_data(task_log)

        # 生成HTML内容
        html_content = template.render(**report_data)

        # 保存HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_report_{task_log.id}_{timestamp}.html"
        file_path = os.path.join(self.output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 创建报告记录
        return {
            "task_log_id": task_log.id,
            "format": "html",
            "file_path": file_path,
        }

    def _prepare_report_data(self, task_log: TaskLog) -> Dict[str, Any]:
        """准备报告数据"""
        task = task_log.task
        results = self._get_results(task_log)

        # 获取数据库连接信息
        source_conn = task.source_conn
        target_conn = task.target_conn

        return {
            "task": {
                "id": task.id,
                "source_database": f"{source_conn.host}:{source_conn.port}/{source_conn.database}",
                "target_database": f"{target_conn.host}:{target_conn.port}/{target_conn.database}",
                "status": task_log.status.value,
                "created_at": task_log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "error_message": task_log.error_message,
            },
            "results": self._group_results_by_type(results),
            "summary": self._generate_summary(results),
        }

    def _get_results(self, task_log: TaskLog) -> List[Result]:
        # 获取该日志下所有比对结果
        return task_log.results if hasattr(task_log, "results") else []

    def _group_results_by_type(
        self, results: List[Result]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按类型分组比较结果"""
        grouped_results = {
            "config": [],
            "table": [],
            "view": [],
            "procedure": [],
            "function": [],
            "trigger": [],
        }

        for result in results:
            result_dict = {
                "object_name": result.object_name,
                "has_differences": result.has_differences,
                "source_definition": result.source_definition,
                "target_definition": result.target_definition,
                "difference_details": result.difference_details,
                "change_sql": result.change_sql,
            }
            grouped_results[result.type.value].append(result_dict)

        return grouped_results

    def _generate_summary(self, results: List[Result]) -> Dict[str, int]:
        """生成比较结果摘要"""
        summary = {
            "total_objects": len(results),
            "total_differences": 0,
            "differences_by_type": {
                "config": 0,
                "table": 0,
                "view": 0,
                "procedure": 0,
                "function": 0,
                "trigger": 0,
            },
        }

        for result in results:
            if result.has_differences:
                summary["total_differences"] += 1
                summary["differences_by_type"][result.type.value] += 1

        return summary
