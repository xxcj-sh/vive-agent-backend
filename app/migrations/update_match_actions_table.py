"""
更新 match_actions 和 match_results 表结构

迁移内容：
1. 添加新字段支持AI推荐和系统操作
2. 优化索引提升查询性能  
3. 扩展字段类型支持更多数据
4. 添加状态管理字段

执行命令：
alembic revision --autogenerate -m "update match_actions table structure"
alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_match_actions_2024'
down_revision = 'update_user_card_table'
branch_labels = None
depends_on = None


def upgrade():
    """执行数据库升级操作"""
    
    # 更新 MatchAction 表
    # 1. 扩展现有字段类型
    op.alter_column('match_actions', 'scene_context',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=True)
    
    # 2. 添加新字段
    op.add_column('match_actions', sa.Column('source', sa.String(length=20), nullable=False, server_default='user'))
    op.add_column('match_actions', sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('match_actions', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('match_actions', sa.Column('metadata', sa.Text(), nullable=True))
    
    # 3. 创建复合索引
    op.create_index('idx_user_scene_created', 'match_actions', ['user_id', 'scene_type', 'created_at'])
    op.create_index('idx_target_user_scene', 'match_actions', ['target_user_id', 'scene_type', 'created_at'])
    op.create_index('idx_action_type_scene', 'match_actions', ['action_type', 'scene_type'])
    op.create_index('idx_created_at', 'match_actions', ['created_at'])
    op.create_index('idx_source_processed', 'match_actions', ['source', 'is_processed'])
    
    # 更新 MatchResult 表
    # 1. 添加新字段
    op.add_column('match_results', sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('match_results', sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True))
    
    # 2. 扩展现有状态枚举
    op.execute("""
        ALTER TYPE matchresultstatus ADD VALUE IF NOT EXISTS 'blocked';
    """)
    
    # 3. 创建复合索引
    op.create_index('idx_user1_scene_active', 'match_results', ['user1_id', 'scene_type', 'is_active'])
    op.create_index('idx_user2_scene_active', 'match_results', ['user2_id', 'scene_type', 'is_active'])
    op.create_index('idx_status_active', 'match_results', ['status', 'is_active'])
    op.create_index('idx_matched_at', 'match_results', ['matched_at'])
    op.create_index('idx_last_activity', 'match_results', ['last_activity_at'])
    op.create_index('idx_expiry_date', 'match_results', ['expiry_date'])


def downgrade():
    """执行数据库回滚操作"""
    
    # 回滚 MatchAction 表
    op.drop_index('idx_source_processed', table_name='match_actions')
    op.drop_index('idx_created_at', table_name='match_actions')
    op.drop_index('idx_action_type_scene', table_name='match_actions')
    op.drop_index('idx_target_user_scene', table_name='match_actions')
    op.drop_index('idx_user_scene_created', table_name='match_actions')
    
    op.drop_column('match_actions', 'metadata')
    op.drop_column('match_actions', 'processed_at')
    op.drop_column('match_actions', 'is_processed')
    op.drop_column('match_actions', 'source')
    
    op.alter_column('match_actions', 'scene_context',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    
    # 回滚 MatchResult 表
    op.drop_index('idx_expiry_date', table_name='match_results')
    op.drop_index('idx_last_activity', table_name='match_results')
    op.drop_index('idx_matched_at', table_name='match_results')
    op.drop_index('idx_status_active', table_name='match_results')
    op.drop_index('idx_user2_scene_active', table_name='match_results')
    op.drop_index('idx_user1_scene_active', table_name='match_results')
    
    op.drop_column('match_results', 'expiry_date')
    op.drop_column('match_results', 'is_blocked')