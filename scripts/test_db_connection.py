#!/usr/bin/env python3
"""
数据库连接测试脚本
测试数据库连接配置的正确性
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.config import settings
    from app.core.database_config import DatabaseManager, DatabaseConfig
except ImportError as e:
    print(f"❌ 无法导入必要的模块: {e}")
    print("请确保在正确的目录下运行此脚本")
    sys.exit(1)

import pymysql
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

class DatabaseConnectionTester:
    """数据库连接测试器"""
    
    def __init__(self):
        self.results = []
        self.connection_string = settings.database_url
        
    def test_connection_string_format(self) -> bool:
        """测试数据库连接字符串格式"""
        print("🔍 测试数据库连接字符串格式...")
        
        try:
            # 检查URL格式
            if not self.connection_string.startswith('mysql+pymysql://'):
                self.results.append(('❌', '连接字符串格式', 'URL应该以 mysql+pymysql:// 开头'))
                return False
            
            # 解析URL组件
            import re
            pattern = r'mysql\+pymysql://([^:@]+)(?::([^@]+))?@([^:]+):(\d+)/(\w+)'
            match = re.match(pattern, self.connection_string)
            
            if not match:
                self.results.append(('❌', '连接字符串格式', 'URL格式不正确'))
                return False
            
            user, password, host, port, database = match.groups()
            
            # 检查各个组件
            if not user:
                self.results.append(('❌', '用户名', '用户名不能为空'))
                return False
            
            if not host:
                self.results.append(('❌', '主机地址', '主机地址不能为空'))
                return False
            
            if not database:
                self.results.append(('❌', '数据库名', '数据库名不能为空'))
                return False
            try:
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    self.results.append(('❌', '端口', '端口号必须在1-65535之间'))
                    return False
            except ValueError:
                self.results.append(('❌', '端口', '端口号必须是数字'))
                return False
            
            self.results.append(('✅', '连接字符串格式', '格式正确'))
            
            # 显示解析结果
            print(f"   📋 解析结果:")
            print(f"      用户名: {user}")
            print(f"      密码: {'已设置' if password else '未设置'}")
            print(f"      主机: {host}")
            print(f"      端口: {port}")
            print(f"      数据库: {database}")
            
            return True
            
        except Exception as e:
            self.results.append(('❌', '连接字符串格式', f'解析失败: {e}'))
            return False
    
    def test_mysql_connection(self) -> bool:
        """测试MySQL连接"""
        print("\n🔍 测试MySQL连接...")
        
        try:
            # 解析连接参数
            import re
            pattern = r'mysql\+pymysql://([^:@]+)(?::([^@]+))?@([^:]+):(\d+)/(\w+)'
            match = re.match(pattern, self.connection_string)
            
            if not match:
                self.results.append(('❌', 'MySQL连接', '无法解析连接字符串'))
                return False
            
            user, password, host, port, database = match.groups()
            
            # 测试连接
            connection = None
            try:
                connection = pymysql.connect(
                    host=host,
                    port=int(port),
                    user=user,
                    password=password or '',
                    database=database,
                    charset='utf8mb4',
                    connect_timeout=10
                )
                
                # 测试查询
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()
                    
                    cursor.execute("SELECT DATABASE()")
                    current_db = cursor.fetchone()
                    
                    cursor.execute("SELECT USER()")
                    current_user = cursor.fetchone()
                
                self.results.append(('✅', 'MySQL连接', f'连接成功'))
                print(f"   📋 连接信息:")
                print(f"      MySQL版本: {version[0] if version else '未知'}")
                print(f"      当前数据库: {current_db[0] if current_db else '未知'}")
                print(f"      当前用户: {current_user[0] if current_user else '未知'}")
                
                return True
                
            except pymysql.Error as e:
                error_code = e.args[0] if e.args else -1
                error_msg = e.args[1] if len(e.args) > 1 else str(e)
                
                if error_code == 1045:
                    self.results.append(('❌', 'MySQL连接', f'访问被拒绝: 用户名或密码错误'))
                elif error_code == 1049:
                    self.results.append(('❌', 'MySQL连接', f'数据库不存在: {database}'))
                elif error_code == 2003:
                    self.results.append(('❌', 'MySQL连接', f'无法连接到MySQL服务器: {host}:{port}'))
                else:
                    self.results.append(('❌', 'MySQL连接', f'连接失败: {error_msg}'))
                
                return False
                
            finally:
                if connection:
                    connection.close()
                    
        except Exception as e:
            self.results.append(('❌', 'MySQL连接', f'测试失败: {e}'))
            return False
    
    def test_sqlalchemy_connection(self) -> bool:
        """测试SQLAlchemy连接"""
        print("\n🔍 测试SQLAlchemy连接...")
        
        try:
            # 创建引擎
            engine = create_engine(
                self.connection_string,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 测试连接
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # 测试数据库存在性
                result = conn.execute(text("SHOW DATABASES"))
                databases = [row[0] for row in result.fetchall()]
                
                # 获取当前数据库
                result = conn.execute(text("SELECT DATABASE()"))
                current_db = result.fetchone()[0]
                
            self.results.append(('✅', 'SQLAlchemy连接', '连接成功'))
            print(f"   📋 SQLAlchemy信息:")
            print(f"      当前数据库: {current_db}")
            print(f"      可用数据库: {len(databases)} 个")
            
            return True
            
        except SQLAlchemyError as e:
            self.results.append(('❌', 'SQLAlchemy连接', f'连接失败: {e}'))
            return False
        except Exception as e:
            self.results.append(('❌', 'SQLAlchemy连接', f'测试失败: {e}'))
            return False
    
    def test_database_tables(self) -> bool:
        """测试数据库表结构"""
        print("\n🔍 测试数据库表结构...")
        
        try:
            # 创建引擎
            engine = create_engine(self.connection_string)
            
            # 测试表存在性
            expected_tables = [
                'users', 'user_cards', 'match_actions', 'match_results',
                'llm_usage_logs', 'social_preferences', 'social_profiles',
                'social_match_criteria', 'user_profiles'
            ]
            
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                existing_tables = [row[0] for row in result.fetchall()]
                
                missing_tables = []
                for table in expected_tables:
                    if table not in existing_tables:
                        missing_tables.append(table)
                
                if not missing_tables:
                    self.results.append(('✅', '数据库表', '所有必需的表都存在'))
                    print(f"   📋 表结构检查:")
                    print(f"      找到 {len(existing_tables)} 个表")
                    print(f"      所有 {len(expected_tables)} 个必需表都存在")
                    return True
                else:
                    self.results.append(('⚠️', '数据库表', f'缺少 {len(missing_tables)} 个表'))
                    print(f"   📋 缺失的表:")
                    for table in missing_tables:
                        print(f"      - {table}")
                    print(f"\n💡 建议运行数据库初始化脚本:")
                    print(f"   python scripts/init_mysql_database.py")
                    return False
                    
        except Exception as e:
            self.results.append(('❌', '数据库表', f'检查失败: {e}'))
            return False
    
    def test_connection_performance(self) -> bool:
        """测试连接性能"""
        print("\n🔍 测试连接性能...")
        
        try:
            # 创建引擎
            engine = create_engine(self.connection_string)
            
            # 测试连接时间
            times = []
            for i in range(3):
                start_time = time.time()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            if avg_time < 0.1:
                performance = '优秀'
                icon = '✅'
            elif avg_time < 0.5:
                performance = '良好'
                icon = '✅'
            elif avg_time < 1.0:
                performance = '一般'
                icon = '⚠️'
            else:
                performance = '较差'
                icon = '❌'
            
            self.results.append((icon, '连接性能', f'{performance} (平均: {avg_time:.3f}s, 最大: {max_time:.3f}s)'))
            
            print(f"   📋 性能测试结果:")
            print(f"      平均连接时间: {avg_time:.3f}秒")
            print(f"      最大连接时间: {max_time:.3f}秒")
            print(f"      性能评级: {performance}")
            
            return True
            
        except Exception as e:
            self.results.append(('❌', '连接性能', f'测试失败: {e}'))
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始数据库连接测试...")
        print("=" * 50)
        
        results = {}
        
        # 运行各项测试
        results['connection_string'] = self.test_connection_string_format()
        results['mysql_connection'] = self.test_mysql_connection()
        results['sqlalchemy_connection'] = self.test_sqlalchemy_connection()
        results['database_tables'] = self.test_database_tables()
        results['connection_performance'] = self.test_connection_performance()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """打印测试总结"""
        print("\n" + "=" * 50)
        print("📊 数据库连接测试总结")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        print(f"\n测试通过: {passed}/{total}")
        
        if passed == total:
            print("✅ 所有测试都通过了！数据库配置正确。")
        elif passed >= total * 0.8:
            print("⚠️  大部分测试通过，但有一些问题需要处理。")
        else:
            print("❌ 测试失败较多，请检查数据库配置。")
        
        print(f"\n详细结果:")
        for icon, test_name, message in self.results:
            print(f"  {icon} {test_name}: {message}")
        
        # 提供建议
        print(f"\n💡 建议:")
        if not results['connection_string']:
            print("  - 检查数据库连接字符串格式")
        if not results['mysql_connection']:
            print("  - 检查MySQL服务是否运行")
            print("  - 检查用户名、密码、主机地址和端口")
            print("  - 检查数据库是否存在")
        if not results['sqlalchemy_connection']:
            print("  - 检查SQLAlchemy配置")
        if not results['database_tables']:
            print("  - 运行数据库初始化脚本")
        if not results['connection_performance']:
            print("  - 检查网络连接和数据库性能")
        
        if all(results.values()):
            print("  - 数据库配置正确，可以正常使用应用")

def main():
    """主函数"""
    tester = DatabaseConnectionTester()
    results = tester.run_all_tests()
    tester.print_summary(results)

if __name__ == "__main__":
    main()