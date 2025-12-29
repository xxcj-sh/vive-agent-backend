#!/usr/bin/env python3
"""
Test database connection and troubleshoot insertion issues
"""
import sys
import os
import traceback
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

def test_connection():
    """Test basic database connection"""
    print("🔍 测试数据库连接...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ 数据库连接成功: {result.fetchone()}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def check_existing_data():
    """Check existing data in users and user_cards tables"""
    print("\n🔍 检查现有数据...")
    try:
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
            user_count = result.fetchone()[0]
            print(f"📊 用户总数: {user_count}")
            
            # Check user_cards table
            result = conn.execute(text("SELECT COUNT(*) as count FROM user_cards"))
            card_count = result.fetchone()[0]
            print(f"📊 用户卡片总数: {card_count}")
            
            # Check for our specific phone numbers
            result = conn.execute(text("SELECT id, phone, nick_name FROM users WHERE phone LIKE '2000%'"))
            xiaohongshu_users = result.fetchall()
            print(f"📱 小红书用户 (2000*): {len(xiaohongshu_users)}")
            for user in xiaohongshu_users:
                print(f"   - ID: {user[0]}, Phone: {user[1]}, Name: {user[2]}")
                
            return user_count, card_count, len(xiaohongshu_users)
    except Exception as e:
        print(f"❌ 数据检查失败: {e}")
        traceback.print_exc()
        return 0, 0, 0

def test_single_insert():
    """Test inserting a single record with detailed logging"""
    print("\n🔍 测试单条数据插入...")
    
    # Test user data
    test_user_id = 'dc1e69b8-111a-41aa-84ba-5999a8e131d9'
    test_phone = '20000000009'
    test_name = '测试用户'
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            print(f"📝 插入测试用户: ID={test_user_id}, Phone={test_phone}, Name={test_name}")
            
            # Insert user
            insert_user_sql = text("""
                INSERT INTO users (id, phone, nick_name, created_at, updated_at, status, register_at) 
                VALUES (:id, :phone, :nick_name, NOW(), NOW(), 'active', NOW())
            """)
            
            result = conn.execute(insert_user_sql, {
                'id': test_user_id,
                'phone': test_phone,
                'nick_name': test_name
            })
            
            print(f"✅ 用户插入影响行数: {result.rowcount}")
            
            # Insert user card
            test_card_id = 'card_social_social_assistant_0009'
            insert_card_sql = text("""
                INSERT INTO user_cards (
                    id, user_id, role_type, scene_type, display_name, avatar_url, bio, profile_data, 
                    register_at, created_at, updated_at
                ) VALUES (
                    :id, :user_id, 'social_assistant', 'beauty', :display_name, 'avatar/test.jpg', 
                    '测试用户简介', '{"persona": "测试人设"}', NOW(), NOW(), NOW()
                )
            """)
            
            result = conn.execute(insert_card_sql, {
                'id': test_card_id,
                'user_id': test_user_id,
                'display_name': test_name
            })
            
            print(f"✅ 用户卡片插入影响行数: {result.rowcount}")
            
            # Commit transaction
            trans.commit()
            print("✅ 事务提交成功")
            
            # Verify insertion
            result = conn.execute(text("SELECT id, phone, nick_name FROM users WHERE id = :id"), {'id': test_user_id})
            user = result.fetchone()
            if user:
                print(f"✅ 验证用户插入成功: ID={user[0]}, Phone={user[1]}, Name={user[2]}")
            else:
                print("❌ 用户插入验证失败: 未找到记录")
                
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ SQL插入失败: {e}")
        if 'trans' in locals():
            trans.rollback()
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        if 'trans' in locals():
            trans.rollback()
        traceback.print_exc()
        return False

def check_table_structure():
    """Check table structure and constraints"""
    print("\n🔍 检查表结构...")
    try:
        with engine.connect() as conn:
            # Check users table structure
            result = conn.execute(text("DESCRIBE users"))
            users_structure = result.fetchall()
            print("📋 users表结构:")
            for field in users_structure:
                print(f"   - {field[0]}: {field[1]} {field[2]} {field[3]}")
                
            # Check user_cards table structure
            result = conn.execute(text("DESCRIBE user_cards"))
            cards_structure = result.fetchall()
            print("\n📋 user_cards表结构:")
            for field in cards_structure:
                print(f"   - {field[0]}: {field[1]} {field[2]} {field[3]}")
                
            return True
    except Exception as e:
        print(f"❌ 表结构检查失败: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 开始数据库连接和插入测试")
    print(f"⏰ 测试时间: {datetime.now()}")
    
    # Test connection
    if not test_connection():
        return
        
    # Check existing data
    user_count, card_count, xiaohongshu_count = check_existing_data()
    
    # Check table structure
    check_table_structure()
    
    # Test single insert
    if test_single_insert():
        print("\n✅ 单条插入测试完成，重新检查数据...")
        check_existing_data()
    
    print(f"\n🏁 测试完成时间: {datetime.now()}")

if __name__ == "__main__":
    main()