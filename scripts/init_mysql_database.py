#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
用于创建和初始化MySQL数据库表结构
"""

import mysql.connector
import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_init.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.config = {
            'host': settings.MYSQL_HOST,
            'port': int(settings.MYSQL_PORT),
            'user': settings.MYSQL_USERNAME,
            'password': settings.MYSQL_PASSWORD,
            'charset': 'utf8mb4'
        }
        
    def connect(self, database: Optional[str] = None) -> bool:
        """连接数据库"""
        try:
            config = self.config.copy()
            if database:
                config['database'] = database
                
            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor()
            logger.info(f"成功连接到MySQL服务器: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("数据库连接已关闭")
    
    def execute_sql_file(self, sql_file_path: str) -> bool:
        """执行SQL文件"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            logger.info(f"正在执行SQL文件: {sql_file_path}")
            
            # 分割SQL语句
            statements = self._split_sql_statements(sql_content)
            
            for i, statement in enumerate(statements, 1):
                if not statement.strip():
                    continue
                    
                try:
                    logger.debug(f"执行第{i}条语句: {statement[:100]}...")
                    self.cursor.execute(statement)
                    
                    # 对于创建数据库语句，需要重新连接
                    if statement.upper().strip().startswith('CREATE DATABASE'):
                        self.connection.commit()
                        time.sleep(0.5)  # 等待数据库创建完成
                        
                except mysql.connector.Error as e:
                    # 忽略已存在的错误
                    if "already exists" in str(e) or "Unknown database" in str(e):
                        logger.info(f"跳过已存在的对象: {e}")
                    else:
                        logger.warning(f"执行SQL语句时出错: {e}")
                        logger.warning(f"语句内容: {statement[:200]}")
            
            self.connection.commit()
            logger.info("SQL文件执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行SQL文件时出错: {e}")
            return False
    
    def _split_sql_statements(self, sql_content: str) -> List[str]:
        """分割SQL语句"""
        statements = []
        current_statement = []
        lines = sql_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if line.startswith('--') or line.startswith('/*') or not line:
                continue
                
            current_statement.append(line)
            
            # 如果行以分号结尾，表示语句结束
            if line.endswith(';'):
                statements.append(' '.join(current_statement))
                current_statement = []
        
        # 添加最后一条语句（如果没有分号）
        if current_statement:
            statements.append(' '.join(current_statement))
            
        return statements
    
    def show_tables(self) -> List[str]:
        """显示所有表"""
        try:
            self.cursor.execute(f"USE {settings.MYSQL_DATABASE}")
            self.cursor.execute("SHOW TABLES")
            tables = [table[0] for table in self.cursor.fetchall()]
            return tables
        except mysql.connector.Error as e:
            logger.error(f"获取表列表失败: {e}")
            return []
    
    def show_views(self) -> List[str]:
        """显示所有视图"""
        try:
            self.cursor.execute(f"USE {settings.MYSQL_DATABASE}")
            self.cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            views = [view[0] for view in self.cursor.fetchall()]
            return views
        except mysql.connector.Error as e:
            logger.error(f"获取视图列表失败: {e}")
            return []
    
    def reset_database(self) -> bool:
        """重置数据库"""
        try:
            logger.warning("开始重置数据库...")
            
            # 删除数据库
            self.cursor.execute(f"DROP DATABASE IF EXISTS {settings.MYSQL_DATABASE}")
            logger.info(f"已删除数据库: {settings.MYSQL_DATABASE}")
            
            # 重新创建数据库
            self.cursor.execute(f"CREATE DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"已创建数据库: {settings.MYSQL_DATABASE}")
            
            self.connection.commit()
            return True
            
        except mysql.connector.Error as e:
            logger.error(f"重置数据库失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if not self.connect(settings.MYSQL_DATABASE):
                return False
                
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            
            if result and result[0] == 1:
                logger.info("✅ 数据库连接测试成功")
                return True
            else:
                logger.error("❌ 数据库连接测试失败")
                return False
                
        except mysql.connector.Error as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            return False
        finally:
            self.disconnect()

def init_mysql_database(sql_script_path: Optional[str] = None) -> bool:
    """
    初始化MySQL数据库
    
    Args:
        sql_script_path: SQL脚本文件路径，默认为当前目录下的init_mysql_db_for_test.sql
    """
    
    # 设置默认路径
    if sql_script_path is None:
        sql_script_path = str(Path(__file__).parent / "init_mysql_db_for_test.sql")
    
    logger.info("=" * 60)
    logger.info("开始MySQL数据库初始化")
    logger.info("=" * 60)
    logger.info(f"MySQL主机: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    logger.info(f"数据库名: {settings.MYSQL_DATABASE}")
    logger.info(f"用户名: {settings.MYSQL_USERNAME}")
    logger.info(f"SQL脚本路径: {sql_script_path}")
    
    # 检查SQL脚本文件是否存在
    if not os.path.exists(sql_script_path):
        logger.error(f"错误: SQL脚本文件不存在: {sql_script_path}")
        return False
    
    initializer = DatabaseInitializer()
    
    try:
        # 连接数据库（不指定具体数据库）
        if not initializer.connect():
            return False
        
        # 执行SQL文件
        if not initializer.execute_sql_file(sql_script_path):
            return False
        
        # 显示创建的表和视图
        tables = initializer.show_tables()
        views = initializer.show_views()
        
        logger.info("=" * 60)
        logger.info("MySQL数据库初始化完成！")
        logger.info("=" * 60)
        logger.info(f"创建的表数量: {len(tables)}")
        for table in sorted(tables):
            logger.info(f"  📋 {table}")
        
        logger.info(f"创建的视图数量: {len(views)}")
        for view in sorted(views):
            logger.info(f"  📊 {view}")
        
        return True
        
    except Exception as e:
        logger.error(f"初始化过程中出错: {e}")
        return False
    finally:
        initializer.disconnect()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MySQL数据库初始化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python init_mysql_database.py                    # 初始化数据库
  python init_mysql_database.py --test           # 测试数据库连接
  python init_mysql_database.py --reset          # 重置数据库
  python init_mysql_database.py --sql-script custom.sql  # 使用自定义SQL文件
        """
    )
    
    parser.add_argument('--sql-script', type=str, help='SQL脚本文件路径')
    parser.add_argument('--test', action='store_true', help='测试数据库连接')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除所有表）')
    parser.add_argument('--force', action='store_true', help='强制重置（不询问确认）')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # 测试数据库连接
    if args.test:
        initializer = DatabaseInitializer()
        success = initializer.test_connection()
        sys.exit(0 if success else 1)
    
    # 重置数据库
    if args.reset:
        if not args.force:
            response = input("⚠️  确定要重置MySQL数据库吗？这将删除所有数据！(y/N): ")
            if response.lower() != 'y':
                logger.info("操作已取消")
                return
        
        initializer = DatabaseInitializer()
        try:
            if initializer.connect():
                if initializer.reset_database():
                    logger.info("✅ 数据库重置完成")
                else:
                    logger.error("❌ 数据库重置失败")
                    sys.exit(1)
            else:
                sys.exit(1)
        finally:
            initializer.disconnect()
        return
    
    # 初始化数据库
    success = init_mysql_database(args.sql_script)
    
    if success:
        logger.info("\n✅ MySQL数据库初始化成功！")
        logger.info("🎉 数据库已准备就绪，可以开始使用！")
    else:
        logger.error("\n❌ MySQL数据库初始化失败！")
        logger.error("请检查日志文件 database_init.log 获取详细信息")
        sys.exit(1)

if __name__ == "__main__":
    main()