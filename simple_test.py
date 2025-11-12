"""简单测试脚本，直接测试API端点"""
import requests
import json

BASE_URL = "http://192.168.0.102:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n测试 {method} {url}")
    
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=json.dumps(data) if data else None)
        
        print(f"状态码: {response.status_code}")
        
        # 尝试解析JSON响应
        try:
            response_json = response.json()
            print(f"响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应内容: {response.text}")
        
        return response.status_code
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None

def run_tests():
    """运行所有测试"""
    print("开始简单API测试...")
    
    # 测试根路径
    test_endpoint("/")
    
    # 测试健康检查
    test_endpoint("/health")
    
    # 测试API信息
    test_endpoint("/api/v1")
    
    # 测试聊天路由
    test_endpoint("/api/v1/chats")
    
    # 测试发送消息（匿名）
    test_endpoint(
        endpoint="/api/v1/chats/test_chat_id/messages",
        method="POST",
        data={
            "content": "测试匿名消息",
            "type": "text",
            "is_anonymous": True
        }
    )
    
    print("\n测试完成！")

if __name__ == "__main__":
    run_tests()