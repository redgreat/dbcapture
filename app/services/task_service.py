from typing import List, Dict, Any, Optional
import pymysql
from sqlalchemy.orm import Session

from app.models.tasks import (
    Task,
    Result,
    TaskStatus,
    TaskLog,
)
from app.core.config import settings
from app.models.connections import Connection
from app.services.comparators import (
    ViewComparator,
    TableComparator,
    ProcedureComparator,
    FunctionComparator,
    TriggerComparator,
)
from app.schemas.task import TaskCreate
from app.services.report_service import ReportService

def _get_database_config(conn: pymysql.Connection) -> Dict[str, Any]:
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


def _compare_configs(
    source_config: Dict[str, Any], target_config: Dict[str, Any]
) -> Dict[str, Any]:
    """比较配置差异"""
    differences = {}

    for key in source_config:
        if key not in target_config:
            differences[key] = {
                "type": "missing_in_target",
                "source_value": source_config[key],
            }
        elif source_config[key] != target_config[key]:
            differences[key] = {
                "type": "value_mismatch",
                "source_value": source_config[key],
                "target_value": target_config[key],
            }

    for key in target_config:
        if key not in source_config:
            differences[key] = {
                "type": "missing_in_source",
                "target_value": target_config[key],
            }

    return differences


def _generate_config_change_sql(differences: Dict[str, Any]) -> str:
    """生成配置变更SQL"""
    sql_statements = []

    for key, diff in differences.items():
        if diff["type"] == "value_mismatch":
            if "character_set" in key:
                sql_statements.append(
                    f"ALTER DATABASE CHARACTER SET = {diff['source_value']};"
                )
            elif "collation" in key:
                sql_statements.append(
                    f"ALTER DATABASE COLLATE = {diff['source_value']};"
                )

    return "\n".join(sql_statements)


def _get_connection(
    host: str, port: str, user: str, password: str, database: str
) -> pymysql.Connection:
    """创建数据库连接"""
    return pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
    )


