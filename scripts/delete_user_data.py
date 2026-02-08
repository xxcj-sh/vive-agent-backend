"""
删除指定用户的所有数据
用法: python scripts/delete_user_data.py <user_id>
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 目标用户ID
TARGET_USER_ID = "a1be9a20-7a83-4b67-bb46-e7c9ebc90fcd"

# 需要删除的表，按依赖顺序排列（先删除子表，再删除父表）
# 格式: (表名, user_id字段名)
TABLES_TO_DELETE = [
    # 话题相关
    ("topic_opinion_summaries", "user_id"),
    ("topic_discussions", "participant_id"),
    ("topic_discussions", "host_id"),
    ("user_card_topic_relations", "user_id"),
    ("topic_cards", "user_id"),
    
    # 投票相关
    ("vote_records", "user_id"),
    ("vote_discussions", "participant_id"),
    ("vote_discussions", "host_id"),
    ("user_card_vote_relations", "user_id"),
    ("vote_cards", "user_id"),
    
    # 用户连接和社交关系
    ("user_connections", "from_user_id"),
    ("user_connections", "to_user_id"),
    
    # 标签相关
    ("user_tag_rel", "user_id"),
    ("user_tag_rel", "granted_by_user_id"),
    ("content_tag_interactions", "user_id"),

    # 用户资料相关
    ("user_profile_feedback", "user_id"),
    ("user_profile_scores", "user_id"),
    ("user_profile_histories", "user_id"),
    ("user_profiles", "user_id"),
    
    # 用户名片
    ("user_cards", "user_id"),
    
    # 聊天记录
    ("chat_messages", "user_id"),
    ("chat_messages", "user_id"),
    
    # LLM使用记录
    ("llm_usage_logs", "user_id"),
    
    # 订单
    ("orders", "user_id"),
    
    # 最后删除用户本身
    ("users", "id"),
]


def delete_user_data(user_id: str):
    """删除指定用户的所有数据"""
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print(f"开始删除用户 {user_id} 的所有数据...")
        print("-" * 60)
        
        deleted_counts = {}
        
        # 按顺序删除各表数据
        for table_name, column_name in TABLES_TO_DELETE:
            try:
                # 构建删除语句
                delete_sql = text(f"""
                    DELETE FROM {table_name} 
                    WHERE {column_name} = :user_id
                """)
                
                # 执行删除
                result = db.execute(delete_sql, {"user_id": user_id})
                deleted_count = result.rowcount
                
                if deleted_count > 0:
                    key = f"{table_name}.{column_name}"
                    deleted_counts[key] = deleted_count
                    print(f"✓ 删除 {table_name} ({column_name}): {deleted_count} 条记录")
                
            except Exception as e:
                print(f"✗ 删除 {table_name} 时出错: {str(e)}")
                # 继续处理其他表
        
        # 提交事务
        db.commit()
        
        print("-" * 60)
        print("删除完成!")
        print(f"总计删除记录数: {sum(deleted_counts.values())}")
        
        if deleted_counts:
            print("\n详细删除统计:")
            for key, count in sorted(deleted_counts.items()):
                print(f"  - {key}: {count} 条")
        else:
            print("\n未找到该用户的任何数据")
            
    except Exception as e:
        db.rollback()
        print(f"删除过程中发生错误: {str(e)}")
        raise
    finally:
        db.close()


def verify_deletion(user_id: str):
    """验证用户数据是否已完全删除"""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("\n验证删除结果...")
        print("-" * 60)
        
        remaining_counts = {}
        
        for table_name, column_name in TABLES_TO_DELETE:
            try:
                query_sql = text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE {column_name} = :user_id
                """)
                
                result = db.execute(query_sql, {"user_id": user_id})
                count = result.scalar()
                
                if count > 0:
                    key = f"{table_name}.{column_name}"
                    remaining_counts[key] = count
                    
            except Exception as e:
                print(f"检查 {table_name} 时出错: {str(e)}")
        
        if remaining_counts:
            print("⚠ 警告: 以下表中仍有该用户的数据:")
            for key, count in sorted(remaining_counts.items()):
                print(f"  - {key}: {count} 条")
            return False
        else:
            print("✓ 验证通过: 该用户的所有数据已完全删除")
            return True
            
    finally:
        db.close()


if __name__ == "__main__":
    # 可以使用命令行参数指定用户ID，否则使用默认的TARGET_USER_ID
    user_id = sys.argv[1] if len(sys.argv) > 1 else TARGET_USER_ID
    
    print(f"目标用户ID: {user_id}")
    print("=" * 60)
    
    # 确认提示
    confirm = input(f"确定要删除用户 {user_id} 的所有数据吗？此操作不可恢复！(yes/no): ")
    if confirm.lower() != "yes":
        print("操作已取消")
        sys.exit(0)
    
    # 执行删除
    delete_user_data(user_id)
    
    # 验证删除结果
    verify_deletion(user_id)
