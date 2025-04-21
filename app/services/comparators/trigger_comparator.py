from typing import Dict, List
import pymysql

from app.models.tasks import Result
from .base_comparator import BaseComparator


def _get_triggers(conn: pymysql.Connection) -> Dict[str, str]:
    """获取数据库中的所有触发器及其创建语句"""
    triggers = {}
    with conn.cursor() as cursor:
        # 获取所有触发器
        cursor.execute(
            """
            SELECT TRIGGER_NAME 
            FROM INFORMATION_SCHEMA.TRIGGERS 
            WHERE TRIGGER_SCHEMA = DATABASE()
        """
        )
        for (trigger_name,) in cursor.fetchall():
            # 获取触发器的创建语句
            cursor.execute(f"SHOW CREATE TRIGGER `{trigger_name}`")
            create_stmt = cursor.fetchone()[2]  # 第3列是创建语句
            triggers[trigger_name] = create_stmt
    return triggers


class TriggerComparator(BaseComparator):
    """触发器比较器"""

    def _do_compare(
        self,
        task_log_id: int,
        source_conn: pymysql.Connection,
        target_conn: pymysql.Connection,
    ) -> List[Result]:
        """执行触发器比较"""
        # 获取源数据库和目标数据库的所有触发器
        source_triggers = _get_triggers(source_conn)
        target_triggers = _get_triggers(target_conn)

        results = []

        # 比较触发器
        all_trigger_names = set(source_triggers.keys()) | set(target_triggers.keys())
        for trigger_name in all_trigger_names:
            if trigger_name not in source_triggers:
                # 触发器在源数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=trigger_name,
                    has_differences=True,
                    source_definition=None,
                    target_definition=target_triggers[trigger_name],
                    difference_details={
                        "result_type": "missing_in_source",
                        "message": f"触发器 {trigger_name} 在源数据库中不存在",
                    },
                    change_sql=f"DROP TRIGGER IF EXISTS `{trigger_name}`;",
                )
                results.append(result)
            elif trigger_name not in target_triggers:
                # 触发器在目标数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=trigger_name,
                    has_differences=True,
                    source_definition=source_triggers[trigger_name],
                    target_definition=None,
                    difference_details={
                        "result_type": "missing_in_target",
                        "message": f"触发器 {trigger_name} 在目标数据库中不存在",
                    },
                    change_sql=source_triggers[trigger_name],
                )
                results.append(result)
            else:
                # 比较触发器定义
                if source_triggers[trigger_name] != target_triggers[trigger_name]:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=trigger_name,
                        has_differences=True,
                        source_definition=source_triggers[trigger_name],
                        target_definition=target_triggers[trigger_name],
                        difference_details={
                            "result_type": "definition_mismatch",
                            "message": f"触发器 {trigger_name} 的定义不同",
                        },
                        change_sql=f"DROP TRIGGER IF EXISTS `{trigger_name}`;\n{source_triggers[trigger_name]}",
                    )
                    results.append(result)
                else:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=trigger_name,
                        has_differences=False,
                        source_definition=source_triggers[trigger_name],
                        target_definition=target_triggers[trigger_name],
                    )
                    results.append(result)

        return results
