#!/usr/bin/env python3
"""
测试匿名访问LLM接口的脚本
"""

import asyncio
import httpx
import json
import time

async def test_anonymous_access():
    """测试匿名访问LLM接口"""
    
    print("=== 测试匿名访问LLM接口 ===")
    
    # 测试数据
    test_data = {
        "scene_config_key": "simple-chat",
        "params": {
            "message": "你好，我想测试匿名访问",
            "conversation_history": [],
            "extracted_info": {},
            "dialog_count": 0
        },
        "user_id": "anonymous_test_user",
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # 测试统一的场景化处理接口（非流式）
            print("\n1. 测试 /api/llm/simple-chat/stream 接口（匿名访问）")
            simple_chat_data = {
                "userId": "anonymous_test_user",
                "chatId": "test_chat_anonymous_001",
                "message": "你好，我想测试匿名访问",
                "context": {}
            }
            response = await client.post(
                "http://localhost:8000/api/v1/llm/simple-chat/stream",
                json=simple_chat_data,
                timeout=30.0
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 流式响应，需要逐行解析
                print("✅ 匿名访问成功！")
                print("流式响应数据:")
                full_content = ""
                for line in response.text.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'text':
                                content = data.get('content', '')
                                full_content += content
                                print(f"收到文本: {content}")
                        except json.JSONDecodeError:
                            continue
                print(f"完整内容: {full_content}")
            else:
                print(f"❌ 匿名访问失败: {response.status_code}")
                print(f"错误信息: {response.text}")
            
            # 测试流式接口
            print("\n2. 测试 /api/llm/simple-chat/stream 接口（流式匿名访问）")
            stream_data = {
                "userId": "anonymous_test_user",
                "chatId": "test_chat_anonymous_002",
                "message": "你好，我想测试流式匿名访问",
                "context": {}
            }
            
            start_time = time.time()
            async with client.stream("POST", 
                                   "http://localhost:8000/api/v1/llm/simple-chat/stream",
                                   json=stream_data,
                                   timeout=30.0) as response:
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ 流式连接成功！")
                    print("接收到的数据:")
                    
                    full_content = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "text":
                                    content = data.get("content", "")
                                    full_content += content
                                    print(f"收到文本: {content}")
                                elif data.get("type") == "end":
                                    print("🎯 流式响应结束")
                                    break
                                elif data.get("type") == "error":
                                    print(f"❌ 流式错误: {data.get('message')}")
                                    break
                            except json.JSONDecodeError as e:
                                print(f"解析错误: {e}")
                    
                    elapsed = time.time() - start_time
                    print(f"总耗时: {elapsed:.2f}秒")
                    print(f"完整内容: {full_content}")
                else:
                    print(f"❌ 流式访问失败: {response.status_code}")
                    print(f"错误信息: {await response.text()}")
            
            # 测试对话建议接口
            print("\n3. 测试 /api/v1/llm/conversation-suggestions 接口（匿名访问）")
            suggestion_data = {
                "userId": "anonymous_test_user",
                "cardId": "test_card_123",
                "chatId": "test_chat_456",
                "context": {
                    "userInfo": {"name": "匿名用户", "age": 25},
                    "cardInfo": {"title": "测试卡片", "preferences": ["运动", "音乐"]}
                },
                "conversation_history": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！很高兴见到你。"}
                ],
                "suggestionType": "general",
                "maxSuggestions": 3
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/llm/conversation-suggestions",
                json=suggestion_data,
                timeout=30.0
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 对话建议接口匿名访问成功！")
                print(f"建议数量: {len(result.get('data', {}).get('suggestions', []))}")
            else:
                print(f"❌ 对话建议接口匿名访问失败: {response.text}")
            
            # 测试活动信息提取接口
            print("\n4. 测试 /api/llm/extract-activity-info 接口（匿名访问）")
            extract_data = {
                "user_id": "anonymous_test_user",
                "task_type": "activity_info_extraction",
                "prompt": "请从以下对话中提取用户的活动信息，包括时间、地点和偏好",
                "conversation_history": [
                    {"role": "user", "content": "我喜欢在周末打篮球"},
                    {"role": "assistant", "content": "篮球是很好的运动！你一般在哪个场地打呢？"},
                    {"role": "user", "content": "通常在市中心的体育馆，周六下午2点"}
                ]
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/llm/extract-activity-info",
                json=extract_data,
                timeout=30.0
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 活动信息提取接口匿名访问成功！")
                print(f"提取结果: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
            else:
                print(f"❌ 活动信息提取接口匿名访问失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试匿名访问LLM接口...")
    asyncio.run(test_anonymous_access())
    print("\n测试完成！")