"""empty message

Revision ID: 7c9858bf7573
Revises: acc172e057d2
Create Date: 2023-12-12 21:58:43.494581

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7c9858bf7573'
down_revision = 'acc172e057d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shows_table', schema=None) as batch_op:
        batch_op.alter_column('start_time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shows_table', schema=None) as batch_op:
        batch_op.alter_column('start_time',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)

    # ### end Alembic commands ###
