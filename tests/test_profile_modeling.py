"""
用户画像离线建模模块测试
测试人设真实性验证、内容合规性验证、用户画像分析更新等功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.profile_modeling_service import ProfileModelingService
from app.services.profile_modeling_scheduler import ProfileModelingScheduler
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.user_profile import UserProfile
from app.models.chat_message import ChatMessage


class TestProfileModelingService:
    """测试用户画像建模服务"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_llm_service(self):
        """创建模拟LLM服务"""
        mock = Mock()
        mock.call_llm_api = AsyncMock()
        return mock
    
    @pytest.fixture
    def profile_service(self, mock_db, mock_llm_service):
        """创建用户画像建模服务实例"""
        service = ProfileModelingService(mock_db)
        service.llm_service = mock_llm_service
        return service
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = Mock(spec=User)
        user.id = "1"  # 字符串类型的ID
        user.username = "test_user"
        user.avatar_url = "https://example.com/avatar.jpg"
        user.bio = "我是一个测试用户"
        user.created_at = datetime.now()
        user.gender = 1  # 男
        user.age = 25
        user.location = "北京"
        return user
    
    @pytest.fixture
    def mock_card(self):
        """创建模拟卡片"""
        card = Mock(spec=UserCard)
        card.id = "1"  # 字符串类型的ID
        card.user_id = "1"  # 字符串类型的用户ID
        card.role_type = "virtual_character"
        card.scene_type = "dating"
        card.display_name = "测试角色"
        card.avatar_url = "https://example.com/card_avatar.jpg"
        card.bio = "这是一个测试角色卡片"
        card.visibility = "public"
        card.compliance_status = "pending"
        card.created_at = datetime.now()
        card.preferences = ["阅读", "音乐", "电影"]
        card.tags = ["温柔", "体贴", "浪漫"]
        card.is_active = 1
        return card
    
    @pytest.fixture
    def mock_profile(self):
        """创建模拟用户画像"""
        profile = Mock(spec=UserProfile)
        profile.id = "1"  # 字符串类型的ID
        profile.user_id = "1"  # 字符串类型的用户ID
        profile.preferences = {"兴趣": ["阅读", "音乐"]}
        profile.personality_traits = {"性格": "外向"}
        profile.mood_status = "开心"
        profile.is_active = True
        profile.created_at = datetime.now()
        profile.updated_at = datetime.now()
        return profile
    
    @pytest.mark.asyncio
    async def test_verify_profile_authenticity_success(self, profile_service, mock_user, mock_card, mock_llm_service):
        """测试人设真实性验证成功场景"""
        # 模拟数据库查询 - 用户查询
        profile_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 模拟数据库查询 - 卡片查询
        profile_service.db.query.return_value.filter.return_value.all.return_value = [mock_card]
        
        # 模拟LLM API响应
        from app.models.llm_schemas import LLMResponse
        mock_llm_service.call_llm_api.return_value = LLMResponse(
            success=True,
            data='{"authenticity_score": 85, "risk_level": "low", "details": {"analysis": "用户人设真实度较高", "key_factors": ["头像真实", "简介详细", "行为模式正常"]}, "recommendations": ["继续保持良好的用户行为"]}',
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            duration=1.5
        )
        
        # 执行测试
        result = await profile_service.verify_profile_authenticity("1")
        
        # 验证结果
        assert result["success"] is True
        assert result["authenticity_score"] == 85  # LLM响应中的值
        assert result["risk_level"] == "low"  # LLM响应中的风险等级
        assert len(result["details"]) > 0  # details字段包含分析详情
        assert len(result["recommendations"]) > 0  # recommendations字段包含建议
        
        # 验证LLM服务被调用
        mock_llm_service.call_llm_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_profile_authenticity_user_not_found(self, profile_service, mock_llm_service):
        """测试用户不存在场景"""
        # 模拟数据库查询返回None
        profile_service.db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行测试
        result = await profile_service.verify_profile_authenticity("999")
        
        # 验证结果
        assert result["success"] is False
        assert "用户不存在" in result["error"]
        
        # 验证LLM服务未被调用
        mock_llm_service.call_llm_api.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_profile_authenticity_llm_error(self, profile_service, mock_user, mock_card, mock_llm_service):
        """测试LLM服务异常场景"""
        # 模拟数据库查询 - 用户查询
        profile_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 模拟数据库查询 - 卡片查询
        profile_service.db.query.return_value.filter.return_value.all.return_value = [mock_card]
        
        # 模拟LLM API异常
        mock_llm_service.call_llm_api.side_effect = Exception("LLM服务异常")
        
        # 执行测试
        result = await profile_service.verify_profile_authenticity("1")
        
        # 验证结果
        assert result["success"] is False
        assert "LLM服务异常" in result["error"]
    
    @pytest.mark.asyncio
    async def test_verify_content_compliance_success(self, profile_service, mock_card, mock_llm_service):
        """测试内容合规性验证成功场景"""
        # 模拟数据库查询
        profile_service.db.query.return_value.filter.return_value.first.return_value = mock_card
        
        # 模拟LLM API响应
        from app.models.llm_schemas import LLMResponse
        mock_llm_service.call_llm_api.return_value = LLMResponse(
            success=True,
            data='{"is_compliant": true, "compliance_score": 92, "violations": [], "violation_severity": "none", "recommendations": ["内容质量良好", "继续保持"]}',
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            duration=1.5
        )
        
        # 执行测试
        result = await profile_service.verify_content_compliance(1)
        
        # 验证结果
        assert result["success"] is True
        assert result["is_compliant"] is True
        assert result["compliance_score"] == 92
        assert len(result["violations"]) == 0
        assert len(result["recommendations"]) == 2
    
    @pytest.mark.asyncio
    async def test_verify_content_compliance_violations(self, profile_service, mock_card, mock_llm_service):
        """测试内容违规场景"""
        # 模拟数据库查询
        profile_service.db.query.return_value.filter.return_value.first.return_value = mock_card
        
        # 模拟LLM API响应（包含违规内容）
        from app.models.llm_schemas import LLMResponse
        mock_llm_service.call_llm_api.return_value = LLMResponse(
            success=True,
            data='{"is_compliant": false, "compliance_score": 25, "violations": ["包含不当内容"], "violation_severity": "high", "recommendations": ["请修改个人简介", "避免使用敏感词汇"]}',
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            duration=1.5
        )
        
        # 执行测试
        result = await profile_service.verify_content_compliance(1)
        
        # 验证结果
        assert result["success"] is True
        assert result["is_compliant"] is False
        assert result["compliance_score"] == 25
        assert len(result["violations"]) == 1
        assert result["violations"][0] == "包含不当内容"
    
    @pytest.mark.asyncio
    async def test_update_user_profile_analysis_success(self, profile_service, mock_user, mock_profile, mock_llm_service):
        """测试用户画像更新成功场景"""
        # 模拟数据库查询
        profile_service.db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_profile]
        
        # 模拟激活卡片查询
        profile_service.db.query.return_value.filter.return_value.all.return_value = [
            Mock(spec=UserCard, id=1, user_id=1, status="active", title="我的兴趣", content="喜欢阅读、音乐和电影", 
                 display_name="兴趣卡片", role_type="兴趣", scene_type="个人展示", bio="热爱阅读和音乐", tags=["阅读", "音乐", "电影"])
        ]
        
        # 模拟聊天记录查询
        profile_service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            Mock(spec=ChatMessage, content="我喜欢阅读和音乐", created_at=datetime.now()),
            Mock(spec=ChatMessage, content="今天心情很好", created_at=datetime.now())
        ]
        
        # 模拟LLM API响应
        from app.models.llm_schemas import LLMResponse
        mock_llm_service.call_llm_api.return_value = LLMResponse(
            success=True,
            data='{"confidence_score": 88, "updated_fields": {"preferences": {"兴趣": ["阅读", "音乐", "电影"], "活动": ["户外运动"]}, "personality_traits": {"性格": "外向乐观", "沟通风格": "友好"}, "mood_status": "积极乐观"}, "analysis_summary": "基于用户最近的聊天记录，发现用户对阅读和音乐有浓厚兴趣，性格外向乐观。", "key_insights": ["用户兴趣广泛", "情绪状态良好", "社交活跃度高"], "recommendations": ["推荐更多音乐和阅读相关内容", "鼓励参与社交活动"]}',
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            duration=1.5
        )
        
        # 执行测试
        result = await profile_service.update_user_profile_analysis(1)
        
        # 验证结果
        assert result["success"] is True
        assert result["confidence_score"] == 88
        assert "updated_profile" in result
        assert result["analysis_summary"] == "分析完成"
    
    @pytest.mark.asyncio
    async def test_update_user_profile_analysis_no_data(self, profile_service, mock_user, mock_llm_service):
        """测试没有足够数据更新画像的场景"""
        # 模拟数据库查询
        profile_service.db.query.return_value.filter.return_value.first.side_effect = [mock_user, None]
        
        # 模拟聊天记录查询返回空列表
        profile_service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # 模拟激活卡片查询返回空列表
        profile_service.db.query.return_value.filter.return_value.all.return_value = []
        
        # 执行测试
        result = await profile_service.update_user_profile_analysis(1)
        
        # 验证结果
        assert result["success"] is False
        assert "没有足够的数据进行画像分析" in result["error"]
        
        # 验证LLM服务未被调用
        mock_llm_service.call_llm_api.assert_not_called()


