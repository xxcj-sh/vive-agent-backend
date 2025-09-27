#!/usr/bin/env python3
"""
数据库迁移脚本：添加wechat_open_id字段到users表
"""

import sqlite3
import os
import sys

def add_wechat_open_id_field():
    """添加wechat_open_id字段到users表"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vmatch_dev.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'wechat_open_id' in columns:
            print("wechat_open_id字段已存在，无需添加")
            return True
        
        # 添加新字段
        print("正在添加wechat_open_id字段...")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN wechat_open_id VARCHAR(100)
        """)
        
        conn.commit()
        print("成功添加wechat_open_id字段")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"数据库操作错误: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False
    finally:
        if conn:
            conn.close()

def rollback_wechat_open_id_field():
    """回滚wechat_open_id字段（SQLite不支持直接删除字段，需要重建表）"""
    print("注意：SQLite不支持直接删除字段，如需回滚需要重建表")
    print("建议备份数据后手动处理")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_wechat_open_id_field()
    else:
        success = add_wechat_open_id_field()
        sys.exit(0 if success else 1)