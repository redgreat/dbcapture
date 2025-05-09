"""add_task_name_field

Revision ID: 603e484a97c1
Revises: 8b8d063ff7d8
Create Date: 2025-04-21 07:09:13.497193+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "603e484a97c1"
down_revision: Union[str, None] = "8b8d063ff7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tasks",
        sa.Column(
            "name", sa.String(length=50), nullable=False, comment="任务名称"
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "description",
            sa.String(length=200),
            nullable=True,
            comment="任务描述",
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tasks", "description")
    op.drop_column("tasks", "name")
    # ### end Alembic commands ###
