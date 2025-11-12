"""
数据库初始化模块测试
测试数据库初始化脚本的功能和可靠性
"""

import unittest
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.utils.db_init import (
    init_database,
    create_database_if_not_exists,
    create_tables,
    drop_all_tables,
    get_db_connection_stats,
    init_db
)
from app.config import settings
from app.database import Base, engine


class TestDatabaseInitialization(unittest.TestCase):
    """测试数据库初始化功能"""
    
    def setUp(self):
        """测试前的设置"""
        self.original_environment = settings.ENVIRONMENT
        settings.ENVIRONMENT = "development"
    
    def tearDown(self):
        """测试后的清理"""
        settings.ENVIRONMENT = self.original_environment
    
    @patch('app.utils.db_init.create_engine')
    def test_create_database_if_not_exists_success(self, mock_create_engine):
        """测试数据库创建成功的情况"""
        # 模拟连接和执行结果
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        # 第一次查询返回None表示数据库不存在
        mock_conn.execute.return_value.fetchone.return_value = None
        
        # 执行函数
        result = create_database_if_not_exists()
        
        # 验证结果
        self.assertTrue(result)
        mock_create_engine.assert_called_once()
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called_once()
    
    @patch('app.utils.db_init.create_engine')
    def test_create_database_if_not_exists_already_exists(self, mock_create_engine):
        """测试数据库已存在的情况"""
        # 模拟连接和执行结果
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        # 返回非None表示数据库已存在
        mock_conn.execute.return_value.fetchone.return_value = (settings.MYSQL_DATABASE,)
        
        # 执行函数
        result = create_database_if_not_exists()
        
        # 验证结果
        self.assertTrue(result)
        mock_create_engine.assert_called_once()
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_not_called()  # 数据库已存在，不应该调用commit
    
    @patch('app.utils.db_init.create_engine')
    def test_create_database_if_not_exists_error(self, mock_create_engine):
        """测试数据库创建失败的情况"""
        # 模拟连接失败
        mock_create_engine.side_effect = Exception("连接失败")
        
        # 执行函数 - 应该继续执行而不是抛出异常
        result = create_database_if_not_exists()
        
        # 验证结果
        self.assertFalse(result)
    
    @patch('app.utils.db_init.Base')
    def test_create_tables_success(self, mock_base):
        """测试创建数据表成功的情况"""
        # 模拟Base.metadata
        mock_metadata = MagicMock()
        mock_metadata.sorted_tables = []
        mock_base.metadata = mock_metadata
        
        # 执行函数
        result = create_tables()
        
        # 验证结果
        self.assertTrue(result)
        mock_metadata.create_all.assert_called_once_with(bind=engine)
    
    @patch('app.utils.db_init.Base')
    def test_create_tables_error(self, mock_base):
        """测试创建数据表失败的情况"""
        # 模拟Base.metadata并设置异常
        mock_metadata = MagicMock()
        mock_metadata.sorted_tables = []
        mock_metadata.create_all.side_effect = Exception("创建表失败")
        mock_base.metadata = mock_metadata
        
        # 执行函数 - 应该抛出异常
        with self.assertRaises(Exception):
            create_tables()
    
    def test_drop_all_tables_development(self):
        """测试在开发环境中删除数据表"""
        # 确保环境设置为开发环境
        settings.ENVIRONMENT = "development"
        
        with patch('app.utils.db_init.Base.metadata') as mock_metadata:
            # 执行函数
            result = drop_all_tables()
            
            # 验证结果
            self.assertTrue(result)
            mock_metadata.drop_all.assert_called_once()
    
    def test_drop_all_tables_production(self):
        """测试在生产环境中禁止删除数据表"""
        # 设置环境为生产环境
        settings.ENVIRONMENT = "production"
        
        # 执行函数 - 应该抛出异常
        with self.assertRaises(RuntimeError):
            drop_all_tables()
    
    @patch('app.utils.db_init.engine')
    def test_get_db_connection_stats_success(self, mock_engine):
        """测试获取数据库连接统计信息成功的情况"""
        # 模拟连接和执行结果
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_engine.pool.size.return_value = 5
        mock_engine.pool.overflow.return_value = 0
        mock_engine.pool.checkedout.return_value = 1
        
        # 模拟表查询结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("users",), ("matches",)]
        mock_conn.execute.return_value = mock_result
        
        # 执行函数
        stats = get_db_connection_stats()
        
        # 验证结果
        self.assertIsNotNone(stats)
        self.assertEqual(stats["pool_size"], 5)
        self.assertEqual(stats["pool_overflow"], 0)
        self.assertEqual(stats["pool_checkout"], 1)
        self.assertEqual(stats["table_count"], 2)
        self.assertEqual(stats["tables"], ["users", "matches"])
    
    @patch('app.utils.db_init.engine')
    def test_get_db_connection_stats_error(self, mock_engine):
        """测试获取数据库连接统计信息失败的情况"""
        # 模拟连接失败
        mock_engine.connect.side_effect = Exception("连接失败")
        
        # 执行函数
        stats = get_db_connection_stats()
        
        # 验证结果
        self.assertIsNone(stats)
    
    @patch('app.utils.db_init.init_database')
    def test_init_db_compatibility(self, mock_init_database):
        """测试init_db函数的兼容性"""
        # 设置模拟返回值
        mock_init_database.return_value = True
        
        # 执行函数
        result = init_db()
        
        # 验证结果
        self.assertTrue(result)
        mock_init_database.assert_called_once()
    
    @patch('app.utils.db_init.create_database_if_not_exists')
    @patch('app.utils.db_init.create_tables')
    def test_init_database_full_flow(self, mock_create_tables, mock_create_database):
        """测试完整的数据库初始化流程"""
        # 设置模拟返回值
        mock_create_database.return_value = True
        mock_create_tables.return_value = True
        
        # 执行函数
        result = init_database()
        
        # 验证结果
        self.assertTrue(result)
        mock_create_database.assert_called_once()
        mock_create_tables.assert_called_once()


if __name__ == '__main__':
    unittest.main()