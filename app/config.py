import os
from typing import Optional
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
        ""
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
    
    # LLM配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")  # 通用LLM API密钥
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "doubao-seed-1-6-250615")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "volcengine")
    llm_provider: Optional[str] = None  # 兼容性格式
    openai_api_key: Optional[str] = None  # 兼容性格式
    
    # LLM调用限制
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 1000))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", 30))
    LLM_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", 60))
    
    # 微信小程序配置
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")
    
    # MySQL配置 - 根据环境自动选择
    def _get_mysql_config(self, config_name: str, default_dev: str, default_prod: str) -> str:
        """根据环境获取MySQL配置"""
        env_value = os.getenv(config_name)
        
        # 如果明确设置了环境变量，优先使用
        if env_value:
            return env_value
        
        # 根据环境选择默认值
        if self.ENVIRONMENT == "production":
            return default_prod
        else:
            return default_dev
    
    @property
    def mysql_host(self) -> str:
        """根据环境选择MySQL主机"""
        return self._get_mysql_config(
            "MYSQL_HOST", 
            "localhost", 
            "rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com"
        )
    
    @property
    def mysql_port(self) -> str:
        """根据环境选择MySQL端口"""
        return self._get_mysql_config("MYSQL_PORT", "3306", "3306")
    
    @property
    def mysql_database(self) -> str:
        """根据环境选择数据库名"""
        return self._get_mysql_config("MYSQL_DATABASE", "vmatch_dev", "vmatch_prod")
    
    @property
    def mysql_username(self) -> str:
        """根据环境选择用户名"""
        return self._get_mysql_config("MYSQL_USERNAME", "root", "user_admin")
    
    @property
    def mysql_password(self) -> str:
        """获取MySQL密码"""
        return self._get_mysql_config("MYSQL_PASSWORD", "", "liukun@187")
    
    # MySQL连接池配置
    MYSQL_POOL_SIZE: int = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    MYSQL_MAX_OVERFLOW: int = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
    MYSQL_POOL_RECYCLE: int = int(os.getenv("MYSQL_POOL_RECYCLE", "3600"))
    
    # 构建MySQL连接URL
    @property
    def mysql_database_url(self) -> str:
        """构建MySQL数据库连接URL"""
        password = self.mysql_password
        if password:
            return f"mysql+pymysql://{self.mysql_username}:{password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        else:
            return f"mysql+pymysql://{self.mysql_username}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # 根据环境选择数据库URL
    @property
    def database_url(self) -> str:
        """根据环境返回合适的数据库URL"""
        # 如果指定了DATABASE_URL环境变量，优先使用
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        
        # 所有环境都使用MySQL，根据环境自动选择配置
        return self.mysql_database_url
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的输入，避免验证错误

# 创建设置实例
settings = Settings()