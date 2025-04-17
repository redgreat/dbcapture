from typing import Dict, Any, List
import pymysql
from sqlalchemy.orm import Session

from app.models.comparison import Comparison, ComparisonResult, ComparisonType


class BaseComparator:
    """基础比较器类，提供通用的数据库连接和比较逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        
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
        
    def _create_result(
        self,
        comparison_id: int,
        object_name: str,
        has_differences: bool,
        source_definition: str | None = None,
        target_definition: str | None = None,
        difference_details: Dict[str, Any] | None = None,
        change_sql: str | None = None
    ) -> ComparisonResult:
        """创建比较结果对象"""
        return ComparisonResult(
            comparison_id=comparison_id,
            type=self.comparison_type,
            object_name=object_name,
            has_differences=has_differences,
            source_definition=source_definition,
            target_definition=target_definition,
            difference_details=difference_details,
            change_sql=change_sql
        )
        
    def compare(self, comparison_id: int) -> List[ComparisonResult]:
        """执行比较"""
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
            results = self._do_compare(comparison_id, source_conn, target_conn)
            
            # 保存所有结果
            for result in results:
                self.db.add(result)
            self.db.commit()
            
            return results
            
        finally:
            source_conn.close()
            target_conn.close()
            
    def _do_compare(self, comparison_id: int, source_conn: pymysql.Connection, target_conn: pymysql.Connection) -> List[ComparisonResult]:
        """执行具体的比较逻辑，由子类实现"""
        raise NotImplementedError("子类必须实现此方法") 