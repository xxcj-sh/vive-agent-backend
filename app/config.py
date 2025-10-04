import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 确保.env文件被加载 - 在创建Settings实例之前加载
load_dotenv(".env", override=True)

class Settings(BaseSettings):
    """应用配置 - 优化版本
    
    优化说明:
    1. 移除重复的os.getenv()调用，完全依赖Pydantic的BaseSettings
    2. 明确配置优先级: 环境变量 > .env文件 > 默认值
    3. 统一配置字段命名，避免混淆
    4. 增强类型安全和验证
    """
    
    # ===========================
    # 基础环境配置
    # ===========================
    environment: str = "development"
    debug: bool = True
    
    # ===========================
    # 安全密钥配置
    # ===========================
    secret_key: str = "your_secret_key_here"  # 生产环境必须修改
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ===========================
    # 数据库配置
    # ===========================
    # 方式1: 完整的DATABASE_URL (优先级最高)
    database_url: str = ""
    
    # 方式2: 单独的数据库配置参数
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "vmatch_dev"
    mysql_username: str = "root"
    mysql_password: str = ""
    
    # MySQL连接池配置
    mysql_pool_size: int = 5
    mysql_max_overflow: int = 10
    mysql_pool_recycle: int = 3600
    
    # ===========================
    # LLM API配置
    # ===========================
    llm_api_key: str = ""
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    llm_model: str = "doubao-seed-1-6-250615"
    llm_provider: str = "volcengine"
    llm_max_tokens: int = 1000
    llm_timeout: int = 30
    llm_rate_limit_per_minute: int = 60
    
    # 兼容性字段 (将逐步废弃)
    llm_provider_compat: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # ===========================
    # 微信小程序配置
    # ===========================
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    
    # ===========================
    # 文件上传配置
    # ===========================
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir: str = "./uploads"
    max_file_size: int = 104_857_600      # 100MB
    max_image_size: int = 10_485_760       # 10MB
    max_video_size: int = 524_288_000      # 500MB
    
    # 兼容性字段
    upload_dir_compat: str = ""
    
    # ===========================
    # 测试模式配置
    # ===========================
    test_mode: bool = False
    
    # ===========================
    # 环境特定配置逻辑
    # ===========================
    
    def __init__(self, **kwargs):
        """初始化配置，根据环境设置适当的默认值"""
        super().__init__(**kwargs)
        
        # 根据环境调整默认配置
        if self.environment == "production":
            self._set_production_defaults()
        elif self.environment == "testing":
            self._set_testing_defaults()
        else:
            self._set_development_defaults()
        
        # 设置兼容性字段
        self._set_compatibility_fields()
    
    def _set_development_defaults(self):
        """开发环境默认配置"""
        if not self.mysql_host:
            self.mysql_host = "localhost"
        if not self.mysql_database:
            self.mysql_database = "vmatch_dev"
        if not self.mysql_username:
            self.mysql_username = "root"
        # 开发环境密码可以为空
    
    def _set_testing_defaults(self):
        """测试环境默认配置"""
        if not self.mysql_host:
            self.mysql_host = "rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com"
        if not self.mysql_database:
            self.mysql_database = "vmatch_dev"
        if not self.mysql_username:
            self.mysql_username = "user_test"
        # 测试环境建议设置密码
        if not self.mysql_password:
            print("⚠️  警告: 测试环境未设置数据库密码，建议设置MYSQL_PASSWORD")
    
    def _set_production_defaults(self):
        """生产环境默认配置"""
        if not self.mysql_host:
            self.mysql_host = "rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com"
        if not self.mysql_database:
            self.mysql_database = "vmatch_prod"
        if not self.mysql_username:
            self.mysql_username = "user_admin"
        
        # 生产环境必须设置密码和密钥
        if not self.mysql_password:
            raise ValueError("❌ 生产环境必须设置MYSQL_PASSWORD环境变量")
        if self.secret_key == "your_secret_key_here":
            raise ValueError("❌ 生产环境必须设置SECRET_KEY环境变量")
        
        # 生产环境必须关闭调试
        self.debug = False
    
    def _set_compatibility_fields(self):
        """设置兼容性和计算字段"""
        # 设置上传目录绝对路径
        if self.upload_dir == "./uploads":
            self.upload_dir = os.path.join(self.base_dir, "uploads")
        
        # 设置兼容性别名
        self.upload_dir_compat = self.upload_dir
    
    # ===========================
    # 计算属性
    # ===========================
    
    @property
    def computed_database_url(self) -> str:
        """计算最终的数据库连接URL
        
        优先级:
        1. 如果设置了database_url，直接使用
        2. 否则根据mysql配置参数构建
        """
        if self.database_url:
            return self.database_url
        
        # 根据mysql配置参数构建URL
        if self.mysql_password:
            return f"mysql+pymysql://{self.mysql_username}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        else:
            return f"mysql+pymysql://{self.mysql_username}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == "testing"
    
    # ===========================
    # 配置验证方法
    # ===========================
    
    def validate_config(self) -> list[str]:
        """验证配置，返回问题列表"""
        issues = []
        
        # 检查密钥安全性
        if self.secret_key == "your_secret_key_here":
            issues.append("⚠️  SECRET_KEY 使用默认值，建议设置强随机密钥")
        elif len(self.secret_key) < 32:
            issues.append("⚠️  SECRET_KEY 长度过短，建议至少32位字符")
        
        # 检查数据库配置
        if not self.computed_database_url:
            issues.append("❌ 数据库连接URL未配置")
        
        if self.is_production and not self.mysql_password:
            issues.append("❌ 生产环境必须设置数据库密码")
        
        # 检查生产环境配置
        if self.is_production and self.debug:
            issues.append("❌ 生产环境必须关闭调试模式")
        
        # 检查LLM配置
        if not self.llm_api_key:
            issues.append("⚠️  LLM_API_KEY 未设置，AI功能可能无法使用")
        
        # 检查微信小程序配置
        if not self.wechat_app_id or not self.wechat_app_secret:
            issues.append("⚠️  微信小程序配置不完整")
        
        return issues
    
    def print_config_summary(self):
        """打印配置摘要（隐藏敏感信息）"""
        print("=== 配置摘要 ===")
        print(f"环境: {self.environment}")
        print(f"调试模式: {self.debug}")
        print(f"数据库主机: {self.mysql_host}")
        print(f"数据库名: {self.mysql_database}")
        print(f"数据库用户: {self.mysql_username}")
        print(f"数据库密码: {'已设置' if self.mysql_password else '未设置'}")
        print(f"SECRET_KEY: {'已设置' if self.secret_key != 'your_secret_key_here' else '使用默认值'}")
        print(f"最终数据库URL: {self.computed_database_url}")
        
        # 验证配置
        issues = self.validate_config()
        if issues:
            print("\n=== 配置问题 ===")
            for issue in issues:
                print(issue)
        else:
            print("\n✅ 配置验证通过")
    
    # ===========================
    # Pydantic配置
    # ===========================
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 允许大小写不敏感的环境变量名
        extra = "ignore"  # 忽略额外的输入
        
        # 环境变量到字段名的映射
        # 处理环境变量名与字段名不一致的情况
        fields = {
            "environment": {"env": "ENVIRONMENT"},
            "debug": {"env": "DEBUG"},
            "secret_key": {"env": "SECRET_KEY"},
            "algorithm": {"env": "ALGORITHM"},
            "access_token_expire_minutes": {"env": "ACCESS_TOKEN_EXPIRE_MINUTES"},
            "database_url": {"env": "DATABASE_URL"},
            "mysql_host": {"env": "MYSQL_HOST"},
            "mysql_port": {"env": "MYSQL_PORT"},
            "mysql_database": {"env": "MYSQL_DATABASE"},
            "mysql_username": {"env": "MYSQL_USERNAME"},
            "mysql_password": {"env": "MYSQL_PASSWORD"},
            "mysql_pool_size": {"env": "MYSQL_POOL_SIZE"},
            "mysql_max_overflow": {"env": "MYSQL_MAX_OVERFLOW"},
            "mysql_pool_recycle": {"env": "MYSQL_POOL_RECYCLE"},
            "llm_api_key": {"env": "LLM_API_KEY"},
            "llm_base_url": {"env": "LLM_BASE_URL"},
            "llm_model": {"env": "LLM_MODEL"},
            "llm_provider": {"env": "LLM_PROVIDER"},
            "llm_max_tokens": {"env": "LLM_MAX_TOKENS"},
            "llm_timeout": {"env": "LLM_TIMEOUT"},
            "llm_rate_limit_per_minute": {"env": "LLM_RATE_LIMIT_PER_MINUTE"},
            "llm_provider_compat": {"env": "LLM_PROVIDER_COMPAT"},
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "wechat_app_id": {"env": "WECHAT_APP_ID"},
            "wechat_app_secret": {"env": "WECHAT_APP_SECRET"},
            "base_dir": {"env": "BASE_DIR"},
            "upload_dir": {"env": "UPLOAD_DIR"},
            "max_file_size": {"env": "MAX_FILE_SIZE"},
            "max_image_size": {"env": "MAX_IMAGE_SIZE"},
            "max_video_size": {"env": "MAX_VIDEO_SIZE"},
            "test_mode": {"env": "TEST_MODE"},
        }


# 全局配置实例
settings = Settings()

# 如果直接运行此文件，显示配置摘要
if __name__ == "__main__":
    settings.print_config_summary()