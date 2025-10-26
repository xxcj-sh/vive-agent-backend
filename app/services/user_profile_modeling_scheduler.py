"""
用户画像离线建模任务调度器
负责定期执行用户画像相关的离线任务
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.user_profile_modeling_service import UserProfileModelingService
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class ProfileModelingScheduler:
    """用户画像离线建模任务调度器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.modeling_service = ProfileModelingService(db)
        self.is_running = False
        
        # 任务配置
        self.task_configs = {
            "authenticity_verification": {
                "enabled": True,
                "interval_hours": 24,  # 每24小时执行一次
                "batch_size": 50,      # 每批处理50个用户
                "min_score_threshold": 30  # 低于30分的需要重新验证
            },
            "content_compliance": {
                "enabled": True,
                "interval_hours": 12,  # 每12小时执行一次
                "batch_size": 100,      # 每批处理100张卡片
                "pending_only": True    # 只处理待审核的卡片
            },
            "profile_update": {
                "enabled": True,
                "interval_hours": 6,   # 每6小时执行一次
                "batch_size": 30,      # 每批处理30个用户
                "min_chat_count": 5,   # 至少需要5条聊天记录
                "max_days_since_update": 7  # 超过7天未更新的需要更新
            }
        }
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行中")
            return
        
        try:
            # 添加人设真实性验证任务
            if self.task_configs["authenticity_verification"]["enabled"]:
                self.scheduler.add_job(
                    self._run_authenticity_verification_task,
                    trigger=IntervalTrigger(hours=self.task_configs["authenticity_verification"]["interval_hours"]),
                    id="authenticity_verification",
                    name="人设真实性验证任务",
                    replace_existing=True
                )
                logger.info("已添加人设真实性验证任务")
            
            # 添加内容合规性验证任务
            if self.task_configs["content_compliance"]["enabled"]:
                self.scheduler.add_job(
                    self._run_content_compliance_task,
                    trigger=IntervalTrigger(hours=self.task_configs["content_compliance"]["interval_hours"]),
                    id="content_compliance",
                    name="内容合规性验证任务",
                    replace_existing=True
                )
                logger.info("已添加内容合规性验证任务")
            
            # 添加用户画像更新任务
            if self.task_configs["profile_update"]["enabled"]:
                self.scheduler.add_job(
                    self._run_profile_update_task,
                    trigger=IntervalTrigger(hours=self.task_configs["profile_update"]["interval_hours"]),
                    id="profile_update",
                    name="用户画像更新任务",
                    replace_existing=True
                )
                logger.info("已添加用户画像更新任务")
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            logger.info("用户画像离线建模调度器已启动")
            
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            raise
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未在运行")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("用户画像离线建模调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
    
    async def _run_authenticity_verification_task(self):
        """运行人设真实性验证任务"""
        logger.info("开始执行人设真实性验证任务")
        start_time = datetime.now()
        
        try:
            config = self.task_configs["authenticity_verification"]
            batch_size = config["batch_size"]
            min_score_threshold = config["min_score_threshold"]
            
            # 获取需要验证的用户
            users_to_verify = self._get_users_for_authenticity_verification(batch_size, min_score_threshold)
            
            if not users_to_verify:
                logger.info("没有需要验证的用户")
                return
            
            logger.info(f"将对 {len(users_to_verify)} 个用户进行人设真实性验证")
            
            # 批量处理用户验证
            success_count = 0
            failure_count = 0
            
            for user in users_to_verify:
                try:
                    result = await self.modeling_service.verify_profile_authenticity(user.id)
                    
                    if result["success"]:
                        success_count += 1
                        logger.info(f"用户 {user.id} 真实性验证完成，评分: {result['authenticity_score']}")
                    else:
                        failure_count += 1
                        logger.error(f"用户 {user.id} 真实性验证失败: {result.get('error', '未知错误')}")
                    
                    # 添加短暂延迟避免API调用过于频繁
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"验证用户 {user.id} 时发生异常: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"人设真实性验证任务完成，成功: {success_count}, 失败: {failure_count}, 耗时: {duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"人设真实性验证任务执行失败: {str(e)}")
    
    async def _run_content_compliance_task(self):
        """运行内容合规性验证任务"""
        logger.info("开始执行内容合规性验证任务")
        start_time = datetime.now()
        
        try:
            config = self.task_configs["content_compliance"]
            batch_size = config["batch_size"]
            pending_only = config["pending_only"]
            
            # 获取需要验证的卡片
            cards_to_verify = self._get_cards_for_compliance_verification(batch_size, pending_only)
            
            if not cards_to_verify:
                logger.info("没有需要验证的卡片")
                return
            
            logger.info(f"将对 {len(cards_to_verify)} 张卡片进行内容合规性验证")
            
            # 批量处理卡片验证
            approved_count = 0
            rejected_count = 0
            failure_count = 0
            
            for card in cards_to_verify:
                try:
                    result = await self.modeling_service.verify_content_compliance(card.id)
                    
                    if result["success"]:
                        if result["is_compliant"]:
                            approved_count += 1
                        else:
                            rejected_count += 1
                        logger.info(f"卡片 {card.id} 合规性验证完成，状态: {'通过' if result['is_compliant'] else '拒绝'}")
                    else:
                        failure_count += 1
                        logger.error(f"卡片 {card.id} 合规性验证失败: {result.get('error', '未知错误')}")
                    
                    # 添加短暂延迟避免API调用过于频繁
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"验证卡片 {card.id} 时发生异常: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"内容合规性验证任务完成，通过: {approved_count}, 拒绝: {rejected_count}, 失败: {failure_count}, 耗时: {duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"内容合规性验证任务执行失败: {str(e)}")
    
    async def _run_profile_update_task(self):
        """运行用户画像更新任务"""
        logger.info("开始执行用户画像更新任务")
        start_time = datetime.now()
        
        try:
            config = self.task_configs["profile_update"]
            batch_size = config["batch_size"]
            min_chat_count = config["min_chat_count"]
            max_days_since_update = config["max_days_since_update"]
            
            # 获取需要更新画像的用户
            users_to_update = self._get_users_for_profile_update(batch_size, min_chat_count, max_days_since_update)
            
            if not users_to_update:
                logger.info("没有需要更新画像的用户")
                return
            
            logger.info(f"将对 {len(users_to_update)} 个用户进行画像更新")
            
            # 批量处理用户画像更新
            success_count = 0
            failure_count = 0
            
            for user in users_to_update:
                try:
                    result = await self.modeling_service.update_user_profile_analysis(user.id)
                    
                    if result["success"]:
                        success_count += 1
                        logger.info(f"用户 {user.id} 画像更新完成，置信度: {result['confidence_score']}")
                    else:
                        failure_count += 1
                        logger.error(f"用户 {user.id} 画像更新失败: {result.get('error', '未知错误')}")
                    
                    # 添加短暂延迟避免API调用过于频繁
                    await asyncio.sleep(0.8)
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"更新用户 {user.id} 画像时发生异常: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"用户画像更新任务完成，成功: {success_count}, 失败: {failure_count}, 耗时: {duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"用户画像更新任务执行失败: {str(e)}")
    
    def _get_users_for_authenticity_verification(self, batch_size: int, min_score_threshold: int) -> List[User]:
        """获取需要真实性验证的用户"""
        try:
            # 获取最近7天内创建或更新的用户
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # 获取还没有画像或者画像评分较低的用户
            users = self.db.query(User).filter(
                User.created_at >= cutoff_date
            ).limit(batch_size).all()
            
            return users
            
        except Exception as e:
            logger.error(f"获取需要真实性验证的用户失败: {str(e)}")
            return []
    
    def _get_cards_for_compliance_verification(self, batch_size: int, pending_only: bool) -> List[UserCard]:
        """获取需要合规性验证的卡片"""
        try:
            query = self.db.query(UserCard)
            
            # 获取最近7天内创建或更新的卡片
            cutoff_date = datetime.now() - timedelta(days=7)
            query = query.filter(
                UserCard.created_at >= cutoff_date
            )
            
            cards = query.limit(batch_size).all()
            
            return cards
            
        except Exception as e:
            logger.error(f"获取需要合规性验证的卡片失败: {str(e)}")
            return []
    
    def _get_users_for_profile_update(self, batch_size: int, min_chat_count: int, max_days_since_update: int) -> List[User]:
        """获取需要更新画像的用户"""
        try:
            from app.models.chat_message import ChatMessage
            
            # 获取最近7天内有聊天记录的用户
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # 简化查询：获取最近7天内有聊天记录的用户（不限制聊天数量）
            users_with_chats = self.db.query(User).join(
                ChatMessage, User.id == ChatMessage.user_id
            ).filter(
                ChatMessage.created_at >= cutoff_date
            ).distinct().limit(batch_size).all()
            
            return users_with_chats
            
        except Exception as e:
            logger.error(f"获取需要更新画像的用户失败: {str(e)}")
            return []
    
    def update_task_config(self, task_name: str, config: Dict[str, Any]):
        """更新任务配置"""
        if task_name in self.task_configs:
            self.task_configs[task_name].update(config)
            logger.info(f"任务 {task_name} 配置已更新")
        else:
            logger.warning(f"未知的任务名称: {task_name}")
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        jobs = self.scheduler.get_jobs()
        job_status = {}
        
        for job in jobs:
            job_status[job.id] = {
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
        
        return {
            "scheduler_running": self.is_running,
            "jobs": job_status,
            "task_configs": self.task_configs
        }