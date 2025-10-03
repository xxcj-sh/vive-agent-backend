import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 环境变量配置
ENV = os.getenv("ENVIRONMENT", "development")

# 数据库URL配置 - 智能获取正确的数据库地址
def get_database_url():
    """从环境配置中获取正确的数据库地址"""
    # 1. 优先使用DATABASE_URL环境变量（如果已设置）
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 2. 根据环境自动选择数据库类型和配置
    env = os.getenv("ENVIRONMENT", "development")
    
    # MySQL配置（优先使用MySQL）
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_user = os.getenv("MYSQL_USERNAME", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    
    if env == "production":
        # 生产环境默认使用MySQL
        mysql_database = os.getenv("MYSQL_DATABASE", "vmatch_prod")
        if mysql_password:
            return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        else:
            return f"mysql+pymysql://{mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}"
    else:
        # 开发/测试环境：使用MySQL
        mysql_database = os.getenv("MYSQL_DATABASE", "vmatch_dev")
        
        # 使用MySQL（默认localhost）
        if mysql_password:
            return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        else:
            return f"mysql+pymysql://{mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}"
        
DATABASE_URL = get_database_url()

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()