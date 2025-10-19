"""Add ADW tracking tables

Revision ID: 001
Revises:
Create Date: 2025-10-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add test_type column to test_cases table
    op.add_column('test_cases', sa.Column('test_type', sa.String(20), server_default='slash_command', nullable=True))

    # Create adw_tests table
    op.create_table(
        'adw_tests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('test_case_id', sa.String(36), sa.ForeignKey('test_cases.id'), nullable=False),
        sa.Column('adw_script_name', sa.String(200), nullable=False),
        sa.Column('python_version', sa.String(20), nullable=True),
        sa.Column('script_execution_status', sa.String(20), nullable=True),
        sa.Column('claude_execution_status', sa.String(20), nullable=True),
        sa.Column('dry_run', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('script_output_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('adw_test_id', sa.String(36), sa.ForeignKey('adw_tests.id'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    # Drop workflow_steps table
    op.drop_table('workflow_steps')

    # Drop adw_tests table
    op.drop_table('adw_tests')

    # Remove test_type column from test_cases
    op.drop_column('test_cases', 'test_type')
