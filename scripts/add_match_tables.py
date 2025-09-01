#!/usr/bin/env python3
"""
添加匹配操作和匹配结果表的迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import DATABASE_URL
from app.utils.db_config import Base
from app.models.match_action import MatchAction, MatchResult

def create_match_tables():
    """创建匹配相关的新表"""
    engine = create_engine(DATABASE_URL)
    
    try:
        # 创建新表
        MatchAction.__table__.create(engine, checkfirst=True)
        MatchResult.__table__.create(engine, checkfirst=True)
        
        print("✅ 匹配操作表 (match_actions) 创建成功")
        print("✅ 匹配结果表 (match_results) 创建成功")
        
        # 验证表是否创建成功
        with engine.connect() as conn:
            # 检查 match_actions 表
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='match_actions'"))
            if result.fetchone():
                print("✅ match_actions 表验证成功")
            else:
                print("❌ match_actions 表创建失败")
            
            # 检查 match_results 表
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='match_results'"))
            if result.fetchone():
                print("✅ match_results 表验证成功")
            else:
                print("❌ match_results 表创建失败")
                
    except Exception as e:
        print(f"❌ 创建表时发生错误: {str(e)}")
        raise

def show_table_structure():
    """显示新创建表的结构"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("\n📋 match_actions 表结构:")
            result = conn.execute(text("PRAGMA table_info(match_actions)"))
            for row in result:
                print(f"  - {row[1]} ({row[2]}) {'NOT NULL' if row[3] else 'NULL'} {'PRIMARY KEY' if row[5] else ''}")
            
            print("\n📋 match_results 表结构:")
            result = conn.execute(text("PRAGMA table_info(match_results)"))
            for row in result:
                print(f"  - {row[1]} ({row[2]}) {'NOT NULL' if row[3] else 'NULL'} {'PRIMARY KEY' if row[5] else ''}")
                
    except Exception as e:
        print(f"❌ 查看表结构时发生错误: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始创建匹配相关表...")
    create_match_tables()
    show_table_structure()
    print("\n✅ 匹配表迁移完成！")