class TestProfileModelingScheduler:
    """测试用户画像建模调度器"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_modeling_service(self):
        """创建模拟建模服务"""
        mock = Mock(spec=ProfileModelingService)
        mock.verify_profile_authenticity = AsyncMock()
        mock.verify_content_compliance = AsyncMock()
        mock.update_user_profile_analysis = AsyncMock()
        return mock
    
    @pytest.fixture
    def scheduler(self, mock_db, mock_modeling_service):
        """创建调度器实例"""
        scheduler = ProfileModelingScheduler(mock_db)
        # 用mock服务替换真实服务
        scheduler.modeling_service = mock_modeling_service
        return scheduler
    
    def test_scheduler_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.is_running is False
        assert "authenticity_verification" in scheduler.task_configs
        assert "content_compliance" in scheduler.task_configs
        assert "profile_update" in scheduler.task_configs
        
        # 验证默认配置
        assert scheduler.task_configs["authenticity_verification"]["enabled"] is True
        assert scheduler.task_configs["authenticity_verification"]["interval_hours"] == 24
        assert scheduler.task_configs["content_compliance"]["interval_hours"] == 12
        assert scheduler.task_configs["profile_update"]["interval_hours"] == 6
    
    def test_task_config_update(self, scheduler):
        """测试任务配置更新"""
        # 更新配置
        new_config = {"interval_hours": 48, "batch_size": 100}
        scheduler.update_task_config("authenticity_verification", new_config)
        
        # 验证配置已更新
        assert scheduler.task_configs["authenticity_verification"]["interval_hours"] == 48
        assert scheduler.task_configs["authenticity_verification"]["batch_size"] == 100
        assert scheduler.task_configs["authenticity_verification"]["enabled"] is True  # 其他配置保持不变
    
    def test_invalid_task_config_update(self, scheduler):
        """测试无效任务配置更新"""
        # 尝试更新不存在的任务
        scheduler.update_task_config("invalid_task", {"enabled": False})
        
        # 验证配置未被修改（应该记录警告日志）
        assert "invalid_task" not in scheduler.task_configs
    
    @pytest.mark.asyncio
    async def test_authenticity_verification_task(self, scheduler, mock_db, mock_modeling_service):
        """测试人设真实性验证任务"""
        # 模拟用户数据
        mock_user = Mock(spec=User)
        mock_user.id = 1
        
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_user]
        
        # 设置建模服务返回值
        mock_modeling_service.verify_profile_authenticity.return_value = {
            "success": True,
            "authenticity_score": 85,
            "analysis_result": "用户人设真实度较高"
        }
        
        # 执行任务
        await scheduler._run_authenticity_verification_task()
        
        # 验证服务被调用
        mock_modeling_service.verify_profile_authenticity.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_content_compliance_task(self, scheduler, mock_db, mock_modeling_service):
        """测试内容合规性验证任务"""
        # 模拟卡片数据
        mock_card = Mock(spec=UserCard)
        mock_card.id = 1
        
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_card]
        
        # 设置建模服务返回值
        mock_modeling_service.verify_content_compliance.return_value = {
            "success": True,
            "is_compliant": True,
            "compliance_score": 92
        }
        
        # 执行任务
        await scheduler._run_content_compliance_task()
        
        # 验证服务被调用
        mock_modeling_service.verify_content_compliance.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_profile_update_task(self, scheduler, mock_db, mock_modeling_service):
        """测试用户画像更新任务"""
        # 模拟用户数据
        mock_user = Mock(spec=User)
        mock_user.id = 1
        
        # 模拟数据库查询 - 使用distinct()简化查询
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.limit.return_value.all.return_value = [mock_user]
        
        # 设置建模服务返回值
        mock_modeling_service.update_user_profile_analysis.return_value = {
            "success": True,
            "confidence_score": 88,
            "updated_fields": {"preferences": {"兴趣": ["阅读"]}}
        }
        
        # 执行任务
        await scheduler._run_profile_update_task()
        
        # 验证服务被调用
        mock_modeling_service.update_user_profile_analysis.assert_called_once_with(1)


class TestProfileModelingIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 这个测试需要实际的数据库和LLM服务
        # 这里提供一个测试框架
        
        # 1. 创建测试用户
        # 2. 创建测试卡片
        # 3. 创建聊天记录
        # 4. 执行人设真实性验证
        # 5. 执行内容合规性验证
        # 6. 执行用户画像更新
        # 7. 验证结果
        
        pass
    
    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self):
        """测试调度器生命周期"""
        # 这个测试需要实际的调度器
        # 这里提供一个测试框架
        
        # 1. 启动调度器
        # 2. 验证任务已添加
        # 3. 停止调度器
        # 4. 验证任务已停止
        
        pass


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])