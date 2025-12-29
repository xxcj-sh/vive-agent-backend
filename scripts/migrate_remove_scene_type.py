#!/usr/bin/env python3
"""
数据库迁移脚本：移除user_cards表中的scene_type字段
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_column_exists():
    """检查scene_type列是否存在"""
    try:
        engine = create_engine(settings.computed_database_url)
        with engine.connect() as conn:
            # 检查列是否存在
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'user_cards' 
                AND COLUMN_NAME = 'scene_type'
            """))
            exists = result.fetchone() is not None
            logger.info(f"scene_type列存在: {exists}")
            return exists
    except Exception as e:
        logger.error(f"检查列存在失败: {e}")
        return False

def remove_scene_type_column():
    """移除scene_type列"""
    try:
        engine = create_engine(settings.computed_database_url)
        with engine.connect() as conn:
            logger.info("开始移除user_cards表的scene_type列...")
            
            # 移除列（MySQL不支持IF EXISTS语法，需要先检查）
            conn.execute(text("ALTER TABLE user_cards DROP COLUMN scene_type"))
            conn.commit()
            
            logger.info("✅ scene_type列移除成功")
            return True
            
    except Exception as e:
        logger.error(f"移除scene_type列失败: {e}")
        return False

def remove_related_indexes():
    """移除与scene_type相关的索引"""
    try:
        engine = create_engine(settings.computed_database_url)
        with engine.connect() as conn:
            logger.info("移除与scene_type相关的索引...")
            
            # 获取数据库名
            db_result = conn.execute(text("SELECT DATABASE()"))
            db_name = db_result.fetchone()[0]
            
            # 查找包含scene_type的索引
            result = conn.execute(text("""
                SELECT DISTINCT INDEX_NAME 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'user_cards'
                AND COLUMN_NAME = 'scene_type'
            """), {"db_name": db_name})
            
            indexes = result.fetchall()
            for index in indexes:
                index_name = index[0]
                if index_name != 'PRIMARY':  # 不删除主键索引
                    logger.info(f"移除索引: {index_name}")
                    conn.execute(text(f"DROP INDEX {index_name} ON user_cards"))
            
            conn.commit()
            logger.info("✅ 相关索引移除完成")
            return True
            
    except Exception as e:
        logger.error(f"移除相关索引失败: {e}")
        return False

def verify_migration():
    """验证迁移结果"""
    try:
        engine = create_engine(settings.computed_database_url)
        with engine.connect() as conn:
            # 检查列是否还存在
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'user_cards' 
                AND COLUMN_NAME = 'scene_type'
            """))
            exists = result.fetchone() is not None
            
            if not exists:
                logger.info("✅ 验证通过: scene_type列已成功移除")
                return True
            else:
                logger.error("❌ 验证失败: scene_type列仍然存在")
                return False
                
    except Exception as e:
        logger.error(f"验证迁移失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始数据库迁移 - 移除scene_type字段")
    
    # 检查列是否存在
    if not check_column_exists():
        logger.info("scene_type列不存在，无需迁移")
        return
    
    # 移除相关索引
    if not remove_related_indexes():
        logger.error("移除相关索引失败")
        return
    
    # 移除列
    if not remove_scene_type_column():
        logger.error("移除scene_type列失败")
        return
    
    # 验证迁移
    if verify_migration():
        logger.info("🎉 数据库迁移成功完成!")
    else:
        logger.error("❌ 数据库迁移验证失败")

if __name__ == "__main__":
    main()