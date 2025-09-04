"""
匹配任务调度器
负责定期执行匹配推荐生成任务
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.enhanced_match_service import EnhancedMatchService
from app.models.user import User
from app.models.user_profile_db import UserProfile
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchScheduler:
    """匹配任务调度器"""
    
    def __init__(self):
        self.is_running = False
        self.last_run_times = {}
    
    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            logger.info("调度器已在运行中")
            return
        
        self.is_running = True
        logger.info("启动匹配任务调度器")
        
        # 配置定时任务
        schedule.every().day.at("02:00").do(self.run_daily_match_generation)
        schedule.every().hour.do(self.run_hourly_match_cleanup)
        schedule.every(30).minutes.do(self.run_match_statistics_update)
        
        # 运行调度循环
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        logger.info("停止匹配任务调度器")
    
    def run_daily_match_generation(self):
        """执行每日匹配推荐生成任务"""
        logger.info("开始执行每日匹配推荐生成任务")
        
        try:
            db = next(get_db())
            match_service = EnhancedMatchService(db)
            
            # 为不同匹配类型生成推荐
            match_types = ["housing", "dating", "activity"]
            total_results = {}
            
            for match_type in match_types:
                logger.info(f"为 {match_type} 类型生成匹配推荐")
                result = match_service.batch_generate_recommendations(
                    match_type=match_type,
                    batch_size=200
                )
                total_results[match_type] = result
                logger.info(f"{match_type} 推荐生成完成: {result}")
            
            # 记录执行时间
            self.last_run_times['daily_generation'] = datetime.now()
            
            # 发送通知（如果需要）
            self._send_task_notification("每日匹配推荐生成", total_results)
            
            logger.info("每日匹配推荐生成任务完成")
            
        except Exception as e:
            logger.error(f"每日匹配推荐生成任务失败: {str(e)}")
        finally:
            db.close()
    
    def run_hourly_match_cleanup(self):
        """执行每小时匹配数据清理任务"""
        logger.info("开始执行匹配数据清理任务")
        
        try:
            db = next(get_db())
            
            # 清理过期的匹配操作记录（超过30天）
            from app.models.match_action import MatchAction
            cutoff_date = datetime.now() - timedelta(days=30)
            
            expired_actions = db.query(MatchAction).filter(
                MatchAction.created_at < cutoff_date
            ).count()
            
            if expired_actions > 0:
                db.query(MatchAction).filter(
                    MatchAction.created_at < cutoff_date
                ).delete()
                db.commit()
                logger.info(f"清理了 {expired_actions} 条过期匹配操作记录")
            
            # 更新匹配结果的活跃状态
            from app.models.match_action import MatchResult
            inactive_cutoff = datetime.now() - timedelta(days=7)
            
            inactive_matches = db.query(MatchResult).filter(
                MatchResult.last_activity_at < inactive_cutoff,
                MatchResult.is_active == True
            ).count()
            
            if inactive_matches > 0:
                db.query(MatchResult).filter(
                    MatchResult.last_activity_at < inactive_cutoff,
                    MatchResult.is_active == True
                ).update({"is_active": False})
                db.commit()
                logger.info(f"标记了 {inactive_matches} 个匹配为非活跃状态")
            
            self.last_run_times['hourly_cleanup'] = datetime.now()
            logger.info("匹配数据清理任务完成")
            
        except Exception as e:
            logger.error(f"匹配数据清理任务失败: {str(e)}")
        finally:
            db.close()
    
    def run_match_statistics_update(self):
        """执行匹配统计更新任务"""
        logger.info("开始执行匹配统计更新任务")
        
        try:
            db = next(get_db())
            
            # 更新用户匹配统计缓存
            # 这里可以实现统计数据的缓存更新逻辑
            # 例如：更新Redis中的用户匹配统计信息
            
            active_users_count = db.query(User).filter(User.is_active == True).count()
            active_profiles_count = db.query(UserProfile).filter(UserProfile.is_active == 1).count()
            
            logger.info(f"当前活跃用户: {active_users_count}, 活跃资料: {active_profiles_count}")
            
            self.last_run_times['statistics_update'] = datetime.now()
            logger.info("匹配统计更新任务完成")
            
        except Exception as e:
            logger.error(f"匹配统计更新任务失败: {str(e)}")
        finally:
            db.close()
    
    def _send_task_notification(self, task_name: str, results: Dict[str, Any]):
        """发送任务执行通知"""
        # 这里可以实现通知逻辑，例如：
        # 1. 发送邮件通知
        # 2. 推送到监控系统
        # 3. 记录到日志文件
        # 4. 发送微信服务号消息
        
        logger.info(f"任务通知 - {task_name}: {results}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "last_run_times": {
                task: time.isoformat() if time else None 
                for task, time in self.last_run_times.items()
            },
            "next_scheduled_runs": {
                "daily_generation": "每天 02:00",
                "hourly_cleanup": "每小时",
                "statistics_update": "每30分钟"
            }
        }
    
    def manual_trigger_task(self, task_name: str) -> Dict[str, Any]:
        """手动触发任务"""
        try:
            if task_name == "daily_generation":
                self.run_daily_match_generation()
                return {"success": True, "message": "每日匹配推荐生成任务已触发"}
            elif task_name == "hourly_cleanup":
                self.run_hourly_match_cleanup()
                return {"success": True, "message": "匹配数据清理任务已触发"}
            elif task_name == "statistics_update":
                self.run_match_statistics_update()
                return {"success": True, "message": "匹配统计更新任务已触发"}
            else:
                return {"success": False, "message": f"未知任务: {task_name}"}
        except Exception as e:
            return {"success": False, "message": f"任务执行失败: {str(e)}"}


# 全局调度器实例
match_scheduler = MatchScheduler()


class MatchRecommendationCache:
    """匹配推荐缓存管理器"""
    
    def __init__(self):
        # 这里可以使用Redis或其他缓存系统
        # 暂时使用内存缓存作为示例
        self._cache = {}
    
    def get_user_recommendations(self, user_id: str, match_type: str) -> List[Dict[str, Any]]:
        """获取用户的匹配推荐"""
        cache_key = f"{user_id}:{match_type}"
        return self._cache.get(cache_key, [])
    
    def set_user_recommendations(self, user_id: str, match_type: str, 
                               recommendations: List[Dict[str, Any]], 
                               expire_hours: int = 24):
        """设置用户的匹配推荐"""
        cache_key = f"{user_id}:{match_type}"
        self._cache[cache_key] = {
            "data": recommendations,
            "timestamp": datetime.now(),
            "expire_at": datetime.now() + timedelta(hours=expire_hours)
        }
    
    def clear_user_recommendations(self, user_id: str, match_type: str = None):
        """清除用户的匹配推荐缓存"""
        if match_type:
            cache_key = f"{user_id}:{match_type}"
            self._cache.pop(cache_key, None)
        else:
            # 清除该用户所有类型的推荐
            keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                self._cache.pop(key, None)
    
    def cleanup_expired_cache(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = []
        
        for key, value in self._cache.items():
            if isinstance(value, dict) and value.get("expire_at", now) < now:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.pop(key, None)
        
        return len(expired_keys)


# 全局推荐缓存实例
recommendation_cache = MatchRecommendationCache()