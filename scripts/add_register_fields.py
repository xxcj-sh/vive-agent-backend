#!/usr/bin/env python3
"""
数据库迁移脚本：添加register_at字段和更新status字段
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def migrate_database():
    """执行数据库迁移 - 适配SQLite语法"""
    
    # 创建数据库连接
    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # 添加register_at字段
            try:
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN register_at DATETIME;
                """))
                print("✅ register_at字段添加成功")
            except Exception as e:
                # 字段可能已经存在
                print(f"⚠️ register_at字段可能已存在: {e}")
            
            # 更新现有用户的status字段（如果为空）
            try:
                conn.execute(text("""
                    UPDATE users SET status = 'active' WHERE status IS NULL OR status = '';
                """))
                print("✅ 现有用户状态更新成功")
            except Exception as e:
                print(f"⚠️ 现有用户状态更新失败: {e}")
            
            # 为已激活的用户设置register_at（如果没有设置）
            try:
                conn.execute(text("""
                    UPDATE users SET register_at = created_at 
                    WHERE register_at IS NULL AND status = 'active';
                """))
                print("✅ 现有用户注册时间设置成功")
            except Exception as e:
                print(f"⚠️ 现有用户注册时间设置失败: {e}")
            
            # 更新status字段的默认值
            try:
                conn.execute(text("""
                    UPDATE users SET status = 'pending' WHERE status IS NULL;
                """))
                print("✅ status字段默认值更新成功")
            except Exception as e:
                print(f"⚠️ status字段默认值更新失败: {e}")
            
            # 提交事务
            conn.commit()
            print("🎉 数据库迁移完成！")
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始执行数据库迁移...")
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    # 确认迁移
    response = input("确认执行数据库迁移吗？(y/N): ")
    if response.lower() == 'y':
        success = migrate_database()
        if success:
            print("迁移脚本执行完成！")
        else:
            print("迁移脚本执行失败！")
            sys.exit(1)
    else:
        print("取消迁移")