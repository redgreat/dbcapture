from typing import List, Dict, Any, Optional
import pymysql
from sqlalchemy.orm import Session

from app.models.comparison import Comparison, ComparisonResult, ComparisonType, ComparisonStatus
from app.core.config import settings
from app.models.db_connection import DbConnection
from app.services.comparators import (
    ViewComparator,
    TableComparator,
    ProcedureComparator,
    FunctionComparator,
    TriggerComparator
)


class DatabaseComparisonService:
    def __init__(self, db: Session):
        self.db = db
        self.view_comparator = ViewComparator(db)
        self.table_comparator = TableComparator(db)
        self.procedure_comparator = ProcedureComparator(db)
        self.function_comparator = FunctionComparator(db)
        self.trigger_comparator = TriggerComparator(db)

    def create_comparison(self, comparison_data):
        """创建新的数据库比较任务"""
        # 验证源数据库连接是否存在
        source_conn = self.db.query(DbConnection).get(comparison_data.source_conn_id)
        if not source_conn:
            raise ValueError(f"源数据库连接ID {comparison_data.source_conn_id} 不存在")

        # 验证目标数据库连接是否存在
        target_conn = self.db.query(DbConnection).get(comparison_data.target_conn_id)
        if not target_conn:
            raise ValueError(f"目标数据库连接ID {comparison_data.target_conn_id} 不存在")

        comparison = Comparison(
            source_conn_id=comparison_data.source_conn_id,
            target_conn_id=comparison_data.target_conn_id,
            config=comparison_data.config
        )
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)
        return comparison

    def _get_connection(self, host: str, port: str, user: str, password: str, database: str) -> pymysql.Connection:
        """创建数据库连接"""
        return pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )

    def compare_database_config(self, comparison_id: int) -> ComparisonResult:
        """比较数据库配置"""
        comparison = self.db.query(Comparison).get(comparison_id)
        if not comparison:
            raise ValueError(f"比较任务 {comparison_id} 不存在")
            
        # 获取数据库连接信息
        source_conn = comparison.source_conn
        target_conn = comparison.target_conn
        
        source_conn = self._get_connection(
            source_conn.host,
            source_conn.port,
            source_conn.user,
            source_conn.password,
            source_conn.database
        )
        target_conn = self._get_connection(
            target_conn.host,
            target_conn.port,
            target_conn.user,
            target_conn.password,
            target_conn.database
        )

        try:
            # 获取数据库配置
            source_config = self._get_database_config(source_conn)
            target_config = self._get_database_config(target_conn)

            # 调试日志
            print('====[compare_database_config 调试]====')
            print('source_config:', source_config)
            print('target_config:', target_config)
            differences = self._compare_configs(source_config, target_config)
            print('differences:', differences)
            print('====[调试结束]====')
            
            result = ComparisonResult(
                comparison_id=comparison_id,
                type=ComparisonType.CONFIG,
                object_name="database_config",
                has_differences=bool(differences),
                source_definition=str(source_config),
                target_definition=str(target_config),
                difference_details=differences,
                change_sql=self._generate_config_change_sql(differences) if differences else None
            )
            
            self.db.add(result)
            self.db.commit()
            return result

        finally:
            source_conn.close()
            target_conn.close()

    def _get_database_config(self, conn: pymysql.Connection) -> Dict[str, Any]:
        """获取数据库配置信息"""
        cursor = conn.cursor()
        config = {}
        
        # 获取字符集
        cursor.execute("SHOW VARIABLES LIKE 'character_set_%'")
        for row in cursor.fetchall():
            config[row[0]] = row[1]
            
        # 获取排序规则
        cursor.execute("SHOW VARIABLES LIKE 'collation_%'")
        for row in cursor.fetchall():
            config[row[0]] = row[1]
            
        cursor.close()
        return config

    def _compare_configs(self, source_config: Dict[str, Any], target_config: Dict[str, Any]) -> Dict[str, Any]:
        """比较配置差异"""
        differences = {}
        
        for key in source_config:
            if key not in target_config:
                differences[key] = {
                    "type": "missing_in_target",
                    "source_value": source_config[key]
                }
            elif source_config[key] != target_config[key]:
                differences[key] = {
                    "type": "value_mismatch",
                    "source_value": source_config[key],
                    "target_value": target_config[key]
                }
                
        for key in target_config:
            if key not in source_config:
                differences[key] = {
                    "type": "missing_in_source",
                    "target_value": target_config[key]
                }
                
        return differences

    def _generate_config_change_sql(self, differences: Dict[str, Any]) -> str:
        """生成配置变更SQL"""
        sql_statements = []
        
        for key, diff in differences.items():
            if diff["type"] == "value_mismatch":
                if "character_set" in key:
                    sql_statements.append(f"ALTER DATABASE CHARACTER SET = {diff['source_value']};")
                elif "collation" in key:
                    sql_statements.append(f"ALTER DATABASE COLLATE = {diff['source_value']};")
                    
        return "\n".join(sql_statements)

    def compare_views(self, comparison_id: int) -> List[ComparisonResult]:
        """比较视图"""
        return self.view_comparator.compare(comparison_id)

    def compare_table_structure(self, comparison_id: int) -> List[ComparisonResult]:
        """比较表结构"""
        return self.table_comparator.compare(comparison_id)

    def compare_procedures(self, comparison_id: int) -> List[ComparisonResult]:
        """比较存储过程"""
        return self.procedure_comparator.compare(comparison_id)

    def compare_functions(self, comparison_id: int) -> List[ComparisonResult]:
        """比较自定义函数"""
        return self.function_comparator.compare(comparison_id)

    def compare_triggers(self, comparison_id: int) -> List[ComparisonResult]:
        """比较触发器"""
        return self.trigger_comparator.compare(comparison_id)

    def run_comparison(self, comparison_id: int) -> None:
        """运行完整的数据库比较"""
        print(f"====[开始执行比较任务 {comparison_id}]====")
        comparison = self.db.query(Comparison).get(comparison_id)
        if not comparison:
            print(f"错误：找不到比较任务 {comparison_id}")
            raise ValueError(f"比较任务 {comparison_id} 不存在")
            
        print(f"任务状态：{comparison.status}")
        comparison.status = ComparisonStatus.RUNNING
        self.db.commit()
        print("已更新任务状态为RUNNING")

        try:
            print("开始执行数据库配置比较...")
            self.compare_database_config(comparison_id)
            print("数据库配置比较完成")
            
            print("开始执行表结构比较...")
            self.compare_table_structure(comparison_id)
            print("表结构比较完成")
            
            print("开始执行视图比较...")
            self.compare_views(comparison_id)
            print("视图比较完成")
            
            print("开始执行存储过程比较...")
            self.compare_procedures(comparison_id)
            print("存储过程比较完成")
            
            print("开始执行函数比较...")
            self.compare_functions(comparison_id)
            print("函数比较完成")
            
            print("开始执行触发器比较...")
            self.compare_triggers(comparison_id)
            print("触发器比较完成")

            comparison.status = ComparisonStatus.COMPLETED
            print("所有比较完成，更新状态为COMPLETED")
        except Exception as e:
            print(f"比较过程中发生错误：{str(e)}")
            comparison.status = ComparisonStatus.FAILED
            comparison.error_message = str(e)
            print(f"更新任务状态为FAILED，错误信息：{str(e)}")
        finally:
            self.db.commit()
            print("====[比较任务执行结束]====\n") 