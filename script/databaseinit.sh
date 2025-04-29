#!/bin/bash

# 查看当前版本
alembic current

# 初始化
alembic init alembic

# 自动生成迁移脚本
alembic revision --autogenerate -m "init"

# 按 model 结构重建所有表
alembic upgrade head

# 清理
truncate table alembic_version;
drop table if exists results;
drop table if exists task_logs;
drop table if exists tasks;
drop table if exists connections;
drop table if exists users;

# 添加任务名称字段
alembic revision --autogenerate -m "add_password" && alembic upgrade head
