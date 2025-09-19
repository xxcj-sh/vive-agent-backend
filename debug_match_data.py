#!/usr/bin/env python3
"""
调试匹配数据结构的脚本
用于分析为什么卡片ID在匹配API中返回的是匹配动作ID而不是实际的卡片ID
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.match_action import MatchAction
from app.models.user_card_db import UserCard
from app.models.user import User

def debug_match_data():
    """调试匹配数据结构"""
    db = SessionLocal()
    
    try:
        print("=== 调试匹配数据结构 ===\n")
        
        # 1. 检查最新的匹配动作记录
        print("1. 最新的匹配动作记录:")
        latest_actions = db.query(MatchAction).order_by(MatchAction.created_at.desc()).limit(3).all()
        
        for i, action in enumerate(latest_actions, 1):
            print(f"\n动作记录 {i}:")
            print(f"  动作ID (action.id): {action.id}")
            print(f"  目标卡片ID (action.target_card_id): {action.target_card_id}")
            print(f"  用户ID (action.user_id): {action.user_id}")
            print(f"  目标用户ID (action.target_user_id): {action.target_user_id}")
            print(f"  操作类型: {action.action_type}")
            print(f"  场景类型: {action.scene_type}")
            
            # 检查对应的实际卡片
            target_card = db.query(UserCard).filter(UserCard.id == action.target_card_id).first()
            if target_card:
                print(f"  实际卡片信息:")
                print(f"    卡片ID: {target_card.id}")
                print(f"    用户ID: {target_card.user_id}")
                print(f"    场景类型: {target_card.scene_type}")
                print(f"    角色类型: {target_card.role_type}")
                print(f"    显示名称: {target_card.display_name}")
            else:
                print(f"  警告: 找不到对应的卡片记录！")
        
        # 2. 检查匹配API返回的数据结构问题
        print("\n\n2. 匹配API数据结构分析:")
        print("问题: API返回的 'id' 字段实际上是匹配动作记录的ID，而不是卡片ID")
        print("期望: API应该返回目标卡片的ID (target_card_id)")
        print("实际: API返回的是动作记录的ID (action.id)")
        
        # 3. 检查前端期望的字段
        print("\n\n3. 前端期望的数据结构:")
        print("前端 handleCardClick 方法期望:")
        print("  match.cardId || match.userId")
        print("但API返回的是:")
        print("  match.id = action.id (匹配动作ID)")
        print("  match.userId = action.target_user_id (目标用户ID)")
        
        # 4. 解决方案
        print("\n\n4. 解决方案:")
        print("在 matches.py 中，应该将 target_card_id 作为 'id' 字段返回，而不是 action.id")
        print("或者添加一个 'cardId' 字段，包含 target_card_id 的值")
        
        # 5. 检查是否有正确的卡片ID字段
        print("\n\n5. 检查是否有其他API返回正确的卡片ID:")
        
        # 检查收藏API返回的数据
        print("收藏API应该返回正确的卡片ID，让我们检查...")
        
    except Exception as e:
        print(f"调试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_match_data()