#!/usr/bin/env python3
"""
数据库迁移脚本：将model_name字段重命名为llm_model_name
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal, engine
from sqlalchemy import text
from app.models.llm_usage_log import LLMUsageLog

def migrate_model_name_field():
    """迁移model_name字段为llm_model_name"""
    print("🔍 开始数据库字段迁移...")
    
    try:
        db = SessionLocal()
        
        # 检查表是否存在
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_usage_logs'"))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print("ℹ️  llm_usage_logs表不存在，无需迁移")
            return
        
        # 检查字段是否存在
        result = db.execute(text("PRAGMA table_info(llm_usage_logs)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'llm_model_name' in columns and 'model_name' not in columns:
            print("✅ 字段已经迁移完成")
            return
        
        if 'model_name' in columns and 'llm_model_name' not in columns:
            # 添加新字段
            print("🔄 添加llm_model_name字段...")
            db.execute(text("ALTER TABLE llm_usage_logs ADD COLUMN llm_model_name VARCHAR"))
            
            # 复制数据
            print("🔄 复制数据到新字段...")
            db.execute(text("UPDATE llm_usage_logs SET llm_model_name = model_name"))
            
            # 删除旧字段（SQLite不支持直接删除，需要创建新表）
            print("⚠️  SQLite不支持直接删除字段，保留model_name作为兼容字段")
            
        elif 'model_name' in columns and 'llm_model_name' in columns:
            # 两个字段都存在，同步数据
            print("🔄 同步字段数据...")
            db.execute(text("UPDATE llm_usage_logs SET llm_model_name = model_name WHERE llm_model_name IS NULL"))
        
        db.commit()
        print("✅ 字段迁移完成")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_model_name_field()