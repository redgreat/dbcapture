from typing import Dict, List, Any
import pymysql

from app.models.comparison import ComparisonType, ComparisonResult
from .base_comparator import BaseComparator


class ProcedureComparator(BaseComparator):
    """存储过程比较器"""
    
    def __init__(self, db):
        super().__init__(db)
        self.comparison_type = ComparisonType.PROCEDURE
        
    def _get_procedures(self, conn: pymysql.Connection) -> Dict[str, str]:
        """获取数据库中的所有存储过程及其创建语句"""
        procedures = {}
        with conn.cursor() as cursor:
            # 获取所有存储过程
            cursor.execute("""
                SELECT ROUTINE_NAME 
                FROM INFORMATION_SCHEMA.ROUTINES 
                WHERE ROUTINE_TYPE = 'PROCEDURE'
                AND ROUTINE_SCHEMA = DATABASE()
            """)
            for (proc_name,) in cursor.fetchall():
                # 获取存储过程的创建语句
                cursor.execute(f"SHOW CREATE PROCEDURE `{proc_name}`")
                create_stmt = cursor.fetchone()[2]  # 第3列是创建语句
                procedures[proc_name] = create_stmt
        return procedures
        
    def _do_compare(self, comparison_id: int, source_conn: pymysql.Connection, target_conn: pymysql.Connection) -> List[ComparisonResult]:
        """执行存储过程比较"""
        # 获取源数据库和目标数据库的所有存储过程
        source_procedures = self._get_procedures(source_conn)
        target_procedures = self._get_procedures(target_conn)
        
        results = []
        
        # 比较存储过程
        all_procedure_names = set(source_procedures.keys()) | set(target_procedures.keys())
        for procedure_name in all_procedure_names:
            if procedure_name not in source_procedures:
                # 存储过程在源数据库中不存在
                result = self._create_result(
                    comparison_id=comparison_id,
                    object_name=procedure_name,
                    has_differences=True,
                    source_definition=None,
                    target_definition=target_procedures[procedure_name],
                    difference_details={
                        "type": "missing_in_source",
                        "message": f"存储过程 {procedure_name} 在源数据库中不存在"
                    },
                    change_sql=f"DROP PROCEDURE IF EXISTS `{procedure_name}`;"
                )
                results.append(result)
            elif procedure_name not in target_procedures:
                # 存储过程在目标数据库中不存在
                result = self._create_result(
                    comparison_id=comparison_id,
                    object_name=procedure_name,
                    has_differences=True,
                    source_definition=source_procedures[procedure_name],
                    target_definition=None,
                    difference_details={
                        "type": "missing_in_target",
                        "message": f"存储过程 {procedure_name} 在目标数据库中不存在"
                    },
                    change_sql=source_procedures[procedure_name]
                )
                results.append(result)
            else:
                # 比较存储过程定义
                if source_procedures[procedure_name] != target_procedures[procedure_name]:
                    result = self._create_result(
                        comparison_id=comparison_id,
                        object_name=procedure_name,
                        has_differences=True,
                        source_definition=source_procedures[procedure_name],
                        target_definition=target_procedures[procedure_name],
                        difference_details={
                            "type": "definition_mismatch",
                            "message": f"存储过程 {procedure_name} 的定义不同"
                        },
                        change_sql=f"DROP PROCEDURE IF EXISTS `{procedure_name}`;\n{source_procedures[procedure_name]}"
                    )
                    results.append(result)
                else:
                    result = self._create_result(
                        comparison_id=comparison_id,
                        object_name=procedure_name,
                        has_differences=False,
                        source_definition=source_procedures[procedure_name],
                        target_definition=target_procedures[procedure_name]
                    )
                    results.append(result)
                    
        return results 