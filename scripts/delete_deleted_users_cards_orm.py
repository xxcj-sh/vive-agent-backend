#!/usr/bin/env python3
"""
删除已注销用户的卡片 - SQLAlchemy ORM版本

这个脚本使用SQLAlchemy ORM框架删除已注销用户的卡片，
更好地集成到现有的代码架构中。

使用方法:
    python scripts/delete_deleted_users_cards_orm.py [--dry-run] [--verbose]

参数:
    --dry-run:  干运行模式，只显示将要删除的卡片，不实际执行删除操作
    --verbose:  显示详细信息
    --help:     显示帮助信息
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User
from app.models.user_card_db import UserCard
from app.database import get_db  # 使用项目的数据库配置

def get_deleted_users(db: Session) -> List[User]:
    """获取所有已注销的用户"""
    return db.query(User).filter(User.status == 'deleted').order_by(User.updated_at.desc()).all()

def get_user_active_cards(db: Session, user_id: str) -> List[UserCard]:
    """获取指定用户的所有活跃卡片"""
    return db.query(UserCard).filter(
        and_(
            UserCard.user_id == user_id,
            UserCard.is_deleted == 0
        )
    ).order_by(UserCard.created_at.desc()).all()

def soft_delete_cards(db: Session, cards: List[UserCard]) -> int:
    """软删除指定的卡片"""
    if not cards:
        return 0
    
    deleted_count = 0
    current_time = datetime.now()
    
    for card in cards:
        if card.is_deleted == 0:  # 确保只删除未删除的卡片
            card.is_deleted = 1
            card.updated_at = current_time
            deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    return deleted_count

def show_user_info(user: User) -> None:
    """显示用户信息"""
    print(f"用户ID: {user.id}")
    print(f"手机号: {user.phone or 'N/A'}")
    print(f"昵称: {user.nick_name or 'N/A'}")
    print(f"状态: {user.status}")
    print(f"创建时间: {user.created_at}")
    print(f"更新时间: {user.updated_at}")
    print(f"是否活跃: {'是' if user.is_active else '否'}")

def show_card_info(card: UserCard, index: int = 1) -> None:
    """显示卡片信息"""
    print(f"  {index}. 卡片ID: {card.id}")
    print(f"     显示名称: {card.display_name}")
    print(f"     场景类型: {card.scene_type}")
    print(f"     角色类型: {card.role_type}")
    if card.bio:
        print(f"     简介: {card.bio[:50]}{'...' if len(card.bio) > 50 else ''}")
    print(f"     状态: {'活跃' if card.is_active else '非活跃'}")
    print(f"     可见性: {card.visibility}")
    print(f"     创建时间: {card.created_at}")
    print(f"     搜索代码: {card.search_code or 'N/A'}")

def show_deletion_summary(db: Session, deleted_count: int, affected_users: int) -> None:
    """显示删除摘要"""
    deleted_users = db.query(User).filter(User.status == 'deleted').count()
    active_cards = db.query(UserCard).filter(UserCard.is_deleted == 0).count()
    total_deleted_cards = db.query(UserCard).filter(UserCard.is_deleted == 1).count()
    
    print(f"\n=== 删除摘要 ===")
    print(f"已注销用户总数: {deleted_users}")
    print(f"本次删除的卡片数量: {deleted_count}")
    print(f"受影响的用户数量: {affected_users}")
    print(f"剩余活跃卡片: {active_cards}")
    print(f"已删除卡片总数: {total_deleted_cards}")

def confirm_deletion(cards_to_delete: List[UserCard], deleted_users: List[User]) -> bool:
    """确认是否删除卡片"""
    if not cards_to_delete:
        print("未找到需要删除的卡片")
        return False
    
    print(f"\n找到 {len(cards_to_delete)} 个属于已注销用户的卡片:")
    print("=" * 100)
    
    # 按用户分组显示卡片
    user_cards_map = {}
    for card in cards_to_delete:
        user = next((u for u in deleted_users if u.id == card.user_id), None)
        if user:
            user_key = f"{user.nick_name or '匿名用户'} ({user.phone or '无手机号'})"
            if user_key not in user_cards_map:
                user_cards_map[user_key] = []
            user_cards_map[user_key].append(card)
    
    # 显示每个用户的卡片
    for user_key, user_cards in user_cards_map.items():
        print(f"\n用户: {user_key}")
        print(f"卡片数量: {len(user_cards)}")
        print("-" * 80)
        
        # 显示前3个卡片的信息
        for i, card in enumerate(user_cards[:3]):
            show_card_info(card, i + 1)
        
        if len(user_cards) > 3:
            print(f"     ... 还有 {len(user_cards) - 3} 个卡片未显示")
    
    # 确认删除
    while True:
        response = input(f"\n是否删除这 {len(cards_to_delete)} 个卡片? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("请输入 'yes' 或 'no'")

def create_database_session() -> Session:
    """创建数据库会话"""
    try:
        # 尝试使用项目的get_db函数
        from app.main import app
        # 创建测试用的数据库会话
        engine = create_engine("sqlite:///./vmatch_dev.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    except Exception as e:
        print(f"使用项目数据库配置失败: {e}")
        print("使用备用数据库连接...")
        # 备用方案：直接连接SQLite数据库
        engine = create_engine("sqlite:///./vmatch_dev.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()

def main():
    """主函数"""
    print("=== 删除已注销用户的卡片 - SQLAlchemy ORM版本 ===")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='删除已注销用户的卡片')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式，只显示不删除')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    parser.add_argument('--force', action='store_true', help='强制删除，不确认')
    args = parser.parse_args()
    
    db = None
    try:
        # 创建数据库会话
        print("正在连接数据库...")
        db = create_database_session()
        
        print("正在查找已注销的用户...")
        
        # 获取已注销的用户
        deleted_users = get_deleted_users(db)
        
        if not deleted_users:
            print("未找到已注销的用户")
            return True
        
        print(f"找到 {len(deleted_users)} 个已注销的用户")
        
        if args.verbose:
            print("\n已注销用户列表:")
            for i, user in enumerate(deleted_users):
                print(f"  {i+1}. ID: {user.id}, 手机号: {user.phone or 'N/A'}, 昵称: {user.nick_name or 'N/A'}")
        
        # 收集所有需要删除的卡片
        all_cards_to_delete = []
        affected_users_count = 0
        
        for user in deleted_users:
            user_cards = get_user_active_cards(db, user.id)
            
            if user_cards:
                affected_users_count += 1
                all_cards_to_delete.extend(user_cards)
                
                if args.verbose:
                    print(f"用户 {user.phone or user.id} 有 {len(user_cards)} 个卡片需要删除")
        
        if not all_cards_to_delete:
            print("未找到需要删除的卡片")
            return True
        
        print(f"\n总共找到 {len(all_cards_to_delete)} 个属于已注销用户的卡片")
        
        # 干运行模式
        if args.dry_run:
            print("\n=== 干运行模式 ===")
            print("以下卡片将被删除（实际未执行删除操作）:")
            for i, card in enumerate(all_cards_to_delete[:10]):  # 只显示前10个
                print(f"  {i+1}. 卡片ID: {card.id}, 名称: {card.display_name}, 用户ID: {card.user_id}")
            
            if len(all_cards_to_delete) > 10:
                print(f"  ... 还有 {len(all_cards_to_delete) - 10} 个卡片")
            
            print(f"\n干运行完成，共 {len(all_cards_to_delete)} 个卡片将被删除")
            return True
        
        # 确认删除（除非强制模式）
        if not args.force and not confirm_deletion(all_cards_to_delete, deleted_users):
            print("取消删除操作")
            return True
        
        print(f"\n正在删除 {len(all_cards_to_delete)} 个卡片...")
        
        # 执行删除
        deleted_count = soft_delete_cards(db, all_cards_to_delete)
        
        print(f"成功删除 {deleted_count} 个卡片")
        
        # 显示删除摘要
        show_deletion_summary(db, deleted_count, affected_users_count)
        
        return True
        
    except Exception as e:
        print(f"发生错误: {e}")
        if db:
            db.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)