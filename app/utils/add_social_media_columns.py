"""
用户表社交媒体字段迁移脚本
为users表添加小红书号、抖音号、微信公众号、小宇宙播客账号等字段
"""

import logging
from sqlalchemy import text, create_engine
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_social_media_columns():
    """
    为users表添加社交媒体字段
    """
    db_url = f"mysql+pymysql://{settings.MYSQL_USERNAME}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_engine(db_url)
    
    new_columns = [
        ("xiaohongshu_id", "VARCHAR(100) DEFAULT NULL COMMENT '小红书号'"),
        ("douyin_id", "VARCHAR(100) DEFAULT NULL COMMENT '抖音号'"),
        ("wechat_official_account", "VARCHAR(100) DEFAULT NULL COMMENT '微信公众号'"),
        ("xiaoyuzhou_id", "VARCHAR(100) DEFAULT NULL COMMENT '小宇宙播客账号'")
    ]
    
    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            
            try:
                for column_name, column_def in new_columns:
                    result = conn.execute(text(f"SHOW COLUMNS FROM users LIKE '{column_name}'"))
                    if not result.fetchone():
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                        logger.info(f"✅ 成功添加字段: {column_name}")
                    else:
                        logger.info(f"⏩ 字段 {column_name} 已存在，跳过")
                
                transaction.commit()
                logger.info("🎉 社交媒体字段迁移完成")
                return True
                
            except Exception as e:
                transaction.rollback()
                logger.error(f"❌ 字段添加失败: {str(e)}")
                raise
    
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("🚀 开始执行社交媒体字段迁移...")
        add_social_media_columns()
    except Exception as e:
        logger.error(f"💥 迁移失败: {str(e)}")
        exit(1)
