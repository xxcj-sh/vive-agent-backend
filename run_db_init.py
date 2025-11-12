"""
数据库初始化执行脚本
用于手动触发数据库初始化过程
"""

import logging
import sys
from app.utils.db_init import init_database, get_db_connection_stats

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_init')

def main():
    """主函数"""
    logger.info("开始数据库初始化...")
    
    try:
        # 执行数据库初始化
        success = init_database()
        
        if success:
            logger.info("数据库初始化成功！")
            
            # 获取并显示数据库连接统计信息
            logger.info("获取数据库统计信息...")
            stats = get_db_connection_stats()
            
            if stats:
                logger.info(f"数据库表数量: {stats['table_count']}")
                logger.info(f"创建的表: {', '.join(stats['tables'])}")
                logger.info(f"连接池大小: {stats['pool_size']}")
                logger.info(f"连接池溢出: {stats['pool_overflow']}")
                logger.info(f"已检出连接数: {stats['pool_checkout']}")
            else:
                logger.warning("无法获取数据库统计信息")
                
            return 0
        else:
            logger.error("数据库初始化失败")
            return 1
            
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())