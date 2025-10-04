#!/usr/bin/env python3
"""
环境配置切换助手
帮助在开发、测试、生产环境之间切换配置
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Optional

class EnvironmentSwitcher:
    """环境配置切换器"""
    
    ENVIRONMENTS = {
        'development': {
            'name': '开发环境',
            'description': '本地开发环境，使用本地MySQL数据库',
            'configs': {
                'ENVIRONMENT': 'development',
                'DEBUG': 'true',
                'MYSQL_HOST': 'localhost',
                'MYSQL_PORT': '3306',
                'MYSQL_DATABASE': 'vmatch_dev',
                'MYSQL_USERNAME': 'root',
                'MYSQL_PASSWORD': '',  # 开发环境可空
                'LLM_BASE_URL': 'https://ark.cn-beijing.volces.com/api/v3',
                'LLM_MODEL': 'doubao-seed-1-6-250615',
            }
        },
        'testing': {
            'name': '测试环境',
            'description': '测试环境，使用独立的测试数据库',
            'configs': {
                'ENVIRONMENT': 'testing',
                'DEBUG': 'false',
                'MYSQL_HOST': 'localhost',
                'MYSQL_PORT': '3306',
                'MYSQL_DATABASE': 'vmatch_dev',
                'MYSQL_USERNAME': 'test_user',
                'MYSQL_PASSWORD': '',  # 需要设置
                'LLM_BASE_URL': 'https://ark.cn-beijing.volces.com/api/v3',
                'LLM_MODEL': 'doubao-seed-1-6-250615',
            }
        },
        'production': {
            'name': '生产环境',
            'description': '生产环境，使用云数据库',
            'configs': {
                'ENVIRONMENT': 'production',
                'DEBUG': 'false',
                'MYSQL_HOST': 'rm-uf672o44x147i9c2p9o.mysql.rds.aliyuncs.com',
                'MYSQL_PORT': '3306',
                'MYSQL_DATABASE': 'vmatch_prod',
                'MYSQL_USERNAME': 'your_production_username',  # 需要修改
                'MYSQL_PASSWORD': 'your_strong_password',  # 需要修改
                'LLM_BASE_URL': 'https://ark.cn-beijing.volces.com/api/v3',
                'LLM_MODEL': 'doubao-seed-1-6-250615',
            }
        }
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        self.env_backup = self.project_root / '.env.backup'
    
    def list_environments(self):
        """列出所有可用的环境配置"""
        print("📋 可用环境配置:")
        print("=" * 50)
        
        for env_key, env_info in self.ENVIRONMENTS.items():
            print(f"\n🔧 {env_info['name']} ({env_key})")
            print(f"   描述: {env_info['description']}")
            print("   主要配置:")
            for key, value in env_info['configs'].items():
                if 'PASSWORD' in key and value:
                    value = '*' * len(value)  # 隐藏密码
                print(f"     {key}: {value}")
    
    def backup_current_env(self) -> bool:
        """备份当前的环境配置文件"""
        if self.env_file.exists():
            try:
                shutil.copy2(self.env_file, self.env_backup)
                print(f"✅ 已备份当前配置到: {self.env_backup}")
                return True
            except Exception as e:
                print(f"❌ 备份失败: {e}")
                return False
        return True
    
    def create_env_file(self, environment: str, custom_configs: Optional[Dict[str, str]] = None):
        """创建指定环境的环境变量文件"""
        if environment not in self.ENVIRONMENTS:
            print(f"❌ 不支持的环境: {environment}")
            print(f"支持的环境: {list(self.ENVIRONMENTS.keys())}")
            return False
        
        env_info = self.ENVIRONMENTS[environment]
        configs = env_info['configs'].copy()
        
        # 应用自定义配置
        if custom_configs:
            configs.update(custom_configs)
        
        # 备份当前配置
        if not self.backup_current_env():
            return False
        
        try:
            # 创建新的.env文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(f"# VMatch {env_info['name']} 环境配置\n")
                f.write(f"# 生成时间: {self._get_current_time()}\n")
                f.write(f"# 描述: {env_info['description']}\n")
                f.write("\n")
                
                # 写入基础配置
                f.write("# ===========================\n")
                f.write("# 基础环境配置\n")
                f.write("# ===========================\n")
                for key, value in configs.items():
                    if key in ['ENVIRONMENT', 'DEBUG']:
                        f.write(f"{key}={value}\n")
                
                f.write("\n# ===========================\n")
                f.write("# 安全密钥配置 (必填)\n")
                f.write("# ===========================\n")
                f.write("# ⚠️  重要: 必须修改以下配置\n")
                f.write("SECRET_KEY=your_very_secret_key_here_change_this\n")
                
                f.write("\n# ===========================\n")
                f.write("# 数据库配置\n")
                f.write("# ===========================\n")
                for key, value in configs.items():
                    if key.startswith('MYSQL_'):
                        f.write(f"{key}={value}\n")
                
                f.write("\n# ===========================\n")
                f.write("# LLM API配置\n")
                f.write("# ===========================\n")
                f.write("# LLM API密钥 (必填)\n")
                f.write("LLM_API_KEY=your_llm_api_key_here\n")
                for key, value in configs.items():
                    if key.startswith('LLM_') and key != 'LLM_API_KEY':
                        f.write(f"{key}={value}\n")
                
                f.write("\n# ===========================\n")
                f.write("# 微信小程序配置\n")
                f.write("# ===========================\n")
                f.write("WECHAT_APP_ID=your_wechat_app_id\n")
                f.write("WECHAT_APP_SECRET=your_wechat_app_secret\n")
                
                f.write("\n# ===========================\n")
                f.write("# 文件上传配置\n")
                f.write("# ===========================\n")
                f.write("UPLOAD_DIR=./uploads\n")
                f.write("MAX_FILE_SIZE=104857600\n")
                f.write("MAX_IMAGE_SIZE=10485760\n")
                f.write("MAX_VIDEO_SIZE=524288000\n")
                
                f.write("\n# ===========================\n")
                f.write("# JWT配置\n")
                f.write("# ===========================\n")
                f.write("ALGORITHM=HS256\n")
                f.write("ACCESS_TOKEN_EXPIRE_MINUTES=30\n")
                
                f.write("\n# ===========================\n")
                f.write("# 测试模式配置\n")
                f.write("# ===========================\n")
                f.write("TEST_MODE=false\n")
                
                f.write("\n# ===========================\n")
                f.write("# 安全提示\n")
                f.write("# ===========================\n")
                f.write("# ⚠️  重要提醒:\n")
                f.write("# 1. 生产环境必须设置强密码\n")
                f.write("# 2. SECRET_KEY必须是长随机字符串\n")
                f.write("# 3. 不要将.env文件提交到版本控制\n")
                f.write("# 4. 定期更新密码和密钥\n")
                f.write("# 5. 使用专用的数据库用户\n")
            
            print(f"✅ 已创建 {env_info['name']} 环境配置文件: {self.env_file}")
            print(f"📋 配置说明: {env_info['description']}")
            
            # 显示需要手动配置的项目
            manual_configs = []
            if 'PASSWORD' in configs.get('MYSQL_PASSWORD', ''):
                manual_configs.append('MYSQL_PASSWORD')
            manual_configs.append('SECRET_KEY')
            
            if environment in ['testing', 'production']:
                print(f"\n⚠️  请手动编辑 .env 文件，设置以下配置:")
                for config in manual_configs:
                    print(f"   - {config}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建环境配置文件失败: {e}")
            return False
    
    def validate_current_env(self):
        """验证当前环境配置"""
        if not self.env_file.exists():
            print("❌ 未找到 .env 文件")
            return False
        
        try:
            # 重新加载配置
            os.environ.clear()
            from app.config import settings
            
            print("🔍 验证当前环境配置...")
            print(f"✅ 环境: {settings.ENVIRONMENT}")
            print(f"✅ 数据库: {settings.mysql_database} @ {settings.mysql_host}:{settings.mysql_port}")
            print(f"✅ 数据库用户: {settings.mysql_username}")
            
            # 检查关键配置
            issues = []
            if not settings.mysql_password and settings.ENVIRONMENT != 'development':
                issues.append("非开发环境未设置数据库密码")
            
            if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'your_very_secret_key_here_change_this':
                issues.append("SECRET_KEY使用默认值，需要修改")
            
            if issues:
                print(f"\n⚠️  发现配置问题:")
                for issue in issues:
                    print(f"   - {issue}")
                return False
            else:
                print("✅ 配置验证通过")
                return True
                
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            return False
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def switch_environment(self, environment: str):
        """切换到指定环境"""
        print(f"🔄 正在切换到 {environment} 环境...")
        
        if self.create_env_file(environment):
            print(f"\n✅ 环境切换完成!")
            print(f"📋 新环境: {self.ENVIRONMENTS[environment]['name']}")
            print(f"📝 描述: {self.ENVIRONMENTS[environment]['description']}")
            
            print(f"\n⚠️  下一步操作:")
            print(f"   1. 检查并编辑 .env 文件中的敏感配置")
            print(f"   2. 重启应用以应用新配置")
            print(f"   3. 运行数据库连接测试")
            print(f"   4. 验证应用功能正常")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🔧 VMatch 环境配置切换助手")
        print("=" * 50)
        print("使用方法:")
        print("  python env_switcher.py list          - 列出所有环境")
        print("  python env_switcher.py switch <env>  - 切换到指定环境")
        print("  python env_switcher.py validate      - 验证当前配置")
        print("\n示例:")
        print("  python env_switcher.py switch development")
        print("  python env_switcher.py switch production")
        return
    
    switcher = EnvironmentSwitcher()
    command = sys.argv[1]
    
    if command == 'list':
        switcher.list_environments()
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("❌ 请指定环境名称")
            print(f"支持的环境: {list(switcher.ENVIRONMENTS.keys())}")
            return
        environment = sys.argv[2]
        switcher.switch_environment(environment)
    elif command == 'validate':
        switcher.validate_current_env()
    else:
        print(f"❌ 未知的命令: {command}")
        print("支持的命令: list, switch, validate")

if __name__ == "__main__":
    main()