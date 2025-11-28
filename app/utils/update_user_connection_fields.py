"""
用户连接表字段重命名脚本
将user_connections表中的requester_id字段重命名为from_user_id，addressee_id字段重命名为to_user_id
"""

import logging
from sqlalchemy import text, create_engine
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_user_connection_fields():
    """
    更新user_connections表的字段名
    """
    try:
        # 创建数据库连接
        db_url = f"mysql+pymysql://{settings.MYSQL_USERNAME}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # 开始事务
            transaction = conn.begin()
            
            try:
                # 检查表是否存在
                result = conn.execute(text("SHOW TABLES LIKE 'user_connections'"))
                if not result.fetchone():
                    logger.warning("user_connections表不存在，无需更新")
                    transaction.commit()
                    return True
                
                # 检查字段是否存在并执行重命名
                # 重命名requester_id为from_user_id
                conn.execute(text("ALTER TABLE user_connections CHANGE COLUMN requester_id from_user_id VARCHAR(36) NOT NULL"))
                logger.info("已将requester_id字段重命名为from_user_id")
                
                # 重命名addressee_id为to_user_id
                conn.execute(text("ALTER TABLE user_connections CHANGE COLUMN addressee_id to_user_id VARCHAR(36) NOT NULL"))
                logger.info("已将addressee_id字段重命名为to_user_id")
                
                # 提交事务
                transaction.commit()
                logger.info("字段重命名操作成功完成")
                return True
                
            except Exception as e:
                # 回滚事务
                transaction.rollback()
                logger.error(f"字段重命名操作失败: {str(e)}")
                raise
        
    except Exception as e:
        logger.error(f"更新数据库失败: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("开始更新user_connections表字段名...")
        update_user_connection_fields()
        logger.info("字段名更新完成")
    except Exception as e:
        logger.error(f"更新失败: {str(e)}")
        exit(1)
