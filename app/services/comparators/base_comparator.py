from typing import Dict, Any, List
import pymysql
from sqlalchemy.orm import Session

from app.models.tasks import Result, TaskLog, TaskStatus, ResultType


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


class BaseComparator:
    """基础比较器类，提供通用的数据库连接和比较逻辑"""

    def __init__(self, db: Session):
        self.db = db

    def _create_result(
        self,
        task_log_id: int,
        object_name: str,
        has_differences: bool,
        source_definition: str | None = None,
        target_definition: str | None = None,
        difference_details: Dict[str, Any] | None = None,
        change_sql: str | None = None,
        type: ResultType = None,
    ) -> Result:
        """创建比较结果对象"""
        if type is None:
            # 根据比较器类型自动设置结果类型
            comparator_name = self.__class__.__name__.lower()
            if 'table' in comparator_name:
                type = ResultType.TABLE
            elif 'view' in comparator_name:
                type = ResultType.VIEW
            elif 'procedure' in comparator_name:
                type = ResultType.PROCEDURE
            elif 'function' in comparator_name:
                type = ResultType.FUNCTION
            elif 'trigger' in comparator_name:
                type = ResultType.TRIGGER
            elif 'config' in comparator_name:
                type = ResultType.CONFIG
            else:
                # 默认为表类型
                type = ResultType.TABLE

        return Result(
            task_log_id=task_log_id,
            object_name=object_name,
            has_differences=has_differences,
            source_definition=source_definition,
            target_definition=target_definition,
            difference_details=difference_details,
            change_sql=change_sql,
            type=type,
        )

    def compare(self, task_log_id: int, report_path: str = None) -> List[Result]:
        """执行比较"""
        task_log = self.db.query(TaskLog).get(task_log_id)
        if not task_log:
            raise ValueError(f"任务日志 {task_log_id} 不存在")

        # 通过 task_log 找到对应 Task，再获取数据库连接信息
        from app.models.tasks import Task
        task = self.db.query(Task).get(task_log.task_id)
        if not task:
            raise ValueError(f"任务 {task_log.task_id} 不存在")
        source_conn_obj = task.source_conn
        target_conn_obj = task.target_conn

        source_conn = _get_connection(
            source_conn_obj.host,
            source_conn_obj.port,
            source_conn_obj.user,
            source_conn_obj.password,
            source_conn_obj.database,
        )
        target_conn = _get_connection(
            target_conn_obj.host,
            target_conn_obj.port,
            target_conn_obj.user,
            target_conn_obj.password,
            target_conn_obj.database,
        )

        try:
            results = self._do_compare(task_log_id, source_conn, target_conn)

            # 保存所有结果
            for result in results:
                self.db.add(result)
            # 成功：状态同步到日志
            task_log.status = TaskStatus.COMPLETED
            task_log.error_message = None
            if report_path:
                task_log.result_url = report_path
            self.db.commit()

            return results

        except Exception as e:
            # 失败：状态同步到日志
            task_log.status = TaskStatus.FAILED
            task_log.error_message = str(e)
            self.db.commit()
            raise

        finally:
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

    def _do_compare(
        self,
        task_log_id: int,
        source_conn: pymysql.Connection,
        target_conn: pymysql.Connection,
    ) -> List[Result]:
        """执行具体的比较逻辑，由子类实现"""
        raise NotImplementedError("子类必须实现此方法")
