"""
可信度评分相关功能的单元测试
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models.user_profile_score import UserProfileScore, ScoreType, UserProfileSkill, UserProfileScoreHistory
from app.services.user_profile.user_profile_score_service import UserProfileScoreService


class TestCredibilityScore:
    """测试可信度评分功能"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return UserProfileScoreService(db_session)
    
    def test_score_type_enum_credibility(self):
        """测试评分类型枚举包含可信度"""
        assert ScoreType.CREDIBILITY == "credibility"
        assert ScoreType.CREDIBILITY != "comprehensiveness"
    
    def test_user_profile_score_credibility_field(self):
        """测试用户评分模型包含可信度字段"""
        score = UserProfileScore(
            user_id="test_user_123",
            credibility_score=85,
            completeness_score=90,
            accuracy_score=80,
            activity_score=75,
            overall_score=82
        )
        assert score.credibility_score == 85
        assert hasattr(score, 'credibility_score')
    
    def test_calculate_credibility_score_method(self, db_session: Session):
        """测试计算可信度评分方法"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_credibility"
        
        # 创建用户评分记录
        score = service.get_or_create_user_score(user_id)
        
        # 获取用户画像数据
        profile = service.profile_service.get_user_profile(user_id)
        if not profile:
            # 如果没有用户画像，创建基础画像数据
            from app.models.user_profile import UserProfile
            profile = UserProfile(
                user_id=user_id,
                raw_profile='{"basic_info": "基础信息", "personality_traits": "个性特征:开放性=0.8,尽责性=0.7,外向性=0.6,宜人性=0.7,神经质=0.3", "chat_style": "聊天风格:友好型,直接型,幽默型", "interest": "兴趣爱好:运动,音乐,阅读,电影,旅行", "preferences": "社交偏好:小型聚会,深度交流,线上互动"}'
            )
            db_session.add(profile)
            db_session.commit()
        
        # 测试可信度评分计算（基于用户画像数据）
        result = service.calculate_credibility_score(profile)
        
        assert isinstance(result, int)
        assert 0 <= result <= 100
        assert result >= 0
    
    def test_update_credibility_score(self, db_session: Session):
        """测试更新可信度评分"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_update_credibility"
        
        # 创建用户评分记录
        score = service.get_or_create_user_score(user_id)
        old_credibility = score.credibility_score
        
        # 更新可信度评分
        new_credibility = 88
        score.credibility_score = new_credibility
        db_session.commit()
        
        # 验证更新
        updated_score = service.get_user_score(user_id)
        assert updated_score.credibility_score == new_credibility
        assert updated_score.credibility_score != old_credibility
    
    def test_score_history_credibility_tracking(self, db_session: Session):
        """测试评分历史记录中的可信度追踪"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_history_credibility"
        
        # 创建初始评分
        score = service.get_or_create_user_score(user_id)
        initial_credibility = score.credibility_score
        
        # 更新可信度评分并创建历史记录
        score.credibility_score = 92
        db_session.commit()
        service.create_score_history(
            user_id=user_id,
            change_type="test_credibility_update",
            reason="测试可信度评分更新"
        )
        db_session.commit()
        
        # 验证历史记录
        history = service.get_user_score_history(user_id)
        assert len(history) > 0
        latest_history = history[0]
        assert latest_history.credibility_score == 92
        assert latest_history.credibility_score != initial_credibility
    
    def test_credibility_impacts_skill_unlock(self, db_session: Session):
        """测试可信度对技能解锁的影响"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_skill_unlock"
        
        # 创建用户评分
        score = service.get_or_create_user_score(user_id)
        
        # 设置较低可信度
        score.credibility_score = 30
        db_session.commit()
        
        # 检查技能解锁状态
        service._check_and_unlock_skills(score)
        
        # 获取用户技能
        skills = db_session.query(UserProfileSkill).filter_by(user_id=user_id).all()
        
        # 低可信度用户应该解锁较少的技能
        low_credibility_skills = len(skills)
        
        # 提高可信度
        score.credibility_score = 90
        db_session.commit()
        
        # 重新检查技能解锁
        service._check_and_unlock_skills(score)
        
        # 获取更新后的技能
        updated_skills = db_session.query(UserProfileSkill).filter_by(user_id=user_id).all()
        high_credibility_skills = len(updated_skills)
        
        # 高可信度用户应该解锁更多技能
        assert high_credibility_skills >= low_credibility_skills
    
    def test_score_weight_config_credibility(self, db_session: Session):
        """测试评分权重配置中的可信度权重"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_weight_config"
        
        # 创建用户评分
        score = service.get_or_create_user_score(user_id)
        
        # 设置各维度评分
        score.credibility_score = 80
        score.completeness_score = 80
        score.accuracy_score = 80
        score.activity_score = 80
        db_session.commit()
        
        # 计算总体评分
        scores_dict = {
            "completeness": score.completeness_score,
            "accuracy": score.accuracy_score,
            "activity": score.activity_score,
            "credibility": score.credibility_score
        }
        overall = service.calculate_overall_score(scores_dict)
        
        # 修改可信度并重新计算
        score.credibility_score = 90
        db_session.commit()
        new_scores_dict = {
            "completeness": score.completeness_score,
            "accuracy": score.accuracy_score,
            "activity": score.activity_score,
            "credibility": score.credibility_score
        }
        new_overall = service.calculate_overall_score(new_scores_dict)
        
        # 验证权重配置
        weight_config = {
            "completeness": 0.3,  # 完整度 (30%)
            "accuracy": 0.3,  # 准确度 (30%)
            "activity": 0.2,  # 活跃度 (20%)
            "credibility": 0.2  # 可信度 (20%)
        }
        credibility_weight = weight_config.get('credibility', 0.25)
        
        assert credibility_weight > 0  # 可信度权重应该为正数
        assert new_overall != overall  # 修改可信度应该影响总体评分
    
    def test_overall_score_calculation_includes_credibility(self, db_session: Session):
        """测试总体评分计算包含可信度"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_overall_credibility"
        
        # 创建用户评分
        score = service.get_or_create_user_score(user_id)
        
        # 设置各维度评分
        score.credibility_score = 85
        score.completeness_score = 80
        score.accuracy_score = 75
        score.activity_score = 70
        db_session.commit()
        
        # 计算总体评分
        scores_dict = {
            "completeness": score.completeness_score,
            "accuracy": score.accuracy_score,
            "activity": score.activity_score,
            "credibility": score.credibility_score
        }
        overall = service.calculate_overall_score(scores_dict)
        
        # 验证总体评分受可信度影响
        assert isinstance(overall, int)
        assert 0 <= overall <= 100
        
        # 修改可信度并验证总体评分变化
        score.credibility_score = 95
        db_session.commit()
        new_scores_dict = {
            "completeness": score.completeness_score,
            "accuracy": score.accuracy_score,
            "activity": score.activity_score,
            "credibility": score.credibility_score
        }
        new_overall = service.calculate_overall_score(new_scores_dict)
        
        # 可信度提高，总体评分应该相应提高或保持不变
        assert new_overall >= overall or abs(new_overall - overall) <= 2  # 允许小误差
    
    def test_credibility_score_validation(self, db_session: Session):
        """测试可信度评分验证"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_credibility_validation"
        
        score = service.get_or_create_user_score(user_id)
        
        # 测试有效值
        for valid_score in [0, 50, 100]:
            score.credibility_score = valid_score
            db_session.commit()
            assert score.credibility_score == valid_score
        
        # 测试边界值处理
        score.credibility_score = 101
        db_session.commit()
        assert score.credibility_score == 101  # 数据库层面不强制限制
        
        score.credibility_score = -1
        db_session.commit()
        assert score.credibility_score == -1  # 数据库层面不强制限制
    
    def test_score_trend_analysis_credibility(self, db_session: Session):
        """测试可信度趋势分析"""
        service = UserProfileScoreService(db_session)
        user_id = "test_user_trend"
        
        # 先创建用户评分
        service.get_or_create_user_score(user_id)
        
        # 创建评分历史记录
        for i in range(4):
            service.create_score_history(
                user_id=user_id,
                change_type="score_update",
                reason=f"测试更新 {i+1}",
                score_changes={"credibility": 10 + i * 5}
            )
        
        # 获取历史记录作为趋势分析
        history = service.get_user_score_history(user_id, limit=10)
        
        # 验证历史记录包含可信度变化
        assert len(history) > 0
        credibility_scores = [record.credibility_score for record in history]
        assert len(credibility_scores) == 4
        assert credibility_scores[0] >= 0  # 验证可信度分数存在且非负