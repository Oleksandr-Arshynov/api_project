"""add email

Revision ID: 52ca25eb76dc
Revises: a8ff8cd11f54
Create Date: 2024-04-05 11:02:13.878996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52ca25eb76dc'
down_revision: Union[str, None] = 'a8ff8cd11f54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.create_unique_constraint(None, 'users', ['email'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###
