#!/usr/bin/env python3
"""
测试 user_profile_feedback 表的 feedback_type 字段默认值设置
"""

import unittest
import pymysql
import os
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

class TestFeedbackTypeDefault(unittest.TestCase):
    """测试 feedback_type 字段默认值的单元测试"""
    
    def setUp(self):
        """设置数据库连接"""
        # 加载环境变量
        load_dotenv()
        
        # 获取数据库配置
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USERNAME', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'db': os.getenv('MYSQL_DATABASE', 'vmatch_dev'),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor
        }
        
        # 连接数据库
        self.conn = pymysql.connect(**self.db_config)
    
    def tearDown(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def test_feedback_type_has_default_value(self):
        """测试 feedback_type 字段是否有默认值"""
        with self.conn.cursor() as cursor:
            # 查询表结构信息
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_DEFAULT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s 
                AND COLUMN_NAME = %s
            """, (self.db_config['db'], 'user_profile_feedback', 'feedback_type'))
            
            result = cursor.fetchone()
            
            # 验证字段存在且有默认值
            self.assertIsNotNone(result, "字段 feedback_type 不存在")
            self.assertEqual(result['COLUMN_DEFAULT'], 'general', "feedback_type 字段默认值不是 'general'")
    
    def test_insert_without_feedback_type(self):
        """测试不指定 feedback_type 字段时能否成功插入数据"""
        test_id = 'test-' + os.urandom(8).hex()
        
        try:
            with self.conn.cursor() as cursor:
                # 首先获取一个有效的user_id
                cursor.execute("SELECT id FROM users LIMIT 1")
                user = cursor.fetchone()
                
                if not user:
                    self.skipTest("没有找到有效的用户数据，跳过测试")
                
                valid_user_id = user['id']
                
                # 获取一个有效的profile_id
                cursor.execute("SELECT id FROM user_profiles LIMIT 1")
                profile = cursor.fetchone()
                
                if not profile:
                    self.skipTest("没有找到有效的用户画像数据，跳过测试")
                
                valid_profile_id = profile['id']
                
                # 尝试插入一条不包含 feedback_type 的记录，但使用有效的外键值
                cursor.execute("""
                    INSERT INTO user_profile_feedback 
                    (id, user_id, profile_id, rating) 
                    VALUES (%s, %s, %s, %s)
                """, (test_id, valid_user_id, valid_profile_id, 5))
                
                # 提交事务
                self.conn.commit()
                
                # 查询插入的记录
                cursor.execute("""
                    SELECT feedback_type FROM user_profile_feedback WHERE id = %s
                """, (test_id,))
                
                result = cursor.fetchone()
                
                # 验证默认值是否正确应用
                self.assertIsNotNone(result, "插入的记录不存在")
                self.assertEqual(result['feedback_type'], 'general', "feedback_type 默认值没有正确应用")
        
        finally:
            # 清理测试数据
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM user_profile_feedback WHERE id = %s", (test_id,))
                self.conn.commit()

if __name__ == '__main__':
    unittest.main()