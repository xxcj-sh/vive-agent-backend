#!/usr/bin/env python3
"""
Test the final SQL file execution with proper statement parsing
"""
import sys
import os
import traceback
import re

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def execute_final_sql():
    """Execute the final SQL file"""
    print("🚀 执行最终SQL文件...")
    
    # Read the SQL file
    sql_file_path = "../user_data_generation_final.sql"
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"📖 成功读取SQL文件: {len(sql_content)} 字符")
    except Exception as e:
        print(f"❌ 读取SQL文件失败: {e}")
        return False
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            print("📝 开始执行SQL语句...")
            
            # Split SQL statements properly - handle multiline statements
            # Remove comments and split by semicolon
            cleaned_sql = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
            cleaned_sql = re.sub(r'/\*.*?\*/', '', cleaned_sql, flags=re.DOTALL)
            
            statements = []
            current_statement = ""
            
            for line in cleaned_sql.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_statement += line + "\n"
                    if line.endswith(';'):
                        statements.append(current_statement.strip())
                        current_statement = ""
            
            # Add any remaining statement
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            executed_count = 0
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        print(f"📝 执行: {statement[:100]}...")
                        result = conn.execute(text(statement))
                        executed_count += 1
                        print(f"✅ 执行成功，影响行数: {result.rowcount}")
                    except Exception as e:
                        print(f"❌ 执行失败: {statement[:100]}...")
                        print(f"   错误: {e}")
                        raise
            
            # Commit transaction
            trans.commit()
            print(f"✅ 事务提交成功，共执行 {executed_count} 条语句")
            
            return True
            
    except Exception as e:
        print(f"❌ SQL执行失败: {e}")
        if 'trans' in locals():
            trans.rollback()
        traceback.print_exc()
        return False

def verify_insertion():
    """Verify the data was inserted correctly"""
    print("\n🔍 验证数据插入结果...")
    try:
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE phone LIKE '2000%'"))
            user_count = result.fetchone()[0]
            print(f"📱 小红书用户数量: {user_count}")
            
            # Check user_cards table
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM user_cards uc 
                JOIN users u ON uc.user_id = u.id 
                WHERE u.phone LIKE '2000%' AND uc.role_type = 'social_assistant'
            """))
            card_count = result.fetchone()[0]
            print(f"📋 小红书用户卡片数量: {card_count}")
            
            # Show some sample data
            result = conn.execute(text("""
                SELECT u.phone, u.nick_name, uc.display_name, uc.bio 
                FROM users u 
                JOIN user_cards uc ON u.id = uc.user_id 
                WHERE u.phone LIKE '2000%' 
                ORDER BY u.phone 
                LIMIT 3
            """))
            samples = result.fetchall()
            
            print("\n📋 样本数据:")
            for sample in samples:
                print(f"   - {sample[0]}: {sample[1]} -> {sample[2]}")
                print(f"     简介: {sample[3][:50]}...")
            
            return user_count, card_count
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        traceback.print_exc()
        return 0, 0

def main():
    """Main function"""
    print("🚀 开始执行最终SQL测试")
    
    # Execute the SQL
    if execute_final_sql():
        # Verify the results
        user_count, card_count = verify_insertion()
        
        if user_count > 0 and card_count > 0:
            print(f"\n✅ 成功！插入了 {user_count} 个用户和 {card_count} 个用户卡片")
        else:
            print(f"\n⚠️  警告：数据插入可能不完整。用户: {user_count}, 卡片: {card_count}")
    else:
        print("\n❌ SQL执行失败")

if __name__ == "__main__":
    main()