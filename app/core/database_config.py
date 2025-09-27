"""
数据库配置模块
提供SQLite数据库连接和配置管理
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库配置
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认数据库路径：项目根目录下的vmatch.db
            self.db_path = Path(__file__).parent.parent.parent / "vmatch.db"
        else:
            self.db_path = Path(db_path)
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 数据库连接参数
        self.connection_params = {
            'isolation_level': None,  # 自动提交模式
            'check_same_thread': False,  # 允许多线程访问
            'timeout': 30.0,  # 连接超时时间（秒）
        }
    
    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return str(self.db_path)
    
    def database_exists(self) -> bool:
        """检查数据库文件是否存在"""
        return self.db_path.exists()
    
    def get_db_size(self) -> int:
        """获取数据库文件大小（字节）"""
        if self.database_exists():
            return self.db_path.stat().st_size
        return 0
    
    def get_db_size_mb(self) -> float:
        """获取数据库文件大小（MB）"""
        return self.get_db_size() / (1024 * 1024)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置对象
        """
        self.config = config
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.config.get_connection_string(),
                **self.config.connection_params
            )
            # 设置外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置编码
            conn.execute("PRAGMA encoding = 'UTF-8'")
            # 设置缓存大小
            conn.execute("PRAGMA cache_size = -64000")  # 64MB缓存
            # 设置同步模式
            conn.execute("PRAGMA synchronous = NORMAL")
            # 设置日志模式
            conn.execute("PRAGMA journal_mode = WAL")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
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
            cursor.execute(query, params)
            return cursor.fetchall()
    
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
        query = "PRAGMA table_info({})".format(table_name)
        return self.execute_query(query)
    
    def get_all_tables(self) -> list:
        """
        获取所有表名
        
        Returns:
            list: 表名列表
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        return [row[0] for row in self.execute_query(query)]
    
    def get_all_indexes(self) -> list:
        """
        获取所有索引名
        
        Returns:
            list: 索引名列表
        """
        query = "SELECT name FROM sqlite_master WHERE type='index'"
        return [row[0] for row in self.execute_query(query)]
    
    def get_database_stats(self) -> dict:
        """
        获取数据库统计信息
        
        Returns:
            dict: 数据库统计信息
        """
        stats = {
            'db_path': str(self.config.db_path),
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
                count_query = f"SELECT COUNT(*) FROM {table}"
                count = self.execute_query(count_query)[0][0]
                stats['tables'][table] = count
            
            # 获取索引统计
            indexes = self.get_all_indexes()
            stats['index_count'] = len(indexes)
            stats['indexes'] = indexes
        
        return stats

# 全局数据库配置实例
default_config = DatabaseConfig()
default_manager = DatabaseManager(default_config)

def get_db_manager() -> DatabaseManager:
    """获取默认数据库管理器"""
    return default_manager

def get_db_config() -> DatabaseConfig:
    """获取默认数据库配置"""
    return default_config