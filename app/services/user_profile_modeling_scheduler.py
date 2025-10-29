"""
用户画像建模调度器
负责调度用户画像相关的定时任务，包括：
1. 定期验证用户人设的真实性
2. 定期验证内容的合规性  
3. 定期更新用户画像
4. 基于用户评价反馈更新用户画像
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
from app.services.user_profile_feedback_service import UserProfileFeedbackService
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.user_profile import UserProfile

# 添加用户评价反馈处理任务
if self.task_configs["feedback_processing"]["enabled"]:
    self.scheduler.add_job(
        self._run_feedback_processing_task,
        trigger=IntervalTrigger(hours=self.task_configs["feedback_processing"]["interval_hours"]),
        id="feedback_processing",
        name="用户评价反馈处理任务",
        replace_existing=True
    )
    logger.info("已添加用户评价反馈处理任务")

    async def _run_feedback_processing_task(self):
        """运行用户评价反馈处理任务"""
        logger.info("开始执行用户评价反馈处理任务")
        start_time = datetime.now()
        
        try:
            config = self.task_configs["feedback_processing"]
            batch_size = config["batch_size"]
            min_rating_threshold = config["min_rating_threshold"]
            
            # 获取未处理的反馈数量
            unprocessed_count = self.feedback_service.get_unprocessed_feedback_count()
            logger.info(f"当前有 {unprocessed_count} 条未处理的用户评价反馈")
            
            if unprocessed_count == 0:
                logger.info("没有待处理的用户评价反馈")
                return
            
            # 处理待处理的反馈
            result = await self.feedback_service.process_pending_feedback(batch_size)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"用户评价反馈处理任务完成，处理: {result.processed_count}, "
                      f"成功: {result.success_count}, 失败: {result.failure_count}, 耗时: {duration:.2f}秒")
            
            # 记录详细的处理结果
            if result.processing_results:
                success_results = [r for r in result.processing_results if r.get("success")]
                failure_results = [r for r in result.processing_results if not r.get("success")]
                
                logger.info(f"成功处理 {len(success_results)} 条反馈")
                if failure_results:
                    logger.warning(f"处理失败 {len(failure_results)} 条反馈")
                    for failure in failure_results[:5]:  # 只记录前5个失败详情
                        logger.warning(f"反馈 {failure.get('feedback_id')} 处理失败: {failure.get('error')}")
            
        except Exception as e:
            logger.error(f"用户评价反馈处理任务执行失败: {str(e)}")