"""
日志工具模块
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别，默认为INFO
        
    Returns:
        配置好的日志记录器
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 如果已经配置过处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger


# 创建默认日志记录器
logger = setup_logger("app")


def log_function_call(func):
    """
    函数调用日志装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        包装后的函数
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"调用函数 {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 调用成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 调用失败: {str(e)}")
            raise
    
    return wrapper