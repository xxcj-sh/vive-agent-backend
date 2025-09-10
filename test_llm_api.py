#!/usr/bin/env python3
"""
测试LLM API的脚本
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"✅ API文档页面: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

def test_llm_endpoints():
    """测试LLM相关端点"""
    endpoints = [
        "/llm/analyze-profile",
        "/llm/analyze-interests", 
        "/llm/analyze-chat",
        "/llm/ask",
        "/llm/usage-logs",
        "/llm/usage-stats"
    ]
    
    print("🔍 测试LLM端点...")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/docs")
            if endpoint.replace("/", "_") in response.text:
                print(f"✅ {endpoint}")
            else:
                print(f"⚠️  {endpoint} (可能未完全加载)")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    print("🚀 测试LLM API...")
    
    if test_api_health():
        test_llm_endpoints()
        print("\n🎉 测试完成！")
        print("📋 访问 http://localhost:8001/docs 查看完整API文档")
    else:
        print("❌ 请确保服务已启动")