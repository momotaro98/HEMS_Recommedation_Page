"""add recommendationpage rows

Revision ID: 6762b21cc902
Revises: 456c7db545f9
Create Date: 2016-09-07 22:13:33.694792

"""

# revision identifiers, used by Alembic.
revision = '6762b21cc902'
down_revision = '456c7db545f9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recommendationpage', sa.Column('indoor_humidity', sa.Float(), nullable=True))
    op.add_column('recommendationpage', sa.Column('indoor_pressure', sa.Float(), nullable=True))
    op.add_column('recommendationpage', sa.Column('indoor_temperature', sa.Float(), nullable=True))
    op.add_column('recommendationpage', sa.Column('on_off', sa.String(length=64), nullable=True))
    op.add_column('recommendationpage', sa.Column('operate_ipaddress', sa.String(length=64), nullable=True))
    op.add_column('recommendationpage', sa.Column('operating', sa.String(length=64), nullable=True))
    op.add_column('recommendationpage', sa.Column('set_temperature', sa.Integer(), nullable=True))
    op.add_column('recommendationpage', sa.Column('wind', sa.String(length=64), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recommendationpage', 'wind')
    op.drop_column('recommendationpage', 'set_temperature')
    op.drop_column('recommendationpage', 'operating')
    op.drop_column('recommendationpage', 'operate_ipaddress')
    op.drop_column('recommendationpage', 'on_off')
    op.drop_column('recommendationpage', 'indoor_temperature')
    op.drop_column('recommendationpage', 'indoor_pressure')
    op.drop_column('recommendationpage', 'indoor_humidity')
    ### end Alembic commands ###
