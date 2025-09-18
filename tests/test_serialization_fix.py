#!/usr/bin/env python3
"""
测试Pydantic序列化修复
验证SQLAlchemy对象到Pydantic模型的正确转换
"""

import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, get_db
from app.models.user import User
from app.services.data_adapter import DataService
from app.services.db_service import create_user, update_user
from app.routers.users import update_current_user
from app.models.schemas import BaseResponse
from pydantic import BaseModel
from fastapi import HTTPException


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_serialization.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


class TestSerializationFix:
    """测试序列化修复"""
    
    @classmethod
    def setup_class(cls):
        """设置测试类"""
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        print("清理测试环境...")
        # 关闭数据库连接
        if hasattr(cls, 'engine'):
            cls.engine.dispose()
        
        # 清理测试数据库
        if os.path.exists("./test_serialization.db"):
            try:
                os.remove("./test_serialization.db")
            except PermissionError:
                # Windows下文件可能被占用，等待一下再试
                import time
                time.sleep(0.5)
                try:
                    os.remove("./test_serialization.db")
                except:
                    pass  # 如果还是删除不了就算了
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.db = TestingSessionLocal()
        
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理数据
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()
    
    def test_data_adapter_create_user_serialization(self):
        """测试DataService.create_user的序列化"""
        # 创建测试数据，使用唯一手机号
        import uuid
        user_data = {
            "id": "test_user_001",
            "phone": f"13800{uuid.uuid4().hex[:8]}",
            "nick_name": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "gender": 1,
            "age": 25,
            "bio": "这是一个测试用户",
            "occupation": "工程师",
            "location": '{"city": "北京", "address": "朝阳区"}',
            "education": "本科",
            "interests": '["编程", "阅读", "旅游"]',
            "wechat": "test_wechat",
            "email": "test@example.com",
            "status": "active"
        }
        
        # 使用DataService创建用户
        data_service = DataService()
        result = data_service.create_user(user_data)
        
        # 验证结果不包含SQLAlchemy内部状态
        assert isinstance(result, dict)
        assert "_sa_instance_state" not in result
        assert result["id"] == "test_user_001"
        assert result["nick_name"] == "测试用户"
        
        # 验证可以序列化为JSON（通过Pydantic BaseResponse）
        response = BaseResponse(code=0, message="success", data=result)
        # 如果序列化失败，这里会抛出异常
        json_data = response.model_dump()
        assert json_data["data"]["id"] == "test_user_001"
    
    def test_data_adapter_get_user_by_id_serialization(self):
        """测试DataService.get_user_by_id的序列化"""
        # 先创建一个用户
        user_data = {
            "id": "test_user_002",
            "phone": "13800138001",
            "nick_name": "测试用户2",
            "avatar_url": "https://example.com/avatar2.jpg",
            "gender": 2,
            "age": 24,
            "bio": "这是另一个测试用户",
            "status": "active"
        }
        
        create_user(self.db, user_data)
        
        # 使用DataService获取用户
        data_service = DataService()
        result = data_service.get_user_by_id("test_user_002")
        
        # 验证结果不包含SQLAlchemy内部状态
        assert isinstance(result, dict)
        assert "_sa_instance_state" not in result
        assert result["id"] == "test_user_002"
        assert result["nickName"] == "测试用户2"  # 注意：这里是nickName（驼峰命名）
        
        # 验证可以序列化为JSON
        response = BaseResponse(code=0, message="success", data=result)
        json_data = response.model_dump()
        assert json_data["data"]["nickName"] == "测试用户2"
    
    def test_db_service_functions_return_clean_objects(self):
        """测试数据库服务函数返回的对象可以被正确序列化"""
        # 创建用户
        user_data = {
            "id": "test_user_003",
            "phone": "13800138002",
            "nick_name": "测试用户3",
            "status": "active"
        }
        
        user = create_user(self.db, user_data)
        
        # 验证用户对象可以被安全序列化
        user_dict = user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        
        # 验证可以序列化为JSON
        response = BaseResponse(code=0, message="success", data=user_dict)
        json_data = response.model_dump()
        assert json_data["data"]["id"] == "test_user_003"
    
    def test_user_update_serialization(self):
        """测试用户更新操作的序列化"""
        # 先创建一个用户
        import uuid
        user_data = {
            "id": "test_user_004",
            "phone": f"13800{uuid.uuid4().hex[:8]}",
            "nick_name": "原始昵称",
            "status": "active"
        }
        
        user = create_user(self.db, user_data)
        
        # 更新用户数据
        update_data = {"nick_name": "更新后的昵称", "age": 30}
        updated_user = update_user(self.db, "test_user_004", update_data)
        
        # 验证更新后的对象可以被安全序列化
        user_dict = updated_user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        
        # 验证可以序列化为JSON
        response = BaseResponse(code=0, message="success", data=user_dict)
        json_data = response.model_dump()
        assert json_data["data"]["nick_name"] == "更新后的昵称"
        assert json_data["data"]["age"] == 30
    
    def test_complex_data_structure_serialization(self):
        """测试复杂数据结构的序列化"""
        # 创建包含各种数据类型的用户
        user_data = {
            "id": "test_user_005",
            "phone": "13800138004",
            "nick_name": "复杂用户",
            "location": '{"city": "上海", "district": "浦东新区", "coordinates": [121.5, 31.2]}',
            "interests": '["编程", "机器学习", "区块链", "物联网"]',
            "bio": "我是一个对技术充满热情的开发者，\n喜欢探索新技术和解决复杂问题。",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        user = create_user(self.db, user_data)
        
        # 验证复杂数据可以被安全序列化
        user_dict = user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        
        # 验证可以序列化为JSON
        response = BaseResponse(code=0, message="success", data=user_dict)
        json_data = response.model_dump()
        
        # 验证复杂字段
        assert json_data["data"]["id"] == "test_user_005"
        assert "上海" in json_data["data"]["location"]
        assert len(json_data["data"]["interests"]) == 4
        assert "技术" in json_data["data"]["bio"]
    
    def test_error_handling_with_serialization(self):
        """测试错误处理时的序列化"""
        # 尝试获取不存在的用户
        data_service = DataService()
        result = data_service.get_user_by_id("non_existent_user")
        
        # 验证返回None而不是抛出异常
        assert result is None
        
        # 验证错误响应也可以被正确序列化
        response = BaseResponse(code=404, message="用户不存在", data=None)
        json_data = response.model_dump()
        assert json_data["code"] == 404
        assert json_data["message"] == "用户不存在"
        assert json_data["data"] is None


def test_serialization_with_pydantic_core():
    """测试Pydantic核心序列化功能"""
    # 测试各种数据类型的序列化
    test_data = {
        "string": "test_string",
        "integer": 42,
        "float": 3.14159,
        "boolean": True,
        "null_value": None,
        "datetime": datetime.now(),
        "list": [1, 2, 3, "four", 5.5],
        "dict": {"nested": {"value": "test"}},
        "empty_dict": {},
        "empty_list": []
    }
    
    # 创建BaseResponse对象
    response = BaseResponse(code=0, message="success", data=test_data)
    
    # 验证可以成功序列化
    json_data = response.model_dump()
    
    # 验证所有数据类型都正确序列化
    assert json_data["data"]["string"] == "test_string"
    assert json_data["data"]["integer"] == 42
    assert json_data["data"]["float"] == 3.14159
    assert json_data["data"]["boolean"] is True
    assert json_data["data"]["null_value"] is None
    # datetime可能被序列化为字符串或保持为datetime对象，取决于Pydantic版本
    datetime_value = json_data["data"]["datetime"]
    assert isinstance(datetime_value, (str, datetime))  # 接受字符串或datetime对象
    assert len(json_data["data"]["list"]) == 5
    assert json_data["data"]["dict"]["nested"]["value"] == "test"


if __name__ == "__main__":
    # 运行基本测试
    print("运行序列化修复测试...")
    
    # 测试Pydantic核心功能
    test_serialization_with_pydantic_core()
    print("✓ Pydantic核心序列化测试通过")
    
    # 运行数据库相关测试
    test_class = TestSerializationFix()
    test_class.setup_class()
    
    try:
        test_class.setup_method()
        test_class.test_data_adapter_create_user_serialization()
        print("✓ DataService.create_user序列化测试通过")
        test_class.teardown_method()
        
        test_class.setup_method()
        test_class.test_data_adapter_get_user_by_id_serialization()
        print("✓ DataService.get_user_by_id序列化测试通过")
        test_class.teardown_method()
        
        test_class.setup_method()
        test_class.test_db_service_functions_return_clean_objects()
        print("✓ 数据库服务函数序列化测试通过")
        test_class.teardown_method()
        
        test_class.setup_method()
        test_class.test_user_update_serialization()
        print("✓ 用户更新序列化测试通过")
        test_class.teardown_method()
        
        test_class.setup_method()
        test_class.test_complex_data_structure_serialization()
        print("✓ 复杂数据结构序列化测试通过")
        test_class.teardown_method()
        
        test_class.setup_method()
        test_class.test_error_handling_with_serialization()
        print("✓ 错误处理序列化测试通过")
        test_class.teardown_method()
        
    finally:
        test_class.teardown_class()
    
    print("\n🎉 所有序列化测试通过！Pydantic序列化错误已修复。")