class DatabaseComparisonService:
    def __init__(self, db: Session):
        self.db = db
        self.view_comparator = ViewComparator(db)
        self.table_comparator = TableComparator(db)
        self.procedure_comparator = ProcedureComparator(db)
        self.function_comparator = FunctionComparator(db)
        self.trigger_comparator = TriggerComparator(db)
        self.report_service = ReportService()

    def create_task(self, task_data: TaskCreate) -> Task:
        """创建新的数据库比较任务"""
        # 验证源数据库连接是否存在
        source_conn = self.db.query(Connection).get(task_data.source_conn_id)
        if not source_conn:
            raise ValueError(f"源数据库连接ID {task_data.source_conn_id} 不存在")

        # 验证目标数据库连接是否存在
        target_conn = self.db.query(Connection).get(task_data.target_conn_id)
        if not target_conn:
            raise ValueError(f"目标数据库连接ID {task_data.target_conn_id} 不存在")

        task = Task(
            name=task_data.name,
            description=task_data.description,
            source_conn_id=task_data.source_conn_id,
            source_conn_name=source_conn.name,
            target_conn_id=task_data.target_conn_id,
            target_conn_name=target_conn.name,
            config=task_data.config,
            status=task_data.status,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        task_log = TaskLog(task_id=task.id, status=TaskStatus.RUNNING)
        self.db.add(task_log)
        self.db.commit()
        self.db.refresh(task_log)

        return task

    def compare_database_config(self, task_log_id: int) -> Result:
        """比较数据库配置"""
        task_log = self.db.query(TaskLog).get(task_log_id)
        if not task_log:
            raise ValueError(f"任务日志 {task_log_id} 不存在")
        task = self.db.query(Task).get(task_log.task_id)
        if not task:
            raise ValueError(f"比较任务 {task_log.task_id} 不存在")

        # 获取数据库连接信息
        source_conn = task.source_conn
        target_conn = task.target_conn

        source_conn = _get_connection(
            source_conn.host,
            source_conn.port,
            source_conn.user,
            source_conn.password,
            source_conn.database,
        )
        target_conn = _get_connection(
            target_conn.host,
            target_conn.port,
            target_conn.user,
            target_conn.password,
            target_conn.database,
        )

        try:
            # 获取数据库配置
            source_config = _get_database_config(source_conn)
            target_config = _get_database_config(target_conn)

            # 调试日志
            print("====[compare_database_config 调试]====")
            print("source_config:", source_config)
            print("target_config:", target_config)
            differences = _compare_configs(source_config, target_config)
            print("differences:", differences)
            print("====[调试结束]====")

            task_log = self.db.query(TaskLog).get(task_log_id)
            if not task_log:
                raise ValueError(f"任务日志 {task_log_id} 不存在")
            task_id = task_log.task_id

            result = Result(
                task_log_id=task_log_id,
                object_name="database_config",
                has_differences=bool(differences),
                source_definition=str(source_config),
                target_definition=str(target_config),
                difference_details=differences,
                change_sql=(
                    _generate_config_change_sql(differences) if differences else None
                ),
            )

            self.db.add(result)
            self.db.commit()
            return result

        finally:
            # 只关闭pymysql.Connection对象
            try:
                if hasattr(source_conn, 'close') and callable(source_conn.close):
                    source_conn.close()
            except Exception:
                pass
            try:
                if hasattr(target_conn, 'close') and callable(target_conn.close):
                    target_conn.close()
            except Exception:
                pass

    def compare_views(self, task_log_id: int) -> List[Result]:
        """比较视图"""
        return self.view_comparator.compare(task_log_id)

    def compare_table_structure(self, task_log_id: int) -> List[Result]:
        """比较表结构"""
        return self.table_comparator.compare(task_log_id)

    def compare_procedures(self, task_log_id: int) -> List[Result]:
        """比较存储过程"""
        return self.procedure_comparator.compare(task_log_id)

    def compare_functions(self, task_log_id: int) -> List[Result]:
        """比较自定义函数"""
        return self.function_comparator.compare(task_log_id)

    def compare_triggers(self, task_log_id: int) -> List[Result]:
        """比较触发器"""
        return self.trigger_comparator.compare(task_log_id)

    def run_comparison(self, task_log_id: int) -> None:
        """运行完整的数据库比较"""
        task_log = self.db.query(TaskLog).get(task_log_id)
        print(f"====[开始执行比较任务 {task_log_id}]====")
        task = self.db.query(Task).get(task_log.task_id)
        if not task:
            print(f"错误：找不到比较任务 {task_log.task_id}")
            raise ValueError(f"比较任务 {task_log.task_id} 不存在")

        print(f"任务状态：{task.status}")
        task.status = TaskStatus.RUNNING
        self.db.commit()
        print("已更新任务状态为RUNNING")

        try:
            print("开始执行数据库配置比较...")
            self.compare_database_config(task_log_id)
            print("数据库配置比较完成")

            print("开始执行表结构比较...")
            self.compare_table_structure(task_log_id)
            print("表结构比较完成")

            print("开始执行视图比较...")
            self.compare_views(task_log_id)
            print("视图比较完成")

            print("开始执行存储过程比较...")
            self.compare_procedures(task_log_id)
            print("存储过程比较完成")

            print("开始执行函数比较...")
            self.compare_functions(task_log_id)
            print("函数比较完成")

            print("开始执行触发器比较...")
            self.compare_triggers(task_log_id)
            print("触发器比较完成")

            print("开始生成报告...")
            reports = self.report_service.generate_reports(task_log)
            if reports:
                report_path = reports[0].get('file_path')
                if report_path:
                    task_log.result_url = report_path
                    self.db.commit()
            print("报告生成并已写入日志")

            task.status = TaskStatus.COMPLETED
            print("所有比较完成，更新状态为COMPLETED")
        except Exception as e:
            print(f"比较过程中发生错误：{str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            print(f"更新任务状态为FAILED，错误信息：{str(e)}")
        finally:
            self.db.commit()
            print("====[比较任务执行结束]====\n")
