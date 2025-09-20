import os
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 环境变量配置
ENV = os.getenv("ENVIRONMENT", "development")

# 数据库URL配置 - 优先使用环境变量
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URLS = {
        "development": "sqlite:///./vmatch_dev.db",
        "testing": "sqlite:///./vmatch_test.db", 
        "production": "sqlite:///./vmatch_prod.db"
    }
    DATABASE_URL = DATABASE_URLS.get(ENV, "sqlite:///./vmatch_dev.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

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