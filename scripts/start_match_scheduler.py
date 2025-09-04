#!/usr/bin/env python3
"""
匹配调度器启动脚本
用于启动后台匹配任务调度器
"""

import sys
import os
import threading
import signal
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.match_scheduler import match_scheduler
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('match_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SchedulerManager:
    """调度器管理器"""
    
    def __init__(self):
        self.scheduler_thread = None
        self.is_running = False
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.info("调度器已在运行中")
            return
        
        logger.info("启动匹配调度器...")
        self.is_running = True
        
        # 在单独线程中运行调度器
        self.scheduler_thread = threading.Thread(
            target=match_scheduler.start_scheduler,
            daemon=True
        )
        self.scheduler_thread.start()
        
        logger.info("匹配调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        logger.info("停止匹配调度器...")
        self.is_running = False
        match_scheduler.stop_scheduler()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("匹配调度器已停止")
    
    def status(self):
        """获取调度器状态"""
        status = match_scheduler.get_scheduler_status()
        logger.info(f"调度器状态: {status}")
        return status

# 全局调度器管理器
scheduler_manager = SchedulerManager()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，正在关闭调度器...")
    scheduler_manager.stop()
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动调度器
        scheduler_manager.start()
        
        # 保持主线程运行
        logger.info("匹配调度器正在运行中... (按 Ctrl+C 停止)")
        while scheduler_manager.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号")
    except Exception as e:
        logger.error(f"调度器运行异常: {str(e)}")
    finally:
        scheduler_manager.stop()

if __name__ == "__main__":
    main()