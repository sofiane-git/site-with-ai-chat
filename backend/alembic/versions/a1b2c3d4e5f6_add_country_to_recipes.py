"""add country to recipes

Revision ID: a1b2c3d4e5f6
Revises: 93277b830c77
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '93277b830c77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recipes', sa.Column('country', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('recipes', 'country')
