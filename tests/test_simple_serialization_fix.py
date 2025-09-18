#!/usr/bin/env python3
"""
简化版序列化修复测试
测试修复 PydanticSerializationError: Unable to serialize unknown type: <class 'sqlalchemy.orm.state.InstanceState'>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import json

# 模拟 BaseResponse
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

# 模拟 SQLAlchemy 实例状态对象
class MockInstanceState:
    """模拟 SQLAlchemy 的 InstanceState 对象"""
    def __init__(self):
        self.class_name = "User"
        self.identity = "test_user"

# 模拟 SQLAlchemy 模型对象
class MockUser:
    """模拟 SQLAlchemy 用户模型对象"""
    def __init__(self):
        self.id = "test_user_001"
        self.phone = "13800138000"
        self.nick_name = "测试用户"
        self.avatar_url = "https://example.com/avatar.jpg"
        self.gender = 1
        self.age = 25
        self.bio = "这是一个测试用户"
        self.occupation = "工程师"
        self.location = '{"city": "北京", "address": "朝阳区"}'
        self.education = "本科"
        self.interests = '["编程", "阅读", "旅游"]'
        self.wechat = "test_wechat"
        self.email = "test@example.com"
        self.status = "active"
        self.level = 1
        self.points = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        # 模拟 SQLAlchemy 实例状态（这是导致问题的对象）
        self._sa_instance_state = MockInstanceState()

def test_original_problem():
    """测试原始问题：直接使用 __dict__ 会导致序列化错误"""
    print("测试原始问题...")
    
    user = MockUser()
    
    # 原始有问题的代码：直接使用 __dict__
    user_dict = user.__dict__
    
    print(f"用户字典包含 _sa_instance_state: {'_sa_instance_state' in user_dict}")
    print(f"_sa_instance_state 类型: {type(user_dict['_sa_instance_state'])}")
    
    try:
        # 这会失败，因为 InstanceState 无法被序列化
        response = BaseResponse(data=user_dict)
        json_str = response.model_dump_json()
        print("❌ 不应该成功，但序列化通过了")
        return False
    except Exception as e:
        print(f"✅ 预期错误: {type(e).__name__}: {e}")
        return True

def test_fixed_version():
    """测试修复后的版本"""
    print("\n测试修复后的版本...")
    
    user = MockUser()
    
    # 修复后的代码：复制字典并移除 _sa_instance_state
    user_dict = user.__dict__.copy()
    user_dict.pop('_sa_instance_state', None)  # 安全移除
    
    print(f"用户字典包含 _sa_instance_state: {'_sa_instance_state' in user_dict}")
    
    try:
        # 这应该成功
        response = BaseResponse(data=user_dict)
        json_str = response.model_dump_json()
        print("✅ 序列化成功")
        
        # 验证JSON内容
        parsed = json.loads(json_str)
        print(f"响应数据: {parsed['data']['nick_name']}")
        print(f"包含 _sa_instance_state: {'_sa_instance_state' in parsed['data']}")
        
        return True
    except Exception as e:
        print(f"❌ 意外错误: {type(e).__name__}: {e}")
        return False

def test_data_adapter_pattern():
    """测试数据适配器模式"""
    print("\n测试数据适配器模式...")
    
    user = MockUser()
    
    # 模拟 app/services/data_adapter.py 中的模式
    def create_user_response(user_obj):
        """模拟数据适配器的用户创建响应"""
        user_dict = user_obj.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        return user_dict
    
    def get_user_by_id_response(user_obj):
        """模拟数据适配器的用户查询响应"""
        user_dict = user_obj.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        
        # 映射数据库字段到前端字段
        return {
            "id": user_dict["id"],
            "phone": user_dict["phone"],
            "nickName": user_dict["nick_name"],
            "avatarUrl": user_dict["avatar_url"],
            "gender": user_dict["gender"],
            "age": user_dict["age"],
            "bio": user_dict["bio"],
            "occupation": user_dict["occupation"],
            "location": user_dict["location"],
            "education": user_dict["education"],
            "interests": user_dict["interests"],
            "wechat": user_dict["wechat"],
            "email": user_dict["email"],
            "status": user_dict["status"],
            "level": user_dict["level"],
            "points": user_dict["points"]
        }
    
    # 测试创建用户响应
    try:
        create_result = create_user_response(user)
        response1 = BaseResponse(data=create_result)
        json1 = response1.model_dump_json()
        print("✅ 创建用户响应序列化成功")
        
        # 测试查询用户响应
        get_result = get_user_by_id_response(user)
        response2 = BaseResponse(data=get_result)
        json2 = response2.model_dump_json()
        print("✅ 查询用户响应序列化成功")
        
        return True
    except Exception as e:
        print(f"❌ 数据适配器模式错误: {type(e).__name__}: {e}")
        return False

def test_pydantic_model_pattern():
    """测试Pydantic模型模式"""
    print("\n测试Pydantic模型模式...")
    
    # 模拟 app/models/user_card.py 中的 Card 模型
    class Card(BaseModel):
        id: str
        phone: str
        nickName: str
        avatarUrl: str
        gender: int
        age: int
        bio: str
        occupation: str
        location: str
        education: str
        interests: str
        wechat: str
        email: str
        status: str
        level: int
        points: int
        
        class Config:
            from_attributes = True  # 允许从ORM对象创建
    
    user = MockUser()
    
    try:
        # 使用 from_attributes=True 应该能正确处理
        card = Card.model_validate(user)
        response = BaseResponse(data=card)
        json_str = response.model_dump_json()
        print("✅ Pydantic模型序列化成功")
        
        # 验证字段映射
        parsed = json.loads(json_str)
        print(f"卡片昵称: {parsed['data']['nickName']}")
        
        return True
    except Exception as e:
        print(f"❌ Pydantic模型错误: {type(e).__name__}: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Pydantic 序列化修复测试")
    print("=" * 60)
    
    results = []
    
    # 测试1：原始问题
    results.append(test_original_problem())
    
    # 测试2：修复版本
    results.append(test_fixed_version())
    
    # 测试3：数据适配器模式
    results.append(test_data_adapter_pattern())
    
    # 测试4：Pydantic模型模式
    results.append(test_pydantic_model_pattern())
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"总测试数: {len(results)}")
    print(f"通过测试: {sum(results)}")
    print(f"失败测试: {len(results) - sum(results)}")
    
    if all(results):
        print("✅ 所有测试通过！序列化修复有效。")
    else:
        print("❌ 部分测试失败，需要进一步修复。")
    
    print("=" * 60)

if __name__ == "__main__":
    main()