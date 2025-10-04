#!/usr/bin/env python3
"""
数据库配置安全检查脚本
用于检查数据库配置的安全性并提供改进建议
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.config import settings
except ImportError:
    print("❌ 无法导入配置文件，请确保在正确的目录下运行")
    sys.exit(1)

class DatabaseSecurityChecker:
    """数据库配置安全检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_environment_variables(self) -> Dict[str, str]:
        """检查环境变量配置"""
        env_vars = {
            'ENVIRONMENT': os.getenv('ENVIRONMENT', '未设置'),
            'DATABASE_URL': os.getenv('DATABASE_URL', '未设置'),
            'MYSQL_HOST': os.getenv('MYSQL_HOST', '未设置'),
            'MYSQL_PORT': os.getenv('MYSQL_PORT', '未设置'),
            'MYSQL_USERNAME': os.getenv('MYSQL_USERNAME', '未设置'),
            'MYSQL_PASSWORD': '已设置' if os.getenv('MYSQL_PASSWORD') else '未设置',
            'MYSQL_DATABASE': os.getenv('MYSQL_DATABASE', '未设置'),
            'SECRET_KEY': '已设置' if os.getenv('SECRET_KEY') and os.getenv('SECRET_KEY') != 'your_secret_key_here' else '未设置或默认值',
        }
        return env_vars
    
    def check_security_issues(self) -> List[Tuple[str, str, str]]:
        """检查安全问题"""
        issues = []
        
        # 检查SECRET_KEY
        if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'your_secret_key_here':
            issues.append(('CRITICAL', 'SECRET_KEY', '使用了默认或空的SECRET_KEY，存在严重的安全风险'))
        
        # 检查数据库密码
        if settings.ENVIRONMENT == 'production':
            if not settings.mysql_password:
                issues.append(('CRITICAL', 'MySQL密码', '生产环境未设置数据库密码'))
            elif len(settings.mysql_password) < 8:
                issues.append(('HIGH', 'MySQL密码', '生产环境数据库密码太短（应至少8位）'))
        
        # 检查数据库主机
        if settings.ENVIRONMENT == 'production':
            if settings.mysql_host in ['localhost', '127.0.0.1']:
                issues.append(('MEDIUM', 'MySQL主机', '生产环境使用本地数据库主机'))
        
        # 检查数据库URL中的敏感信息
        db_url = settings.database_url
        if '@' in db_url and ':' in db_url:
            # 检查是否包含默认密码
            if ':@' in db_url or ':password@' in db_url.lower():
                issues.append(('HIGH', '数据库URL', '数据库连接URL可能包含默认或空密码'))
        
        # 检查用户名
        if settings.mysql_username == 'root' and settings.ENVIRONMENT == 'production':
            issues.append(('MEDIUM', 'MySQL用户名', '生产环境使用root用户，建议创建专用用户'))
        
        return issues
    
    def check_environment_separation(self) -> List[str]:
        """检查环境分离"""
        warnings = []
        
        # 检查数据库名称
        if settings.ENVIRONMENT == 'production' and 'dev' in settings.mysql_database:
            warnings.append('生产环境数据库名称包含开发标识(dev)')
        
        if settings.ENVIRONMENT == 'development' and 'prod' in settings.mysql_database:
            warnings.append('开发环境数据库名称包含生产标识(prod)')
        
        # 检查主机分离
        if settings.ENVIRONMENT == 'production' and settings.mysql_host == 'localhost':
            warnings.append('生产环境使用本地数据库，建议分离')
        
        return warnings
    
    def generate_security_recommendations(self) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if settings.ENVIRONMENT == 'production':
            recommendations.extend([
                '使用强密码策略（至少12位，包含大小写字母、数字和特殊字符）',
                '为不同环境创建独立的数据库用户',
                '启用数据库SSL连接',
                '配置数据库访问白名单',
                '定期轮换数据库密码',
                '使用专用的密码管理工具',
                '启用数据库审计日志',
                '配置数据库连接加密'
            ])
        else:
            recommendations.extend([
                '开发环境也建议使用密码保护',
                '避免在代码中硬编码敏感信息',
                '使用环境变量管理配置',
                '定期更新开发环境密码'
            ])
        
        return recommendations
    
    def print_report(self):
        """打印安全检查报告"""
        print("=" * 60)
        print("🔒 VMatch 数据库配置安全检查报告")
        print("=" * 60)
        
        # 环境信息
        print(f"\n📋 环境信息:")
        print(f"   当前环境: {settings.ENVIRONMENT}")
        print(f"   数据库主机: {settings.mysql_host}")
        print(f"   数据库名: {settings.mysql_database}")
        print(f"   数据库用户: {settings.mysql_username}")
        
        # 环境变量状态
        print(f"\n🔧 环境变量配置:")
        env_vars = self.check_environment_variables()
        for var, value in env_vars.items():
            status = "✅" if value not in ['未设置', '未设置或默认值'] else "❌"
            print(f"   {status} {var}: {value}")
        
        # 安全问题
        print(f"\n🚨 安全问题:")
        issues = self.check_security_issues()
        if issues:
            for severity, field, description in issues:
                severity_icon = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(severity, '⚪')
                print(f"   {severity_icon} [{severity}] {field}: {description}")
        else:
            print("   ✅ 未发现严重的安全问题")
        
        # 环境分离警告
        print(f"\n⚠️  环境分离检查:")
        warnings = self.check_environment_separation()
        if warnings:
            for warning in warnings:
                print(f"   🟡 {warning}")
        else:
            print("   ✅ 环境分离配置正确")
        
        # 安全建议
        print(f"\n💡 安全建议:")
        recommendations = self.generate_security_recommendations()
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # 快速修复指南
        print(f"\n🔧 快速修复指南:")
        print(f"   1. 复制环境变量模板: cp .env.example .env")
        print(f"   2. 编辑 .env 文件，设置安全的配置值")
        print(f"   3. 确保生产环境使用强密码和SECRET_KEY")
        print(f"   4. 重启应用以应用新配置")
        
        print("\n" + "=" * 60)
        
        # 总体安全评级
        critical_count = sum(1 for s, _, _ in issues if s == 'CRITICAL')
        high_count = sum(1 for s, _, _ in issues if s == 'HIGH')
        
        if critical_count > 0:
            print("🔴 安全评级: 严重 - 存在关键安全问题，需要立即修复！")
        elif high_count > 0:
            print("🟠 安全评级: 高风险 - 存在重要安全问题，建议尽快修复")
        elif issues:
            print("🟡 安全评级: 中等风险 - 存在一些安全问题，建议修复")
        else:
            print("🟢 安全评级: 良好 - 基础安全配置正确")
        
        print("=" * 60)

def main():
    """主函数"""
    checker = DatabaseSecurityChecker()
    checker.print_report()

if __name__ == "__main__":
    main()