#!/usr/bin/env python3
"""
数据库初始化脚本
用于快速初始化数据库表结构
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.config import settings
from app.database import Base
from app.models import *
import warnings

# 忽略SQLAlchemy警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    
    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    print(f"连接到数据库: {settings.DATABASE_URL.split('@')[-1]}")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n数据库中共有 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("数据库初始化脚本")
    print("=" * 50)
    
    # 检查是否有环境变量跳过确认（用于自动化）
    if os.environ.get('SKIP_CONFIRMATION') != 'true':
        print("⚠️  此操作将创建所有数据库表（如果已存在则跳过）")
        confirmation = input("请输入 'yes' 确认要继续: ")
        if confirmation.lower() != 'yes':
            print("操作已取消")
            return
    
    success = init_database()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 数据库初始化成功！")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ 数据库初始化失败！")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()