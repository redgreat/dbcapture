from typing import Dict, List
import pymysql

from app.models.tasks import Result
from .base_comparator import BaseComparator


def _get_views(conn: pymysql.Connection) -> Dict[str, str]:
    """获取数据库中的所有视图及其创建语句"""
    views = {}
    with conn.cursor() as cursor:
        # 获取所有视图
        cursor.execute(
            """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.VIEWS 
            WHERE TABLE_SCHEMA = DATABASE()
        """
        )
        for (view_name,) in cursor.fetchall():
            # 获取视图的创建语句
            cursor.execute(f"SHOW CREATE VIEW `{view_name}`")
            create_stmt = cursor.fetchone()[1]
            views[view_name] = create_stmt
    return views


class ViewComparator(BaseComparator):
    """视图比较器"""

    def _do_compare(
        self,
        task_log_id: int,
        source_conn: pymysql.Connection,
        target_conn: pymysql.Connection,
    ) -> List[Result]:
        """执行视图比较"""
        # 获取源数据库和目标数据库中的所有视图
        source_views = _get_views(source_conn)
        target_views = _get_views(target_conn)

        results = []

        # 比较视图
        all_view_names = set(source_views.keys()) | set(target_views.keys())
        for view_name in all_view_names:
            if view_name not in source_views:
                # 视图在源数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=view_name,
                    has_differences=True,
                    source_definition=None,
                    target_definition=target_views[view_name],
                    difference_details={
                        "result_type": "missing_in_source",
                        "message": f"视图 {view_name} 在源数据库中不存在",
                    },
                    change_sql=f"DROP VIEW IF EXISTS `{view_name}`;",
                )
                results.append(result)
            elif view_name not in target_views:
                # 视图在目标数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=view_name,
                    has_differences=True,
                    source_definition=source_views[view_name],
                    target_definition=None,
                    difference_details={
                        "result_type": "missing_in_target",
                        "message": f"视图 {view_name} 在目标数据库中不存在",
                    },
                    change_sql=source_views[view_name],
                )
                results.append(result)
            else:
                # 比较视图定义
                if source_views[view_name] != target_views[view_name]:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=view_name,
                        has_differences=True,
                        source_definition=source_views[view_name],
                        target_definition=target_views[view_name],
                        difference_details={
                            "result_type": "definition_mismatch",
                            "message": f"视图 {view_name} 的定义不同",
                        },
                        change_sql=f"DROP VIEW IF EXISTS `{view_name}`;\n{source_views[view_name]}",
                    )
                    results.append(result)
                else:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=view_name,
                        has_differences=False,
                        source_definition=source_views[view_name],
                        target_definition=target_views[view_name],
                    )
                    results.append(result)

        return results
