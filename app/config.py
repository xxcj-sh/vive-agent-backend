import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 智能加载环境文件 - 根据环境变量或默认优先级加载
env_file = os.environ.get('ENV_FILE', '.env')
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ 已加载环境文件: {env_file}")
elif os.path.exists('.env'):
    load_dotenv('.env', override=True)
    print("✅ 已加载环境文件: .env")
else:
    print("⚠️  未找到环境文件，使用默认配置")

class Settings(BaseSettings):
    """应用配置 - 与.env文件保持一致
    
    配置原则:
    1. 字段名称与.env文件中的变量名完全一致
    2. 完全依赖Pydantic的BaseSettings从环境变量读取配置
    3. 所有配置都通过环境变量或.env文件提供
    4. 移除复杂的映射逻辑，保持简单直接
    """
    
    # ===========================
    # 基础环境配置
    # ===========================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ===========================
    # 安全密钥配置
    # ===========================
    SECRET_KEY: str = "your_secret_key_here"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ===========================
    # 数据库配置
    # ===========================
    # 方式1: 完整的DATABASE_URL (优先级最高)
    DATABASE_URL: str = ""
    
    # 方式2: 单独的数据库配置参数
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "vmatch_dev"
    MYSQL_USERNAME: str = "root"
    MYSQL_PASSWORD: str = ""
    
    # MySQL连接池配置
    MYSQL_POOL_SIZE: int = 5
    MYSQL_MAX_OVERFLOW: int = 10
    MYSQL_POOL_RECYCLE: int = 3600
    
    # ===========================
    # LLM API配置
    # ===========================
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    LLM_MODEL: str = "doubao-seed-1-6-250615"
    LLM_PROVIDER: str = "volcengine"
    LLM_MAX_TOKENS: int = 1000
    LLM_TIMEOUT: int = 30
    LLM_RATE_LIMIT_PER_MINUTE: int = 60
    
    # 兼容性字段 (将逐步废弃)
    LLM_PROVIDER_COMPAT: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # ===========================
    # 微信小程序配置
    # ===========================
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    
    # ===========================
    # 文件上传配置
    # ===========================
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 104_857_600      # 100MB
    MAX_IMAGE_SIZE: int = 10_485_760       # 10MB
    MAX_VIDEO_SIZE: int = 524_288_000      # 500MB
    
    # 兼容性字段
    UPLOAD_DIR_COMPAT: str = ""
    
    # ===========================
    # 测试模式配置
    # ===========================
    TEST_MODE: bool = False
    
    # ===========================
    # 环境特定配置逻辑
    # ===========================
    
    def __init__(self, **kwargs):
        """初始化配置，根据环境设置适当的默认值"""
        super().__init__(**kwargs)
        
        # 根据环境调整默认配置
        if self.ENVIRONMENT == "production":
            self._set_production_defaults()
        elif self.ENVIRONMENT == "testing":
            self._set_testing_defaults()
        else:
            self._set_development_defaults()
        
        # 设置兼容性字段
        self._set_compatibility_fields()
    
    def _set_development_defaults(self):
        """开发环境默认配置"""
        if not self.MYSQL_HOST:
            self.MYSQL_HOST = "localhost"
        if not self.MYSQL_DATABASE:
            self.MYSQL_DATABASE = "vmatch_dev"
        if not self.MYSQL_USERNAME:
            self.MYSQL_USERNAME = "root"
        # 开发环境密码可以为空
    
    def _set_testing_defaults(self):
        """测试环境默认配置"""
        if not self.MYSQL_HOST:
            self.MYSQL_HOST = "rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com"
        if not self.MYSQL_DATABASE:
            self.MYSQL_DATABASE = "vmatch_dev"
        if not self.MYSQL_USERNAME:
            self.MYSQL_USERNAME = "user_test"
        # 测试环境建议设置密码
        if not self.MYSQL_PASSWORD:
            print("⚠️  警告: 测试环境未设置数据库密码，建议设置MYSQL_PASSWORD")
    
    def _set_production_defaults(self):
        """生产环境默认配置"""
        if not self.MYSQL_HOST:
            self.MYSQL_HOST = "rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com"
        if not self.MYSQL_DATABASE:
            self.MYSQL_DATABASE = "vmatch_prod"
        if not self.MYSQL_USERNAME:
            self.MYSQL_USERNAME = "user_admin"
        
        # 生产环境必须设置密码和密钥
        if not self.MYSQL_PASSWORD:
            raise ValueError("❌ 生产环境必须设置MYSQL_PASSWORD环境变量")
        if self.SECRET_KEY == "your_secret_key_here":
            raise ValueError("❌ 生产环境必须设置SECRET_KEY环境变量")
        
        # 生产环境必须关闭调试
        self.DEBUG = False
    
    def _set_compatibility_fields(self):
        """设置兼容性和计算字段"""
        # 设置上传目录绝对路径
        if self.UPLOAD_DIR == "./uploads":
            self.UPLOAD_DIR = os.path.join(self.BASE_DIR, "uploads")
        
        # 设置兼容性别名
        self.UPLOAD_DIR_COMPAT = self.UPLOAD_DIR
    
    # ===========================
    # 计算属性
    # ===========================
    
    @property
    def computed_database_url(self) -> str:
        """计算最终的数据库连接URL
        
        优先级:
        1. 如果设置了DATABASE_URL，直接使用
        2. 否则根据mysql配置参数构建
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # 根据mysql配置参数构建URL
        if self.MYSQL_PASSWORD:
            return f"mysql+pymysql://{self.MYSQL_USERNAME}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        else:
            return f"mysql+pymysql://{self.MYSQL_USERNAME}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == "testing"
    
    # ===========================
    # 配置验证方法
    # ===========================
    
    def validate_config(self) -> list[str]:
        """验证配置，返回问题列表"""
        issues = []
        
        # 检查密钥安全性
        if self.SECRET_KEY == "your_secret_key_here":
            issues.append("⚠️  SECRET_KEY 使用默认值，建议设置强随机密钥")
        elif len(self.SECRET_KEY) < 32:
            issues.append("⚠️  SECRET_KEY 长度过短，建议至少32位字符")
        
        # 检查数据库配置
        if not self.computed_database_url:
            issues.append("❌ 数据库连接URL未配置")
        
        if self.is_production and not self.MYSQL_PASSWORD:
            issues.append("❌ 生产环境必须设置数据库密码")
        
        # 检查生产环境配置
        if self.is_production and self.DEBUG:
            issues.append("❌ 生产环境必须关闭调试模式")
        
        # 检查LLM配置
        if not self.LLM_API_KEY:
            issues.append("⚠️  LLM_API_KEY 未设置，AI功能可能无法使用")
        
        # 检查微信小程序配置
        if not self.WECHAT_APP_ID or not self.WECHAT_APP_SECRET:
            issues.append("⚠️  微信小程序配置不完整")
        
        return issues
    
    def print_config_summary(self):
        """打印配置摘要（隐藏敏感信息）"""
        print("=== 配置摘要 ===")
        print(f"环境: {self.ENVIRONMENT}")
        print(f"调试模式: {self.DEBUG}")
        print(f"数据库主机: {self.MYSQL_HOST}")
        print(f"数据库名: {self.MYSQL_DATABASE}")
        print(f"数据库用户: {self.MYSQL_USERNAME}")
        print(f"数据库密码: {'已设置' if self.MYSQL_PASSWORD else '未设置'}")
        print(f"SECRET_KEY: {'已设置' if self.SECRET_KEY != 'your_secret_key_here' else '使用默认值'}")
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


# 全局配置实例
settings = Settings()

# 如果直接运行此文件，显示配置摘要
if __name__ == "__main__":
    settings.print_config_summary()