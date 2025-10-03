#!/usr/bin/env python3
"""
数据库配置检查脚本
用于验证数据库连接和配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def check_sqlite_config():
    """检查SQLite配置"""
    print("=== SQLite配置检查 ===")
    
    database_url = settings.database_url
    print(f"数据库URL: {database_url}")
    
    if database_url.startswith("sqlite"):
        # 提取SQLite文件路径
        db_path = database_url.replace("sqlite:///", "")
        print(f"SQLite文件路径: {db_path}")
        
        # 检查文件是否存在
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"✅ SQLite数据库文件存在，大小: {file_size / (1024*1024):.2f} MB")
        else:
            print("⚠️ SQLite数据库文件不存在，将在首次运行时创建")
        
        return True
    else:
        print("❌ 当前配置不是SQLite数据库")
        return False

def check_mysql_config():
    """检查MySQL配置"""
    print("\n=== MySQL配置检查 ===")
    
    print(f"MySQL主机: {settings.mysql_host}")
    print(f"MySQL端口: {settings.mysql_port}")
    print(f"数据库名: {settings.mysql_database}")
    print(f"用户名: {settings.mysql_username}")
    print(f"密码: {'*' * len(settings.mysql_password) if settings.mysql_password else '未设置'}")
    
    # 检查MySQL连接
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=settings.mysql_host,
            port=int(settings.mysql_port),
            user=settings.mysql_username,
            password=settings.mysql_password,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SHOW DATABASES LIKE %s", (settings.mysql_database,))
        db_exists = cursor.fetchone() is not None
        
        if db_exists:
            print("✅ MySQL数据库存在")
            
            # 切换到数据库并检查表
            cursor.execute(f"USE {settings.mysql_database}")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✅ 数据库中有 {len(tables)} 个表")
        else:
            print("⚠️ MySQL数据库不存在，需要初始化")
        
        cursor.close()
        conn.close()
        
        print("✅ MySQL连接测试成功")
        return True
        
    except ImportError:
        print("❌ mysql-connector-python未安装，请运行: pip install mysql-connector-python")
        return False
    except mysql.connector.Error as e:
        print(f"❌ MySQL连接失败: {e}")
        return False

def check_database_url():
    """检查数据库URL配置"""
    print("\n=== 数据库URL配置检查 ===")
    
    database_url = settings.database_url
    print(f"当前数据库URL: {database_url}")
    
    if database_url.startswith("sqlite"):
        print("✅ 使用SQLite数据库（开发环境）")
        return "sqlite"
    elif database_url.startswith("mysql"):
        print("✅ 使用MySQL数据库（生产环境）")
        return "mysql"
    else:
        print(f"⚠️ 未知的数据库类型: {database_url}")
        return "unknown"

def check_environment():
    """检查环境配置"""
    print("\n=== 环境配置检查 ===")
    
    print(f"当前环境: {settings.ENVIRONMENT}")
    print(f"调试模式: {settings.DEBUG}")
    
    if settings.ENVIRONMENT == "production":
        print("✅ 生产环境配置")
        return "production"
    else:
        print("✅ 开发环境配置")
        return "development"

def main():
    """主函数"""
    print("VMatch数据库配置检查工具")
    print("=" * 50)
    
    # 检查环境
    env = check_environment()
    
    # 检查数据库URL
    db_type = check_database_url()
    
    # 根据数据库类型进行检查
    if db_type == "sqlite":
        sqlite_ok = check_sqlite_config()
        mysql_ok = False
    elif db_type == "mysql":
        sqlite_ok = False
        mysql_ok = check_mysql_config()
    else:
        sqlite_ok = check_sqlite_config()
        mysql_ok = check_mysql_config()
    
    # 总结
    print("\n" + "=" * 50)
    print("配置检查总结:")
    
    if env == "production" and db_type != "mysql":
        print("⚠️ 警告: 生产环境建议使用MySQL数据库")
    
    if db_type == "sqlite" and sqlite_ok:
        print("✅ SQLite配置正常")
    elif db_type == "mysql" and mysql_ok:
        print("✅ MySQL配置正常")
    else:
        print("❌ 数据库配置存在问题，请检查上述错误信息")
    
    print("\n建议操作:")
    if db_type == "sqlite":
        print("- 如需切换到MySQL，请设置ENVIRONMENT=production并配置MySQL连接参数")
    elif db_type == "mysql":
        print("- 如需初始化数据库，请运行: python scripts/init_mysql_database.py")
    
    return sqlite_ok or mysql_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)