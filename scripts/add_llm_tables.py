#!/usr/bin/env python3
"""
添加大语言模型相关表
运行此脚本创建llm_usage_logs表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.llm_usage_log import LLMUsageLog
from app.config import settings

def add_llm_tables():
    """添加LLM相关表"""
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        
        # 检查表是否已存在
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"当前数据库: {settings.DATABASE_URL}")
        print(f"现有表: {existing_tables}")
        
        # 创建LLM使用日志表
        if 'llm_usage_logs' not in existing_tables:
            print("正在创建llm_usage_logs表...")
            LLMUsageLog.__table__.create(engine)
            print("✅ llm_usage_logs表创建成功")
        else:
            print("ℹ️ llm_usage_logs表已存在，跳过创建")
        
        # 验证表创建
        inspector = inspect(engine)
        updated_tables = inspector.get_table_names()
        print(f"更新后的表列表: {updated_tables}")
        
        if 'llm_usage_logs' in updated_tables:
            # 获取表结构
            columns = inspector.get_columns('llm_usage_logs')
            print("\nllm_usage_logs表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        
        print("\n🎉 LLM相关表初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_llm_tables()