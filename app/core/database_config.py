"""
数据库配置模块
提供MySQL数据库连接和配置管理
"""

import os
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
import logging

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置类 - 支持MySQL"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库配置
        
        Args:
            db_url: 数据库连接URL，如果为None则自动检测
        """
        self.db_url = db_url or self._get_default_database_url()
        self.connection_params = {
            'charset': 'utf8mb4',
            'autocommit': True,
            'connect_timeout': 30,
        }
    
    def _get_default_database_url(self) -> str:
        """获取默认数据库URL"""
        # 优先使用环境变量
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # MySQL配置
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        mysql_user = os.getenv("MYSQL_USERNAME", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "")
        mysql_database = os.getenv("MYSQL_DATABASE", "vmatch_dev")
        
        if mysql_password:
            return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        else:
            return f"mysql+pymysql://{mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}"
    
    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return self.db_url
    
    def database_exists(self) -> bool:
        """检查数据库是否存在"""
        # MySQL需要通过连接测试
        try:
            connection = pymysql.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                user=os.getenv("MYSQL_USERNAME", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DATABASE", "vmatch_dev"),
                connect_timeout=5
            )
            connection.close()
            return True
        except Exception:
            return False
    
    def get_db_size(self) -> int:
        """获取数据库大小（字节）"""
        # MySQL数据库大小查询
        try:
            connection = pymysql.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                user=os.getenv("MYSQL_USERNAME", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DATABASE", "vmatch_dev"),
                connect_timeout=5
            )
            cursor = connection.cursor()
            cursor.execute("SELECT SUM(data_length + index_length) FROM information_schema.tables WHERE table_schema = DATABASE()")
            size = cursor.fetchone()[0] or 0
            cursor.close()
            connection.close()
            return size
        except Exception:
            return 0
    
    def get_db_size_mb(self) -> float:
        """获取数据库大小（MB）"""
        return self.get_db_size() / (1024 * 1024)

class DatabaseManager:
    """数据库管理器 - 支持MySQL"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置对象
        """
        self.config = config
        self._sqlalchemy_engine = None
        self._sqlalchemy_session = None
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            pymysql.Connection: 数据库连接对象
        """
        yield from self._get_mysql_connection()
    

    
    def _get_mysql_connection(self):
        """获取MySQL连接"""
        
        conn = None
        try:
            # 解析数据库URL
            import re
            pattern = r'mysql\+pymysql://([^:@]+)(?::([^@]+))?@([^:]+):(\d+)/(\w+)'
            match = re.match(pattern, self.config.db_url)
            
            if not match:
                raise ValueError(f"无效的MySQL URL格式: {self.config.db_url}")
            
            user, password, host, port, database = match.groups()
            
            conn = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password or '',
                database=database,
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=30
            )
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @property
    def sqlalchemy_engine(self):
        """获取SQLAlchemy引擎（用于高级操作）"""
        if self._sqlalchemy_engine is None:
            self._sqlalchemy_engine = create_engine(self.config.db_url)
        
        return self._sqlalchemy_engine
    
    @property
    def sqlalchemy_session(self):
        """获取SQLAlchemy会话"""
        if self._sqlalchemy_session is None:
            Session = sessionmaker(bind=self.sqlalchemy_engine)
            self._sqlalchemy_session = Session()
        
        return self._sqlalchemy_session
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            list: 查询结果
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # MySQL使用 %s 作为参数占位符
            query = query.replace("?", "%s")
            
            cursor.execute(query, params)
            
            # MySQL返回字典列表
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新语句（INSERT, UPDATE, DELETE）
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            int: 影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # MySQL使用 %s 作为参数占位符
            query = query.replace("?", "%s")
            
            cursor.execute(query, params)
            return cursor.rowcount
    
    def get_table_info(self, table_name: str) -> list:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            list: 表结构信息
        """
        query = """
            SELECT 
                COLUMN_NAME as name,
                DATA_TYPE as type,
                IS_NULLABLE as [notnull],
                COLUMN_DEFAULT as dflt_value,
                CASE WHEN COLUMN_KEY = 'PRI' THEN 1 ELSE 0 END as pk
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, (table_name,))
    
    def get_all_tables(self) -> list:
        """
        获取所有表名
        
        Returns:
            list: 表名列表
        """
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'"
        return [row['TABLE_NAME'] for row in self.execute_query(query)]
    
    def get_all_indexes(self) -> list:
        """
        获取所有索引名
        
        Returns:
            list: 索引名列表
        """
        query = "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() GROUP BY INDEX_NAME"
        return [row['INDEX_NAME'] for row in self.execute_query(query)]
    
    def get_database_stats(self) -> dict:
        """
        获取数据库统计信息
        
        Returns:
            dict: 数据库统计信息
        """
        stats = {
            'db_type': 'mysql',
            'db_url': self.config.db_url,
            'db_exists': self.config.database_exists(),
            'db_size_bytes': self.config.get_db_size(),
            'db_size_mb': round(self.config.get_db_size_mb(), 2),
        }
        
        if self.config.database_exists():
            # 获取表统计
            tables = self.get_all_tables()
            stats['table_count'] = len(tables)
            stats['tables'] = {}
            
            for table in tables:
                count_query = f"SELECT COUNT(*) FROM `{table}`"
                result = self.execute_query(count_query)
                if result and len(result) > 0:
                    count = result[0].get('COUNT(*)', 0) if isinstance(result[0], dict) else result[0][0]
                    stats['tables'][table] = count
            
            # 获取索引统计
            indexes = self.get_all_indexes()
            stats['index_count'] = len(indexes)
            stats['indexes'] = indexes
        
        return stats

# 全局数据库配置实例
default_config = DatabaseConfig()
default_manager = DatabaseManager(default_config)

def get_db_manager(db_url: Optional[str] = None) -> DatabaseManager:
    """获取数据库管理器
    
    Args:
        db_url: 数据库连接URL，如果为None使用默认配置
        
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    if db_url is None:
        return default_manager
    else:
        config = DatabaseConfig(db_url)
        return DatabaseManager(config)

def get_db_config(db_url: Optional[str] = None) -> DatabaseConfig:
    """获取数据库配置
    
    Args:
        db_url: 数据库连接URL，如果为None使用默认配置
        
    Returns:
        DatabaseConfig: 数据库配置实例
    """
    if db_url is None:
        return default_config
    else:
        return DatabaseConfig(db_url)