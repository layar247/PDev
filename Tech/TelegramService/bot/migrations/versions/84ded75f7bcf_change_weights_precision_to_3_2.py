"""change weights precision to 3,2

Revision ID: 84ded75f7bcf
Revises: 
Create Date: 2026-04-23 19:26:53.863782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84ded75f7bcf'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('topics', 'weights',
               existing_type=sa.ARRAY(sa.NUMERIC(2, 1)),
               type_=sa.ARRAY(sa.NUMERIC(3, 2)),
               existing_nullable=True)

def downgrade() -> None:
    op.alter_column('topics', 'weights',
               existing_type=sa.ARRAY(sa.NUMERIC(3, 2)),
               type_=sa.ARRAY(sa.NUMERIC(2, 1)),
               existing_nullable=True)
