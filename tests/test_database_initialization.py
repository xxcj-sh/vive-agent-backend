#!/usr/bin/env python3
"""
数据库初始化测试
验证数据库初始化脚本的功能正确性
"""

import pytest
import mysql.connector
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.init_mysql_database import DatabaseInitializer, init_mysql_database
from app.config import settings


class TestDatabaseInitialization:
    """数据库初始化测试类"""
    
    @pytest.fixture
    def initializer(self):
        """创建数据库初始化器实例"""
        return DatabaseInitializer()
    
    @pytest.fixture
    def mock_connection(self):
        """创建模拟数据库连接"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor
    
    def test_database_initializer_creation(self, initializer):
        """测试数据库初始化器创建"""
        assert initializer is not None
        assert initializer.connection is None
        assert initializer.cursor is None
        assert 'host' in initializer.config
        assert 'port' in initializer.config
        assert 'user' in initializer.config
        assert 'password' in initializer.config
    
    @patch('mysql.connector.connect')
    def test_connect_success(self, mock_connect, initializer):
        """测试数据库连接成功"""
        # 设置模拟连接
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # 测试连接
        result = initializer.connect()
        
        # 验证结果
        assert result is True
        assert initializer.connection == mock_conn
        assert initializer.cursor == mock_cursor
        mock_connect.assert_called_once()
    
    @patch('mysql.connector.connect')
    def test_connect_failure(self, mock_connect, initializer):
        """测试数据库连接失败"""
        # 设置连接异常
        mock_connect.side_effect = mysql.connector.Error("连接失败")
        
        # 测试连接
        result = initializer.connect()
        
        # 验证结果
        assert result is False
        assert initializer.connection is None
        assert initializer.cursor is None
    
    def test_disconnect(self, initializer, mock_connection):
        """测试数据库断开连接"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 测试断开连接
        initializer.disconnect()
        
        # 验证结果 - 注意disconnect方法会设置connection和cursor为None
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    def test_split_sql_statements(self, initializer):
        """测试SQL语句分割功能"""
        sql_content = """
        CREATE TABLE users (
            id INT PRIMARY KEY
        );
        
        CREATE TABLE cards (
            id INT PRIMARY KEY
        );
        
        -- 注释行
        INSERT INTO users VALUES (1);
        """
        
        statements = initializer._split_sql_statements(sql_content)
        
        # 验证结果
        assert len(statements) == 3
        assert 'CREATE TABLE users' in statements[0]
        assert 'CREATE TABLE cards' in statements[1]
        assert 'INSERT INTO users' in statements[2]
    
    @patch('builtins.open', create=True)
    def test_execute_sql_file_success(self, mock_open, initializer, mock_connection):
        """测试SQL文件执行成功"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 模拟SQL文件内容
        sql_content = """
        CREATE TABLE test_table (
            id INT PRIMARY KEY
        );
        
        CREATE DATABASE test_db;
        """
        mock_open.return_value.__enter__.return_value.read.return_value = sql_content
        
        # 测试执行SQL文件
        result = initializer.execute_sql_file('test.sql')
        
        # 验证结果 - 注意execute_sql_file方法会多次调用commit
        assert result is True
        assert mock_cursor.execute.call_count >= 2  # 至少执行2条语句
        assert mock_conn.commit.call_count >= 1  # 至少提交1次
    
    @patch('builtins.open', create=True)
    def test_execute_sql_file_failure(self, mock_open, initializer, mock_connection):
        """测试SQL文件执行失败"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 模拟文件读取异常
        mock_open.side_effect = FileNotFoundError("文件不存在")
        
        # 测试执行SQL文件
        result = initializer.execute_sql_file('nonexistent.sql')
        
        # 验证结果
        assert result is False
    
    def test_show_tables(self, initializer, mock_connection):
        """测试显示表列表"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 模拟表列表
        mock_cursor.fetchall.return_value = [('users',), ('cards',), ('orders',)]
        
        # 测试显示表列表
        tables = initializer.show_tables()
        
        # 验证结果
        assert len(tables) == 3
        assert 'users' in tables
        assert 'cards' in tables
        assert 'orders' in tables
        mock_cursor.execute.assert_any_call(f"USE {settings.MYSQL_DATABASE}")
        mock_cursor.execute.assert_any_call("SHOW TABLES")
    
    def test_show_views(self, initializer, mock_connection):
        """测试显示视图列表"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 模拟视图列表
        mock_cursor.fetchall.return_value = [('user_statistics',), ('match_statistics',)]
        
        # 测试显示视图列表
        views = initializer.show_views()
        
        # 验证结果
        assert len(views) == 2
        assert 'user_statistics' in views
        assert 'match_statistics' in views
    
    def test_reset_database(self, initializer, mock_connection):
        """测试数据库重置"""
        mock_conn, mock_cursor = mock_connection
        initializer.connection = mock_conn
        initializer.cursor = mock_cursor
        
        # 测试重置数据库
        result = initializer.reset_database()
        
        # 验证结果
        assert result is True
        mock_cursor.execute.assert_any_call(f"DROP DATABASE IF EXISTS {settings.MYSQL_DATABASE}")
        mock_cursor.execute.assert_any_call(f"CREATE DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        mock_conn.commit.assert_called_once()
    
    def test_test_connection_success(self, initializer, mock_connection):
        """测试连接测试成功"""
        mock_conn, mock_cursor = mock_connection
        
        with patch.object(initializer, 'connect', return_value=True):
            with patch.object(initializer, 'disconnect') as mock_disconnect:
                mock_cursor.fetchone.return_value = (1,)
                initializer.connection = mock_conn
                initializer.cursor = mock_cursor
                
                # 测试连接测试
                result = initializer.test_connection()
                
                # 验证结果
                assert result is True
                mock_cursor.execute.assert_called_with("SELECT 1")
                mock_disconnect.assert_called_once()
    
    @patch('scripts.init_mysql_database.DatabaseInitializer')
    def test_init_mysql_database_success(self, mock_initializer_class):
        """测试数据库初始化函数成功"""
        # 设置模拟初始化器
        mock_initializer = MagicMock()
        mock_initializer_class.return_value = mock_initializer
        mock_initializer.connect.return_value = True
        mock_initializer.execute_sql_file.return_value = True
        mock_initializer.show_tables.return_value = ['users', 'user_cards']
        mock_initializer.show_views.return_value = ['user_statistics']
        
        # 测试初始化函数 - 使用实际的SQL文件路径
        with patch('os.path.exists', return_value=True):
            result = init_mysql_database('test.sql')
        
        # 验证结果
        assert result is True
        mock_initializer.connect.assert_called_once()
        mock_initializer.execute_sql_file.assert_called_once_with('test.sql')
        mock_initializer.show_tables.assert_called_once()
        mock_initializer.show_views.assert_called_once()
        mock_initializer.disconnect.assert_called_once()
    
    @patch('scripts.init_mysql_database.DatabaseInitializer')
    def test_init_mysql_database_failure(self, mock_initializer_class):
        """测试数据库初始化函数失败"""
        # 设置模拟初始化器
        mock_initializer = MagicMock()
        mock_initializer_class.return_value = mock_initializer
        mock_initializer.connect.return_value = False
        
        # 测试初始化函数 - 使用实际的SQL文件路径检查
        with patch('os.path.exists', return_value=True):
            result = init_mysql_database('test.sql')
        
        # 验证结果
        assert result is False
        mock_initializer.connect.assert_called_once()
        mock_initializer.disconnect.assert_called_once()
        mock_initializer.execute_sql_file.assert_not_called()


class TestDatabaseSchema:
    """数据库架构测试类"""
    
    @pytest.fixture
    def test_db_connection(self):
        """创建测试数据库连接"""
        try:
            conn = mysql.connector.connect(
                host=settings.MYSQL_HOST,
                port=int(settings.MYSQL_PORT),
                user=settings.MYSQL_USERNAME,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE
            )
            yield conn
            conn.close()
        except mysql.connector.Error:
            pytest.skip("数据库连接不可用")
    
    def test_database_connection(self, test_db_connection):
        """测试数据库连接"""
        cursor = test_db_connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result == (1,)
        cursor.close()
    
    def test_core_tables_exist(self, test_db_connection):
        """测试核心表是否存在"""
        cursor = test_db_connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        
        # 验证核心表存在
        core_tables = [
            'users', 'user_cards', 'user_profiles', 'match_actions',
            'match_results', 'chat_messages', 'llm_usage_logs',
            'membership_orders', 'subscribe_messages', 'user_subscribe_settings'
        ]
        
        for table in core_tables:
            assert table in tables, f"核心表 {table} 不存在"
    
    def test_table_columns(self, test_db_connection):
        """测试表字段完整性"""
        cursor = test_db_connection.cursor()
        
        # 测试users表字段 - 根据实际SQL结构调整
        cursor.execute("DESCRIBE users")
        user_columns = {col[0]: col[1] for col in cursor.fetchall()}
        
        expected_user_columns = ['id', 'phone', 'hashed_password', 'is_active', 'nick_name', 'avatar_url']
        for column in expected_user_columns:
            assert column in user_columns, f"users表缺少字段 {column}"
        
        # 测试user_cards表字段 - 根据实际SQL结构调整
        cursor.execute("DESCRIBE user_cards")
        card_columns = {col[0]: col[1] for col in cursor.fetchall()}
        
        expected_card_columns = ['id', 'user_id', 'role_type', 'scene_type', 'display_name', 'bio']
        for column in expected_card_columns:
            assert column in card_columns, f"user_cards表缺少字段 {column}"
        
        cursor.close()
    
    def test_indexes_exist(self, test_db_connection):
        """测试索引是否存在"""
        cursor = test_db_connection.cursor()
        
        # 测试users表的索引 - 根据实际SQL结构调整
        cursor.execute("SHOW INDEX FROM users")
        user_indexes = [index[2] for index in cursor.fetchall()]
        
        expected_user_indexes = ['idx_users_phone', 'idx_users_wechat_open_id', 'idx_users_status', 'idx_users_created_at']
        for index in expected_user_indexes:
            assert index in user_indexes, f"users表缺少索引 {index}"
        
        cursor.close()
    
    def test_foreign_keys(self, test_db_connection):
        """测试外键约束"""
        cursor = test_db_connection.cursor()
        
        # 测试user_cards表的外键 - 根据实际SQL结构调整
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'user_cards' 
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        foreign_keys = [fk[0] for fk in cursor.fetchall()]
        
        # 验证外键存在 - 使用实际的外键名称
        # MySQL会自动生成外键名称，格式为 '表名_ibfk_序号'
        expected_fk_pattern = 'user_cards_ibfk_'
        matching_fks = [fk for fk in foreign_keys if fk.startswith(expected_fk_pattern)]
        assert len(matching_fks) > 0, f"user_cards表缺少外键约束"
        
        cursor.close()
    
    def test_views_exist(self, test_db_connection):
        """测试视图是否存在"""
        cursor = test_db_connection.cursor()
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = [view[0] for view in cursor.fetchall()]
        cursor.close()
        
        # 验证视图存在
        expected_views = ['user_statistics', 'match_statistics', 'user_activity_statistics']
        for view in expected_views:
            assert view in views, f"视图 {view} 不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])