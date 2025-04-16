import os
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.models.comparison import Comparison, ComparisonResult, ComparisonReport


class ReportService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "../templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.output_dir = settings.REPORT_OUTPUT_DIR
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_reports(self, comparison: Comparison) -> List[ComparisonReport]:
        """生成比较报告"""
        reports = []
        
        if settings.HTML_ENABLED:
            html_report = self.generate_html_report(comparison)
            reports.append(html_report)
            
        return reports

    def generate_html_report(self, comparison: Comparison) -> ComparisonReport:
        """生成HTML报告"""
        template = self.env.get_template("comparison_report.html")
        
        # 准备报告数据
        report_data = self._prepare_report_data(comparison)
        
        # 生成HTML内容
        html_content = template.render(**report_data)
        
        # 保存HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_report_{comparison.id}_{timestamp}.html"
        file_path = os.path.join(self.output_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # 创建报告记录
        report = ComparisonReport(
            comparison_id=comparison.id,
            format="html",
            file_path=file_path
        )
        
        return report

    def _prepare_report_data(self, comparison: Comparison) -> Dict[str, Any]:
        """准备报告数据"""
        # 获取数据库连接信息
        source_conn = comparison.source_conn
        target_conn = comparison.target_conn
        
        return {
            "comparison": {
                "id": comparison.id,
                "source_database": f"{source_conn.host}:{source_conn.port}/{source_conn.database}",
                "target_database": f"{target_conn.host}:{target_conn.port}/{target_conn.database}",
                "status": comparison.status.value,
                "created_at": comparison.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "error_message": comparison.error_message
            },
            "results": self._group_results_by_type(comparison.results),
            "summary": self._generate_summary(comparison.results)
        }

    def _group_results_by_type(self, results: List[ComparisonResult]) -> Dict[str, List[Dict[str, Any]]]:
        """按类型分组比较结果"""
        grouped_results = {
            "config": [],
            "table": [],
            "view": [],
            "procedure": [],
            "function": [],
            "trigger": []
        }
        
        for result in results:
            result_dict = {
                "object_name": result.object_name,
                "has_differences": result.has_differences,
                "source_definition": result.source_definition,
                "target_definition": result.target_definition,
                "difference_details": result.difference_details,
                "change_sql": result.change_sql
            }
            grouped_results[result.type.value].append(result_dict)
            
        return grouped_results

    def _generate_summary(self, results: List[ComparisonResult]) -> Dict[str, int]:
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
                "trigger": 0
            }
        }
        
        for result in results:
            if result.has_differences:
                summary["total_differences"] += 1
                summary["differences_by_type"][result.type.value] += 1
                
        return summary 