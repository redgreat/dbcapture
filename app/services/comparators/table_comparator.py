from typing import Dict, List, Any
import pymysql

from app.models.tasks import Result
from .base_comparator import BaseComparator


def _get_tables(conn: pymysql.Connection) -> Dict[str, str]:
    """获取数据库中的所有表及其创建语句"""
    tables = {}
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_TYPE = 'BASE TABLE'
        """
        )
        for (table_name,) in cursor.fetchall():
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_stmt = cursor.fetchone()[1]
            tables[table_name] = create_stmt
    return tables


def _get_table_columns(conn: pymysql.Connection, table_name: str) -> Dict[str, Dict]:
    """获取表的列定义"""
    columns = {}
    with conn.cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        for col in cursor.fetchall():
            columns[col[0]] = {
                "type": col[1],
                "nullable": col[2] == "YES",
                "default": col[4],
                "extra": col[5],
            }
    return columns


def _get_table_indexes(conn: pymysql.Connection, table_name: str) -> Dict[str, Dict]:
    """获取表的索引定义"""
    indexes = {}
    with conn.cursor() as cursor:
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        for idx in cursor.fetchall():
            index_name = idx[2]
            if index_name not in indexes:
                indexes[index_name] = {"unique": idx[1] == 0, "columns": []}
            indexes[index_name]["columns"].append(idx[4])
    return indexes


def _get_table_constraints(
    conn: pymysql.Connection, table_name: str
) -> Dict[str, Dict]:
    """获取表的约束定义"""
    constraints = {}
    with conn.cursor() as cursor:
        # 获取外键约束
        cursor.execute(
            f"""
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL
            AND CONSTRAINT_NAME != 'PRIMARY'
        """,
            (table_name,),
        )

        for row in cursor.fetchall():
            constraint_name = row[0]
            if constraint_name not in constraints:
                constraints[constraint_name] = {
                    "type": "FOREIGN KEY",
                    "columns": [],
                    "referenced_table": row[2],
                    "referenced_columns": [],
                }
            constraints[constraint_name]["columns"].append(row[1])
            if row[3]:
                constraints[constraint_name]["referenced_columns"].append(row[3])

        # 获取唯一约束
        cursor.execute(
            f"""
            SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME != 'PRIMARY'
            AND CONSTRAINT_NAME NOT IN (
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            )
        """,
            (table_name, table_name),
        )

        for row in cursor.fetchall():
            constraint_name = row[0]
            if constraint_name not in constraints:
                constraints[constraint_name] = {"type": "UNIQUE", "columns": []}
            constraints[constraint_name]["columns"].append(row[1])

    return constraints


def _compare_columns(
    source: Dict[str, Dict], target: Dict[str, Dict]
) -> Dict[str, Any]:
    """比较列定义"""
    differences = {}
    all_columns = set(source.keys()) | set(target.keys())

    for col in all_columns:
        if col not in source:
            differences[col] = {
                "type": "missing_in_source",
                "message": f"列 {col} 在源表中不存在",
            }
        elif col not in target:
            differences[col] = {
                "type": "missing_in_target",
                "message": f"列 {col} 在目标表中不存在",
            }
        else:
            source_col = source[col]
            target_col = target[col]
            col_diffs = {}

            if source_col["type"] != target_col["type"]:
                col_diffs["type"] = {
                    "source": source_col["type"],
                    "target": target_col["type"],
                }
            if source_col["nullable"] != target_col["nullable"]:
                col_diffs["nullable"] = {
                    "source": source_col["nullable"],
                    "target": target_col["nullable"],
                }
            if source_col["default"] != target_col["default"]:
                col_diffs["default"] = {
                    "source": source_col["default"],
                    "target": target_col["default"],
                }
            if source_col["extra"] != target_col["extra"]:
                col_diffs["extra"] = {
                    "source": source_col["extra"],
                    "target": target_col["extra"],
                }

            if col_diffs:
                differences[col] = col_diffs

    return differences


def _compare_indexes(
    source: Dict[str, Dict], target: Dict[str, Dict]
) -> Dict[str, Any]:
    """比较索引定义"""
    differences = {}
    all_indexes = set(source.keys()) | set(target.keys())

    for idx in all_indexes:
        if idx not in source:
            differences[idx] = {
                "type": "missing_in_source",
                "message": f"索引 {idx} 在源表中不存在",
            }
        elif idx not in target:
            differences[idx] = {
                "type": "missing_in_target",
                "message": f"索引 {idx} 在目标表中不存在",
            }
        else:
            source_idx = source[idx]
            target_idx = target[idx]
            idx_diffs = {}

            if source_idx["unique"] != target_idx["unique"]:
                idx_diffs["unique"] = {
                    "source": source_idx["unique"],
                    "target": target_idx["unique"],
                }
            if set(source_idx["columns"]) != set(target_idx["columns"]):
                idx_diffs["columns"] = {
                    "source": source_idx["columns"],
                    "target": target_idx["columns"],
                }

            if idx_diffs:
                differences[idx] = idx_diffs

    return differences


def _compare_constraints(
    source: Dict[str, Dict], target: Dict[str, Dict]
) -> Dict[str, Any]:
    """比较约束定义"""
    differences = {}
    all_constraints = set(source.keys()) | set(target.keys())

    for constr in all_constraints:
        if constr not in source:
            differences[constr] = {
                "type": "missing_in_source",
                "message": f"约束 {constr} 在源表中不存在",
            }
        elif constr not in target:
            differences[constr] = {
                "type": "missing_in_target",
                "message": f"约束 {constr} 在目标表中不存在",
            }
        else:
            source_constr = source[constr]
            target_constr = target[constr]
            constr_diffs = {}

            if source_constr["type"] != target_constr["type"]:
                constr_diffs["type"] = {
                    "source": source_constr["type"],
                    "target": target_constr["type"],
                }
            if set(source_constr["columns"]) != set(target_constr["columns"]):
                constr_diffs["columns"] = {
                    "source": source_constr["columns"],
                    "target": target_constr["columns"],
                }

            # 只在外键约束时比较引用信息
            if (
                source_constr["type"] == "FOREIGN KEY"
                and target_constr["type"] == "FOREIGN KEY"
            ):
                if source_constr.get("referenced_table") != target_constr.get(
                    "referenced_table"
                ):
                    constr_diffs["referenced_table"] = {
                        "source": source_constr.get("referenced_table"),
                        "target": target_constr.get("referenced_table"),
                    }
                if set(source_constr.get("referenced_columns", [])) != set(
                    target_constr.get("referenced_columns", [])
                ):
                    constr_diffs["referenced_columns"] = {
                        "source": source_constr.get("referenced_columns", []),
                        "target": target_constr.get("referenced_columns", []),
                    }

            if constr_diffs:
                differences[constr] = constr_diffs

    return differences


def _generate_table_change_sql(table_name: str, differences: Dict[str, Any]) -> str:
    """生成表结构变更SQL"""
    sql_statements = []

    try:
        if "columns" in differences:
            for col_name, col_diff in differences["columns"].items():
                if col_diff.get("type") == "missing_in_target":
                    # 添加列
                    if "source" not in col_diff:
                        continue
                    source_col = col_diff["source"]
                    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {source_col['type']}"
                    if not source_col["nullable"]:
                        sql += " NOT NULL"
                    if source_col["default"] is not None:
                        sql += f" DEFAULT {source_col['default']}"
                    if source_col["extra"]:
                        sql += f" {source_col['extra']}"
                    sql_statements.append(sql + ";")
                elif col_diff.get("type") == "missing_in_source":
                    # 删除列
                    sql_statements.append(
                        f"ALTER TABLE `{table_name}` DROP COLUMN `{col_name}`;"
                    )
                else:
                    # 修改列
                    if "source" not in col_diff:
                        continue
                    source_col = col_diff["source"]
                    sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{col_name}` {source_col['type']}"
                    if not source_col["nullable"]:
                        sql += " NOT NULL"
                    if source_col["default"] is not None:
                        sql += f" DEFAULT {source_col['default']}"
                    if source_col["extra"]:
                        sql += f" {source_col['extra']}"
                    sql_statements.append(sql + ";")

        if "indexes" in differences:
            for idx_name, idx_diff in differences["indexes"].items():
                if idx_diff.get("type") == "missing_in_target":
                    # 添加索引
                    if "source" not in idx_diff:
                        continue
                    source_idx = idx_diff["source"]
                    if idx_name == "PRIMARY":
                        sql = f"ALTER TABLE `{table_name}` ADD PRIMARY KEY ({', '.join(f'`{col}`' for col in source_idx['columns'])})"
                    else:
                        unique = "UNIQUE" if source_idx["unique"] else ""
                        sql = f"ALTER TABLE `{table_name}` ADD {unique} INDEX `{idx_name}` ({', '.join(f'`{col}`' for col in source_idx['columns'])})"
                    sql_statements.append(sql + ";")
                elif idx_diff.get("type") == "missing_in_source":
                    # 删除索引
                    if idx_name == "PRIMARY":
                        sql = f"ALTER TABLE `{table_name}` DROP PRIMARY KEY"
                    else:
                        sql = f"ALTER TABLE `{table_name}` DROP INDEX `{idx_name}`"
                    sql_statements.append(sql + ";")

        if "constraints" in differences:
            for constr_name, constr_diff in differences["constraints"].items():
                if constr_diff.get("type") == "missing_in_target":
                    # 添加约束
                    if "source" not in constr_diff:
                        continue

                    source_constr = constr_diff["source"]

                    if source_constr["type"] == "FOREIGN KEY":
                        # 检查必要字段
                        if not all(
                            key in source_constr
                            for key in [
                                "columns",
                                "referenced_table",
                                "referenced_columns",
                            ]
                        ):
                            continue

                        sql = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{constr_name}` FOREIGN KEY ({', '.join(f'`{col}`' for col in source_constr['columns'])}) REFERENCES `{source_constr['referenced_table']}` ({', '.join(f'`{col}`' for col in source_constr['referenced_columns'])})"
                        sql_statements.append(sql + ";")

                    elif source_constr["type"] == "UNIQUE":
                        if "columns" not in source_constr:
                            continue

                        sql = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{constr_name}` UNIQUE ({', '.join(f'`{col}`' for col in source_constr['columns'])})"
                        sql_statements.append(sql + ";")

                elif constr_diff.get("type") == "missing_in_source":
                    # 删除约束
                    sql = f"ALTER TABLE `{table_name}` DROP CONSTRAINT `{constr_name}`"
                    sql_statements.append(sql + ";")

        return "\n".join(sql_statements)

    except Exception as e:
        print(f"生成SQL时发生错误: {str(e)}")
        print(f"差异信息: {differences}")
        raise


class TableComparator(BaseComparator):
    """表比较器"""

    def _compare_table_details(
        self,
        table_name: str,
        source_columns: Dict[str, Dict],
        target_columns: Dict[str, Dict],
        source_indexes: Dict[str, Dict],
        target_indexes: Dict[str, Dict],
        source_constraints: Dict[str, Dict],
        target_constraints: Dict[str, Dict],
    ) -> Dict[str, Any]:
        """比较表的详细结构"""
        differences = {}

        # 比较列
        column_diffs = _compare_columns(source_columns, target_columns)
        if column_diffs:
            differences["columns"] = column_diffs

        # 比较索引
        index_diffs = _compare_indexes(source_indexes, target_indexes)
        if index_diffs:
            differences["indexes"] = index_diffs

        # 比较约束
        constraint_diffs = _compare_constraints(source_constraints, target_constraints)
        if constraint_diffs:
            differences["constraints"] = constraint_diffs

        return differences

    def _do_compare(
        self,
        task_log_id: int,
        source_conn: pymysql.Connection,
        target_conn: pymysql.Connection,
        config: Dict[str, Any] = None,
    ) -> List[Result]:
        """执行表比较"""
        # 获取源数据库和目标数据库的所有表
        source_tables = _get_tables(source_conn)
        target_tables = _get_tables(target_conn)

        results = []
        
        # 处理忽略表配置
        ignored_tables = []
        ignored_prefixes = []
        
        if config and 'ignored_tables' in config:
            # 处理具体表名忽略
            if 'exact' in config['ignored_tables'] and isinstance(config['ignored_tables']['exact'], list):
                ignored_tables = config['ignored_tables']['exact']
            
            # 处理表名前缀忽略
            if 'prefixes' in config['ignored_tables'] and isinstance(config['ignored_tables']['prefixes'], list):
                ignored_prefixes = config['ignored_tables']['prefixes']

        # 比较表是否存在
        all_tables = set(source_tables.keys()) | set(target_tables.keys())
        
        # 过滤掉需要忽略的表
        filtered_tables = set()
        for table_name in all_tables:
            # 检查是否在忽略表列表中
            if table_name in ignored_tables:
                continue
                
            # 检查是否匹配忽略前缀
            should_ignore = False
            for prefix in ignored_prefixes:
                if table_name.startswith(prefix):
                    should_ignore = True
                    break
                    
            if not should_ignore:
                filtered_tables.add(table_name)
        
        # 使用过滤后的表集合
        all_tables = filtered_tables

        for table_name in all_tables:
            source_exists = table_name in source_tables
            target_exists = table_name in target_tables

            if not source_exists:
                # 表在目标数据库存在但在源数据库不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=table_name,
                    has_differences=True,
                    source_definition=None,
                    target_definition=target_tables[table_name],
                    difference_details={
                        "type": "missing_in_source",
                        "message": f"表 {table_name} 在源数据库中不存在",
                    },
                    change_sql=f"DROP TABLE IF EXISTS `{table_name}`;",
                )
                results.append(result)
                continue

            if not target_exists:
                # 表在源数据库存在但在目标数据库不存在
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=table_name,
                    has_differences=True,
                    source_definition=source_tables[table_name],
                    target_definition=None,
                    difference_details={
                        "type": "missing_in_target",
                        "message": f"表 {table_name} 在目标数据库中不存在",
                    },
                    change_sql=source_tables[table_name],
                )
                results.append(result)
                continue

            # 比较表结构
            source_columns = _get_table_columns(source_conn, table_name)
            target_columns = _get_table_columns(target_conn, table_name)

            source_indexes = _get_table_indexes(source_conn, table_name)
            target_indexes = _get_table_indexes(target_conn, table_name)

            source_constraints = _get_table_constraints(source_conn, table_name)
            target_constraints = _get_table_constraints(target_conn, table_name)

            differences = self._compare_table_details(
                table_name,
                source_columns,
                target_columns,
                source_indexes,
                target_indexes,
                source_constraints,
                target_constraints,
            )

            if differences:
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=table_name,
                    has_differences=True,
                    source_definition=source_tables[table_name],
                    target_definition=target_tables[table_name],
                    difference_details=differences,
                    change_sql=_generate_table_change_sql(table_name, differences),
                )
                results.append(result)
            else:
                result = self._create_result(
                    task_log_id=task_log_id,
                    object_name=table_name,
                    has_differences=False,
                    source_definition=source_tables[table_name],
                    target_definition=target_tables[table_name],
                )
                results.append(result)

        return results
