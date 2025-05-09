"""add_task_name_unique

Revision ID: 81cff0d0585c
Revises: 603e484a97c1
Create Date: 2025-04-21 07:13:04.646681+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "81cff0d0585c"
down_revision: Union[str, None] = "603e484a97c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "tasks",
        "status",
        existing_type=mysql.ENUM(
            "PENDING",
            "RUNNING",
            "COMPLETED",
            "FAILED",
            collation="utf8mb4_general_ci",
        ),
        comment="任务状态",
        existing_nullable=False,
    )
    op.create_unique_constraint(None, "tasks", ["name"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "tasks", type_="unique")
    op.alter_column(
        "tasks",
        "status",
        existing_type=mysql.ENUM(
            "PENDING",
            "RUNNING",
            "COMPLETED",
            "FAILED",
            collation="utf8mb4_general_ci",
        ),
        comment=None,
        existing_comment="任务状态",
        existing_nullable=False,
    )
    # ### end Alembic commands ###
