from typing import Dict, List
import pymysql

from app.models.tasks import Result
from .base_comparator import BaseComparator


def _get_functions(conn: pymysql.Connection) -> Dict[str, str]:
    """获取数据库中的所有函数及其创建语句"""
    functions = {}
    with conn.cursor() as cursor:
        # 获取所有函数
        cursor.execute(
            """
            SELECT ROUTINE_NAME 
            FROM INFORMATION_SCHEMA.ROUTINES 
            WHERE ROUTINE_TYPE = 'FUNCTION'
            AND ROUTINE_SCHEMA = DATABASE()
        """
        )
        for (func_name,) in cursor.fetchall():
            # 获取函数的创建语句
            cursor.execute(f"SHOW CREATE FUNCTION `{func_name}`")
            create_stmt = cursor.fetchone()[2]  # 第3列是创建语句
            functions[func_name] = create_stmt
    return functions


class FunctionComparator(BaseComparator):
    """函数比较器"""

    def _do_compare(
        self,
        task_log_id: int,
        source_conn: pymysql.Connection,
        target_conn: pymysql.Connection,
    ) -> List[Result]:
        """执行函数比较"""
        # 获取源数据库和目标数据库的所有函数
        source_functions = _get_functions(source_conn)
        target_functions = _get_functions(target_conn)

        results = []

        # 比较函数
        all_function_names = set(source_functions.keys()) | set(target_functions.keys())
        for function_name in all_function_names:
            if function_name not in source_functions:
                # 函数在源数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=function_name,
                    has_differences=True,
                    source_definition=None,
                    target_definition=target_functions[function_name],
                    difference_details={
                        "result_type": "missing_in_source",
                        "message": f"函数 {function_name} 在源数据库中不存在",
                    },
                    change_sql=f"DROP FUNCTION IF EXISTS `{function_name}`;",
                )
                results.append(result)
            elif function_name not in target_functions:
                # 函数在目标数据库中不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=function_name,
                    has_differences=True,
                    source_definition=source_functions[function_name],
                    target_definition=None,
                    difference_details={
                        "result_type": "missing_in_target",
                        "message": f"函数 {function_name} 在目标数据库中不存在",
                    },
                    change_sql=source_functions[function_name],
                )
                results.append(result)
            else:
                # 比较函数定义
                if source_functions[function_name] != target_functions[function_name]:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=function_name,
                        has_differences=True,
                        source_definition=source_functions[function_name],
                        target_definition=target_functions[function_name],
                        difference_details={
                            "result_type": "definition_mismatch",
                            "message": f"函数 {function_name} 的定义不同",
                        },
                        change_sql=f"DROP FUNCTION IF EXISTS `{function_name}`;\n{source_functions[function_name]}",
                    )
                    results.append(result)
                else:
                    result = self._create_result(
                        task_log_id=task_log_id,
                        object_name=function_name,
                        has_differences=False,
                        source_definition=source_functions[function_name],
                        target_definition=target_functions[function_name],
                    )
                    results.append(result)

        return results
