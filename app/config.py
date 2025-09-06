import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Settings(BaseSettings):
    """应用配置"""
    # 环境设置
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///./vmatch_{ENVIRONMENT}.db"
    )
    
    # 应用配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 测试模式配置 - 默认关闭
    test_mode: bool = os.getenv("TEST_MODE", "false").lower() == "true"
    
    # 文件上传配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
    upload_dir: str = UPLOAD_DIR  # 兼容性别名
    
    # 文件大小限制配置
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))  # 100MB (通用限制)
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", 10 * 1024 * 1024))   # 10MB (图片限制)
    MAX_VIDEO_SIZE: int = int(os.getenv("MAX_VIDEO_SIZE", 500 * 1024 * 1024))  # 500MB (视频限制)
    
    class Config:
        env_file = ".env"

# 创建设置实例
settings = Settings()