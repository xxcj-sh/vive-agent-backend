#!/usr/bin/env python3
"""
测试大语言模型模块
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.services.llm_service import LLMService
from app.models.llm_schemas import ProfileAnalysisRequest, QuestionAnsweringRequest
from app.models.llm_usage_log import LLMProvider, LLMTaskType

async def test_llm_service():
    """测试LLM服务"""
    print("🧪 开始测试大语言模型服务...")
    
    try:
        # 创建LLM服务实例
        service = LLMService()
        
        # 测试1: 用户资料分析
        print("\n📊 测试用户资料分析...")
        profile_request = ProfileAnalysisRequest(
            user_id="test_user_001",
            profile_data={
                "name": "张三",
                "age": 28,
                "interests": ["阅读", "旅行", "摄影"],
                "occupation": "软件工程师",
                "location": "北京"
            }
        )
        
        result = await service.analyze_user_profile(profile_request)
        print(f"✅ 用户资料分析结果: {result}")
        
        # 测试2: 兴趣分析
        print("\n🎯 测试兴趣分析...")
        interest_request = ProfileAnalysisRequest(
            user_id="test_user_001",
            profile_data={
                "interests": ["阅读", "旅行", "摄影", "美食", "音乐"],
                "recent_activities": ["周末去故宫拍照", "参加读书会", "学习法语"]
            }
        )
        
        result = await service.analyze_user_interests(interest_request)
        print(f"✅ 兴趣分析结果: {result}")
        
        # 测试3: 问题回答
        print("\n❓ 测试问题回答...")
        qa_request = QuestionAnsweringRequest(
            user_id="test_user_001",
            question="我应该如何提升我的摄影技巧？",
            context={
                "user_interests": ["摄影", "旅行"],
                "skill_level": "中级"
            }
        )
        
        result = await service.answer_question(qa_request)
        print(f"✅ 问题回答结果: {result}")
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_service())