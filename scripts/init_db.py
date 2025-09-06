#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.db_config import engine, Base
from app.models.user import User
from app.models.match import Match
from app.models.chat_message import ChatMessage, ChatConversation
from app.models.user_card_db import UserCard

def init_database():
    """初始化数据库表"""
    print("正在初始化数据库表...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表初始化完成！")
    print("已创建的表：")
    print("- users")
    print("- matches")
    print("- chat_messages")
    print("- chat_conversations")
    print("- user_cards")

if __name__ == "__main__":
    init_database()