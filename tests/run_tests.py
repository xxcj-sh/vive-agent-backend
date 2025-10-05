#!/usr/bin/env python3
"""
测试运行器
用于运行所有服务测试或指定测试模块
"""

import sys
import os
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有测试"""
    print("🧪 运行所有服务测试...")
    
    # 测试参数
    test_args = [
        "-v",  # 详细输出
        "--tb=short",  # 简短错误信息
        "--color=yes",  # 彩色输出
        "tests/services/"
    ]
    
    # 运行测试
    exit_code = pytest.main(test_args)
    
    return exit_code

def run_specific_test(test_file):
    """运行指定测试文件"""
    print(f"🧪 运行测试文件: {test_file}")
    
    test_args = [
        "-v",
        "--tb=short",
        "--color=yes",
        test_file
    ]
    
    exit_code = pytest.main(test_args)
    
    return exit_code

def run_test_by_pattern(pattern):
    """按模式运行测试"""
    print(f"🧪 运行匹配模式的测试: {pattern}")
    
    test_args = [
        "-v",
        "--tb=short",
        "--color=yes",
        "-k", pattern,
        "tests/services/"
    ]
    
    exit_code = pytest.main(test_args)
    
    return exit_code

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 无参数，运行所有测试
        exit_code = run_all_tests()
    elif sys.argv[1] == "--help":
        print("""
用法: python run_tests.py [选项] [参数]

选项:
    --all           运行所有测试 (默认)
    --file FILE     运行指定测试文件
    --pattern PATTERN 运行匹配模式的测试
    --help          显示帮助信息

示例:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --file tests/services/test_auth.py  # 运行认证服务测试
    python run_tests.py --pattern "test_login"  # 运行包含test_login的测试
        """)
        exit_code = 0
    elif sys.argv[1] == "--all":
        exit_code = run_all_tests()
    elif sys.argv[1] == "--file" and len(sys.argv) > 2:
        exit_code = run_specific_test(sys.argv[2])
    elif sys.argv[1] == "--pattern" and len(sys.argv) > 2:
        exit_code = run_test_by_pattern(sys.argv[2])
    else:
        print("❌ 无效的参数。使用 --help 查看用法。")
        exit_code = 1
    
    # 根据退出码显示结果
    if exit_code == 0:
        print("\n✅ 所有测试通过！")
    else:
        print(f"\n❌ 测试失败，退出码: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())