"""
用户画像服务
提供用户画像的CRUD操作和历史记录管理
"""
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate
from app.models.user_profile_history import UserProfileHistory, UserProfileHistoryCreate
from app.services.embedding_service import embedding_service
from app.utils.logger import logger


def _embedding_to_json(embedding: List[float]) -> str:
    """将 embedding 列表转换为 JSON 字符串"""
    return json.dumps(embedding, ensure_ascii=False)


class UserProfileService:
    """用户画像服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户的画像"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def get_user_profile_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """根据ID获取画像"""
        return self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    
    async def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """创建用户画像"""
        # 检查是否已存在
        existing = self.get_user_profile(profile_data.user_id)
        if existing:
            logger.info(f"用户 {profile_data.user_id} 的用户画像已存在，将更新现有画像")
            return await self.update_user_profile(existing.id, UserProfileUpdate(**profile_data.dict()))

        # 解析 JSON 数据并生成 LLM 总结
        summary_text = None
        description_text = None
        try:
            profile_dict = json.loads(profile_data.raw_profile)
            profile_rs = await self._generate_profile_summary(profile_data.user_id, profile_dict)
            summary_text = profile_rs.get("summary", "") if isinstance(profile_rs, dict) else str(profile_rs)
            description_text = profile_rs.get("description", "") if isinstance(profile_rs, dict) else str(profile_rs)

            logger.info(f"成功生成用户画像总结: user_id={profile_data.user_id}, {profile_rs}")
        except Exception as e:
            logger.error(f"生成用户画像总结失败: user_id={profile_data.user_id}, error={str(e)}")
            basic_summary = self._generate_basic_summary({})
            summary_text = basic_summary.get("description", "") if isinstance(basic_summary, dict) else str(basic_summary)
            description_text = summary_text

        embedding_text = description_text or profile_data.raw_profile
        embedding_json = None
        if embedding_text:
            embedding = await embedding_service.generate_embedding_with_retry(embedding_text)
            if embedding:
                embedding_json = _embedding_to_json(embedding)
                logger.info(f"成功生成用户画像向量: user_id={profile_data.user_id}")
            else:
                logger.warning(f"生成用户画像向量失败，使用零向量: user_id={profile_data.user_id}")
                embedding_json = _embedding_to_json([0.0] * 1024)
        else:
            logger.warning(f"用户画像文本为空，使用零向量: user_id={profile_data.user_id}")
            embedding_json = _embedding_to_json([0.0] * 1024)

        try:
            self.db.execute(
                text("""
                    INSERT INTO user_profiles 
                    (id, user_id, raw_profile, raw_profile_embedding, profile_summary, update_reason, created_at, updated_at)
                    VALUES 
                    (:id, :user_id, :raw_profile, VEC_FROMTEXT(:embedding), :summary, :reason, NOW(), NOW())
                """),
                {
                    "id": str(profile_data.user_id) + "-" + str(hash(profile_data.raw_profile) % 10000),
                    "user_id": profile_data.user_id,
                    "raw_profile": description_text,
                    "embedding": embedding_json,
                    "summary": summary_text,
                    "reason": profile_data.update_reason or "初始创建"
                }
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"插入用户画像失败: user_id={profile_data.user_id}, error={str(e)}")
            raise

        db_profile = self.get_user_profile(profile_data.user_id)

        # 创建历史记录
        self._create_history_record(db_profile, "create", "system", "初始创建")

        logger.info(f"创建用户画像成功: user_id={profile_data.user_id}")
        return db_profile
    
    def update_user_profile(self, profile_id: str, profile_update: UserProfileUpdate) -> Optional[UserProfile]:
        """更新用户画像"""
        db_profile = self.get_user_profile_by_id(profile_id)
        if not db_profile:
            return None
        
        # 记录更新前的数据
        old_data = db_profile.raw_profile
        
        # 更新字段
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        self.db.commit()
        self.db.refresh(db_profile)
        
        # 创建历史记录
        change_reason = profile_update.update_reason or "用户更新"
        self._create_history_record(db_profile, "update", "user", change_reason)
        
        logger.info(f"更新用户画像成功: profile_id={profile_id}")
        return db_profile
    
    async def update_profile(self, user_id: str, profile_update: UserProfileUpdate, change_source: str = "user") -> UserProfile:
        """通过用户ID更新用户画像（API路由使用）"""
        # 首先获取用户画像
        db_profile = self.get_user_profile(user_id)
        if not db_profile:
            # 如果画像不存在，创建新的
            create_data = UserProfileCreate(
                user_id=user_id,
                raw_profile=profile_update.raw_profile,
                update_reason=profile_update.update_reason or "自动创建"
            )
            return await self.create_user_profile(create_data)

        # 如果有raw_profile更新，需要重新生成总结文本
        embedding_json = None
        if profile_update.raw_profile:
            # 格式化原始数据
            formatted_profile = self._format_raw_profile(profile_update.raw_profile)
            setattr(db_profile, 'raw_profile', formatted_profile)

            # 解析JSON数据并生成LLM总结
            try:
                import json
                profile_dict = json.loads(profile_update.raw_profile)

                profile_rs = await self._generate_profile_summary(user_id, profile_dict)
                if isinstance(profile_rs, dict):
                    profile_summary = profile_rs.get("summary", "")
                    profile_description = profile_rs.get("description", "")
                else:
                    profile_summary = str(profile_rs)
                    profile_description = profile_summary

                setattr(db_profile, 'profile_summary', profile_summary)
                setattr(db_profile, 'raw_profile', profile_description)

                embedding_text = profile_description or profile_update.raw_profile
                embedding_json = None
                if embedding_text:
                    embedding = await embedding_service.generate_embedding_with_retry(embedding_text)
                    if embedding:
                        embedding_json = _embedding_to_json(embedding)
                        logger.info(f"成功生成用户画像向量: user_id={user_id}")
                    else:
                        logger.warning(f"生成用户画像向量失败，使用零向量: user_id={user_id}")
                        embedding_json = _embedding_to_json([0.0] * 1024)
                else:
                    logger.warning(f"用户画像文本为空，使用零向量: user_id={user_id}")
                    embedding_json = _embedding_to_json([0.0] * 1024)

                logger.info(f"成功生成并更新用户画像总结: user_id={user_id}")
            except Exception as e:
                logger.error(f"生成用户画像总结失败: user_id={user_id}, error={str(e)}")
                basic_summary = self._generate_basic_summary({})
                if isinstance(basic_summary, dict):
                    setattr(db_profile, 'profile_summary', basic_summary.get("description", ""))
                else:
                    setattr(db_profile, 'profile_summary', str(basic_summary))
                embedding_json = None

        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ['raw_profile', 'profile_summary'] and value is not None:
                setattr(db_profile, field, value)

        update_fields = ["raw_profile = :raw_profile", "profile_summary = :summary", "updated_at = NOW()"]
        update_params = {
            "raw_profile": db_profile.raw_profile,
            "summary": db_profile.profile_summary
        }

        if embedding_json is not None:
            update_fields.append("raw_profile_embedding = VEC_FROMTEXT(:embedding)")
            update_params["embedding"] = embedding_json
        else:
            update_fields.append("raw_profile_embedding = VEC_FROMTEXT(:embedding)")
            update_params["embedding"] = _embedding_to_json([0.0] * 1024)

        update_params["user_id"] = user_id

        try:
            self.db.execute(
                text(f"UPDATE user_profiles SET {', '.join(update_fields)} WHERE user_id = :user_id"),
                update_params
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户画像失败: user_id={user_id}, error={str(e)}")
            raise

        db_profile = self.get_user_profile(user_id)

        # 创建历史记录
        change_reason = profile_update.update_reason or "用户更新"
        self._create_history_record(db_profile, "update", change_source, change_reason)

        logger.info(f"更新用户画像成功: user_id={user_id}")
        return db_profile
    
    def delete_user_profile(self, profile_id: str) -> bool:
        """删除用户画像"""
        db_profile = self.get_user_profile_by_id(profile_id)
        if not db_profile:
            return False
        
        self.db.delete(db_profile)
        self.db.commit()
        
        logger.info(f"删除用户画像成功: profile_id={profile_id}")
        return True
    
    def get_profile_history(self, user_id: str, limit: int = 10) -> List[UserProfileHistory]:
        """获取用户画像历史记录"""
        return self.db.query(UserProfileHistory).filter(
            UserProfileHistory.user_id == user_id
        ).order_by(desc(UserProfileHistory.created_at)).limit(limit).all()
    
    def _create_history_record(self, profile: UserProfile, change_type: str, 
                              change_source: str, change_reason: str) -> UserProfileHistory:
        """创建历史记录"""
        # 获取下一个版本号
        last_history = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile.id
        ).order_by(desc(UserProfileHistory.version)).first()
        
        next_version = (last_history.version + 1) if last_history else 1
        
        history_record = UserProfileHistory(
            profile_id=profile.id,
            user_id=profile.user_id,
            version=next_version,
            change_type=change_type,
            change_source=change_source,
            change_reason=change_reason,
            current_raw_profile=profile.raw_profile
        )
        
        self.db.add(history_record)
        self.db.commit()
        self.db.refresh(history_record)
        
        logger.info(f"创建画像历史记录成功: profile_id={profile.id}, version={next_version}")
        return history_record
    
    def _format_raw_profile(self, raw_profile: str) -> str:
        """
        格式化 raw_profile 字符串，提高可读性
        """
        try:
            import json
            # 尝试解析JSON字符串
            profile_dict = json.loads(raw_profile)

            # 格式化JSON字符串，使用2空格缩进并添加换行
            formatted = json.dumps(
                profile_dict,
                ensure_ascii=False,
                indent=2,  # 使用2个空格缩进
                separators=(',', ': ')  # 减少空格，使格式更紧凑
            )

            return formatted
        except (json.JSONDecodeError, TypeError) as e:
            # 如果解析失败，返回原始字符串
            logger.warning(f"格式化raw_profile失败，使用原始格式: {e}")
            return raw_profile

    async def _generate_profile_summary(self, user_id: str, profile_data_str: str, existing_profile_str: str = None) -> dict:
        """
        调用LLM服务生成用户画像总结文本

        Args:
            user_id: 用户ID
            profile_data: 用户基本数据（JSON格式的字典）

        Returns:
            str: LLM生成的总结文本
        """
        try:
            # 导入LLM服务
            from app.services.llm_service import LLMService
            from app.models.llm_schemas import LLMProvider

            # 创建LLM服务实例
            llm_service = LLMService(self.db)

            # 调用LLM分析用户画像
            response = await llm_service.generate_profile_summary(
                user_id=user_id,
                profile_data_str=profile_data_str,
                existing_profile_str=existing_profile_str,
                provider=LLMProvider.VOLCENGINE
            )

            if response.success and response.data:
                try:
                    # 解析LLM返回的JSON字符串
                    result = json.loads(response.data)
                    parsed_description = result.get("description", "")
                    parsed_summary = result.get("summary", "")
                    return {
                        "description": parsed_description,
                        "summary": parsed_summary
                    }
                except json.JSONDecodeError:
                    logger.warning(f"LLM返回的JSON格式错误: user_id={user_id}")
                    return self._generate_basic_summary(profile_data_str)

            # 如果LLM调用失败，生成基本总结
            logger.warning(f"LLM分析失败，生成基本总结: user_id={user_id}")
            return self._generate_basic_summary(profile_data_str)

        except Exception as e:
            # 记录错误并返回基本总结
            logger.error(f"生成用户画像总结失败: user_id={user_id}, error={str(e)}")
            return self._generate_basic_summary(profile_data_str)

    def _format_analysis_dict(self, analysis: Dict[str, Any]) -> str:
        """
        将分析字典格式化为自然语言文本
        """
        if not isinstance(analysis, dict) or not analysis:
            return ""

        parts = []
        for key, value in analysis.items():
            if value and str(value).strip():
                # 转换key为更友好的描述
                friendly_key = self._convert_key_to_text(key)
                parts.append(f"{friendly_key}: {value}")

        return "\n".join(parts)

    def _convert_key_to_text(self, key: str) -> str:
        """
        将字典键转换为更友好的文本描述
        """
        key_map = {
            "personality": "性格特点",
            "lifestyle": "生活方式",
            "values": "价值观",
            "interests": "兴趣爱好",
            "social_style": "社交风格",
            "behavior_patterns": "行为模式",
            "preferences": "个人偏好",
            "traits": "个性特征",
            "mood": "情绪状态",
            "communication_style": "沟通方式"
        }
        return key_map.get(key, key)

    def _generate_basic_summary(self, profile_data: Dict[str, Any]) -> dict:
        """
        生成基础的用户画像总结（当LLM不可用时使用）
        """
        try:
            import json

            parts = ["用户画像总结："]

            # 添加基本信息
            if "nickname" in profile_data:
                parts.append(f"昵称: {profile_data['nickname']}")

            if "gender" in profile_data:
                gender = profile_data['gender']
                if gender in ['1', 1]:
                    parts.append("性别: 男")
                elif gender in ['2', 2]:
                    parts.append("性别: 女")
                else:
                    parts.append(f"性别: {gender}")

            if "age" in profile_data:
                parts.append(f"年龄: {profile_data['age']}")

            if "location" in profile_data:
                parts.append(f"位置: {profile_data['location']}")

            if "bio" in profile_data and profile_data['bio']:
                parts.append(f"个人简介: {profile_data['bio']}")

            if "birthday" in profile_data and profile_data['birthday'] != "未知":
                parts.append(f"生日: {profile_data['birthday']}")

            return {
                "description": "\n".join(parts),
                "summary": "\n".join(parts)
            }

        except Exception as e:
            logger.error(f"生成基础总结失败: {e}")
            return "用户画像生成中..."

    async def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像"""
        profile = self.get_user_profile(user_id)
        if not profile:
            # 创建默认画像
            profile_data = UserProfileCreate(
                user_id=user_id,
                raw_profile=None,
                update_reason="自动创建默认画像"
            )
            profile = await self.create_user_profile(profile_data)
        
        return profile

    async def generate_profile_from_user_data(
        self, 
        user_id: str, 
        user_data: Dict[str, Any],
        existing_profile: str = None
    ) -> UserProfile:
        """
        根据用户基础信息生成用户画像
        
        当用户创建账号或更新个人信息时调用此方法
        结合用户表的基础信息（bio, gender, age, occupation, location）
        和用户画像表中已有的 raw_profile 信息，使用 LLM 异步生成新的画像数据
        
        Args:
            user_id: 用户ID
            user_data: 用户基础信息字典，包含 bio, gender, age, occupation, location 等
            existing_raw_profile: 已有的 raw_profile 数据（可选）
            
        Returns:
            更新后的 UserProfile 对象
        """
        import json
        from datetime import datetime
        
        # 性别映射：Integer -> 文字描述
        gender_value = user_data.get("gender")
        gender_map = {
            0: "未知",
            1: "男性",
            2: "女性"
        }
        gender_text = gender_map.get(gender_value, "未知") if gender_value is not None else "未知"
        
        # 年龄处理：转换为年龄段描述
        age_value = user_data.get("age")
        if age_value is not None:
            if age_value < 18:
                age_text = "18岁以下"
            elif age_value < 25:
                age_text = "18-24岁"
            elif age_value < 35:
                age_text = "25-34岁"
            elif age_value < 45:
                age_text = "35-44岁"
            elif age_value < 55:
                age_text = "45-54岁"
            elif age_value < 65:
                age_text = "55-64岁"
            else:
                age_text = "65岁及以上"
        else:
            age_text = "未知"
        
        # 1. 准备画像数据
        profile_data = {
            "user_id": user_id,
            "nickname": user_data.get("nick_name") or user_data.get("nickName"),
            "gender": gender_text,
            "age": age_text,
            "bio": user_data.get("bio"),
            "occupation": user_data.get("occupation"),
            "location": user_data.get("location"),
            "education": user_data.get("education"),
            "interests": user_data.get("interests"),
            "update_time": datetime.now().isoformat()
        }
        
        # 清理空值
        profile_data = {k: v for k, v in profile_data.items() if v is not None}
        
        # 2. 准备 raw_profile JSON 字符串
        profile_data_str = json.dumps(profile_data, ensure_ascii=False)
        
        # 3. 调用 LLM 生成 profile_dict
        profile_dict = await self._generate_profile_summary(user_id, profile_data_str, existing_profile)
        
        # 4. 获取或创建用户画像记录
        db_profile = self.get_user_profile(user_id)
        
        # 生成新的 raw_profile 文本
        new_raw_profile = profile_dict.get("description", "")
        new_profile_summary = profile_dict.get("summary", "")
        
        # 生成 embedding
        embedding_text = new_raw_profile or json.dumps(profile_data, ensure_ascii=False)
        embedding_json = None
        if embedding_text:
            try:
                embedding = await embedding_service.generate_embedding_with_retry(embedding_text)
                if embedding:
                    embedding_json = _embedding_to_json(embedding)
                    logger.info(f"成功生成用户画像向量: user_id={user_id}")
                else:
                    logger.warning(f"生成用户画像向量失败，使用零向量: user_id={user_id}")
                    embedding_json = _embedding_to_json([0.0] * 1024)
            except Exception as e:
                logger.error(f"生成用户画像向量失败: user_id={user_id}, error={str(e)}")
                embedding_json = _embedding_to_json([0.0] * 1024)
        else:
            logger.warning(f"用户画像文本为空，使用零向量: user_id={user_id}")
            embedding_json = _embedding_to_json([0.0] * 1024)
        
        if db_profile:
            # 更新现有画像
            db_profile.raw_profile = new_raw_profile
            db_profile.profile_summary = new_profile_summary
            db_profile.update_reason = "用户信息更新触发画像生成"
            db_profile.updated_at = datetime.now()
            
            # 创建历史记录
            self._create_history_record(db_profile, "update", "system", "用户信息更新触发LLM画像生成")
            
            # 更新 embedding
            self.db.execute(
                text("UPDATE user_profiles SET raw_profile = :raw_profile, profile_summary = :summary, raw_profile_embedding = VEC_FROMTEXT(:embedding), updated_at = NOW() WHERE user_id = :user_id"),
                {
                    "raw_profile": new_raw_profile,
                    "summary": new_profile_summary,
                    "embedding": embedding_json,
                    "user_id": user_id
                }
            )
        else:
            # 创建新画像
            db_profile = UserProfile(
                user_id=user_id,
                raw_profile=new_raw_profile,
                profile_summary=new_profile_summary,
                update_reason="用户创建触发画像生成"
            )
            self.db.add(db_profile)
            self.db.flush()
            
            # 更新 embedding
            self.db.execute(
                text("UPDATE user_profiles SET raw_profile_embedding = VEC_FROMTEXT(:embedding) WHERE user_id = :user_id"),
                {
                    "embedding": embedding_json,
                    "user_id": user_id
                }
            )
        
        self.db.commit()
        self.db.refresh(db_profile)
        
        logger.info(f"用户画像生成成功: user_id={user_id}")
        return db_profile

    async def refresh_profile_on_user_update(
        self, 
        user_id: str, 
        user_data: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """
        在用户信息更新后刷新用户画像
        
        这是主要的入口方法，会在用户更新基础信息后被调用
        结合用户基础信息和已有画像数据，使用 LLM 重新生成画像
        
        Args:
            user_id: 用户ID
            user_data: 更新后的用户基础信息
            
        Returns:
            更新后的 UserProfile 对象，如果用户不存在则返回 None
        """
        # 检查用户是否存在
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在，无法生成画像: user_id={user_id}")
            return None
        
        # 获取已有的 raw_profile
        existing_profile = self.get_user_profile(user_id)
        existing_raw_profile = existing_profile.raw_profile if existing_profile else None
        
        # 生成新画像
        return await self.generate_profile_from_user_data(
            user_id=user_id,
            user_data=user_data,
            existing_profile=existing_raw_profile
        )
    
    def search_by_vector_similarity(
        self,
        embedding: List[float],
        exclude_user_ids: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        基于向量相似度搜索用户画像

        Args:
            embedding: 查询向量
            exclude_user_ids: 排除的用户ID列表
            limit: 返回结果数量限制

        Returns:
            匹配的用户画像列表，包含用户ID、相似度分数和原始画像信息
        """
        import json

        # 将查询向量转换为 JSON 字符串
        embedding_json = json.dumps(embedding, ensure_ascii=False)

        # 构建查询 SQL，使用 VEC_DISTANCE_COSINE 计算余弦相似度
        sql = """
            SELECT 
                user_id,
                raw_profile,
                profile_summary,
                VEC_DISTANCE_COSINE(raw_profile_embedding, VEC_FROMTEXT(:embedding)) AS similarity
            FROM user_profiles
            WHERE raw_profile_embedding IS NOT NULL
        """

        params = {"embedding": embedding_json}

        # 添加排除用户条件
        if exclude_user_ids and len(exclude_user_ids) > 0:
            placeholders = ", ".join([f":exclude_{i}" for i in range(len(exclude_user_ids))])
            sql += f" AND user_id NOT IN ({placeholders})"
            for i, user_id in enumerate(exclude_user_ids):
                params[f"exclude_{i}"] = user_id

        # 按相似度降序排序并限制数量
        sql += " ORDER BY similarity DESC LIMIT :limit"
        params["limit"] = limit

        try:
            result = self.db.execute(text(sql), params)
            rows = result.fetchall()

            matches = []
            for row in rows:
                raw_profile = row.raw_profile
                # 如果 raw_profile 是 JSON 字符串，尝试解析
                profile_data = None
                try:
                    if raw_profile and isinstance(raw_profile, str):
                        profile_data = json.loads(raw_profile)
                except json.JSONDecodeError:
                    profile_data = {"raw_profile": raw_profile}

                matches.append({
                    "user_id": row.user_id,
                    "similarity": float(row.similarity) if row.similarity else 0.0,
                    "profile_summary": row.profile_summary,
                    "raw_profile": profile_data
                })

            logger.info(f"向量相似度搜索完成，找到 {len(matches)} 个匹配用户")
            return matches

        except Exception as e:
            logger.error(f"向量相似度搜索失败: {str(e)}")
            import traceback
            logger.error(f"详细堆栈: {traceback.format_exc()}")
            return []