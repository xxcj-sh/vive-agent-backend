"""
测试对话建议功能
"""

import os
import sys
import json
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import get_db
from app.services.llm_service import LLMService
from app.models.llm_usage_log import LLMProvider, LLMTaskType

async def test_conversation_suggestion():
    """测试生成对话建议功能"""
    print("开始测试对话建议功能...")
    
    # 创建数据库会话
    db = next(get_db())
    
    try:
        # 初始化LLM服务
        llm_service = LLMService(db)
        
        # 准备测试数据
        user_id = "test_user_123"
        chat_id = "test_chat_456"
        context = {
            "userPersonality": {
                "性格": "开朗活泼",
                "沟通风格": "直接友好"
            },
            "chatHistory": [
                {"role": "user", "content": "你好，最近过得怎么样？"},
                {"role": "assistant", "content": "我很好，谢谢！你最近在忙什么呢？"},
                {"role": "user", "content": "我最近在学习编程，感觉很有意思。"}
            ]
        }
        suggestion_type = "reply"
        max_suggestions = 3
        
        # 调用对话建议生成方法，使用模拟模式
        response = await llm_service.generate_conversation_suggestion(
            user_id=user_id,
            chatId=chat_id,
            context=context,
            suggestionType=suggestion_type,
            maxSuggestions=max_suggestions,
            provider=LLMProvider.CUSTOM,  # 使用CUSTOM提供商来触发模拟API
            model_name="mock-model"
        )
        
        # 打印结果
        print(f"\n测试结果:")
        print(f"成功状态: {response.success}")
        print(f"生成的建议数量: {len(response.suggestions)}")
        print(f"置信度: {response.confidence}")
        print(f"Token使用: {response.usage}")
        print(f"处理耗时: {response.duration:.2f}秒")
        
        print(f"\n生成的建议:")
        for i, suggestion in enumerate(response.suggestions, 1):
            print(f"{i}. {suggestion}")
            
        print("\n测试完成！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    finally:
        # 关闭数据库会话
        db.close()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_conversation_suggestion())