#!/usr/bin/env python3
"""
用户数据管理脚本
用于安全删除用户及其关联的所有数据

使用方法:
    python manage_user_data.py --user-id <用户ID> [--dry-run] [--verbose]
    python manage_user_data.py --phone <手机号> [--dry-run] [--verbose]
    python manage_user_data.py --list-users
"""

import argparse
import sys
import os
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.db_config import DATABASE_URL, engine, SessionLocal
from app.models.user import User
from app.models.match import Match
from app.models.chat_message import ChatMessage, ChatConversation
from app.models.user_card_db import UserCard

class UserDataManager:
    """用户数据管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.deleted_counts = {}
        
    def get_user_by_id(self, session: Session, user_id: str) -> User:
        """通过ID获取用户"""
        return session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_phone(self, session: Session, phone: str) -> User:
        """通过手机号获取用户"""
        return session.query(User).filter(User.phone == phone).first()
    
    def list_all_users(self, session: Session) -> List[Dict[str, Any]]:
        """列出所有用户"""
        users = session.query(User).all()
        return [
            {
                "id": user.id,
                "phone": user.phone,
                "nick_name": user.nick_name,
                "created_at": user.created_at,
                "is_active": user.is_active
            }
            for user in users
        ]
    
    def count_user_data(self, session: Session, user_id: str) -> Dict[str, int]:
        """统计用户数据量"""
        counts = {}
        
        # 用户卡片
        counts['user_cards'] = session.query(UserCard).filter(
            UserCard.user_id == user_id
        ).count()
        
        # 匹配记录（作为用户）
        counts['matches'] = session.query(Match).filter(
            Match.user_id == user_id
        ).count()
        
        # 聊天记录（作为发送者）
        counts['sent_messages'] = session.query(ChatMessage).filter(
            ChatMessage.sender_id == user_id
        ).count()
        
        # 聊天记录（作为接收者）
        counts['received_messages'] = session.query(ChatMessage).filter(
            ChatMessage.receiver_id == user_id
        ).count()
        
        # 聊天会话
        counts['chat_conversations'] = session.query(ChatConversation).filter(
            (ChatConversation.user1_id == user_id) | 
            (ChatConversation.user2_id == user_id)
        ).count()
        
        return counts
    
    def delete_user_cards(self, session: Session, user_id: str) -> int:
        """删除用户卡片"""
        deleted = session.query(UserCard).filter(
            UserCard.user_id == user_id
        ).delete(synchronize_session=False)
        self.deleted_counts['user_cards'] = deleted
        return deleted
    
    def delete_user_matches(self, session: Session, user_id: str) -> int:
        """删除用户匹配记录"""
        # 首先删除关联的聊天记录和会话
        matches = session.query(Match).filter(Match.user_id == user_id).all()
        deleted_count = 0
        
        for match in matches:
            # 删除聊天记录
            session.query(ChatMessage).filter(
                ChatMessage.match_id == match.id
            ).delete(synchronize_session=False)
            
            # 删除聊天会话
            session.query(ChatConversation).filter(
                ChatConversation.match_id == match.id
            ).delete(synchronize_session=False)
            
            # 删除匹配详情（MatchDetail是Match的关系属性，会自动级联删除）
            
            # 删除匹配记录
            session.delete(match)
            deleted_count += 1
            
        self.deleted_counts['matches'] = deleted_count
        return deleted_count
    
    def delete_user_chat_data(self, session: Session, user_id: str) -> Dict[str, int]:
        """删除用户聊天数据"""
        deleted = {}
        
        # 获取用户参与的所有匹配
        user_matches = session.query(Match).filter(Match.user_id == user_id).all()
        match_ids = [m.id for m in user_matches]
        
        # 删除聊天记录
        deleted['chat_messages'] = session.query(ChatMessage).filter(
            (ChatMessage.sender_id == user_id) | 
            (ChatMessage.receiver_id == user_id)
        ).delete(synchronize_session=False)
        
        # 删除聊天会话
        deleted['chat_conversations'] = session.query(ChatConversation).filter(
            (ChatConversation.user1_id == user_id) | 
            (ChatConversation.user2_id == user_id)
        ).delete(synchronize_session=False)
        
        return deleted
    
    def delete_user_account(self, session: Session, user_id: str) -> bool:
        """删除用户账户"""
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            self.deleted_counts['user_account'] = 1
            return True
        return False
    
    def safe_delete_user(self, user_id: str, dry_run: bool = True, verbose: bool = False) -> Dict[str, Any]:
        """安全删除用户及其所有数据"""
        session = self.SessionLocal()
        try:
            # 检查用户是否存在
            user = self.get_user_by_id(session, user_id)
            if not user:
                return {"error": f"用户 {user_id} 不存在"}
            
            # 统计当前数据量
            data_counts = self.count_user_data(session, user_id)
            
            if verbose:
                print(f"\n=== 用户数据统计 ===")
                print(f"用户ID: {user_id}")
                print(f"手机号: {user.phone}")
                print(f"昵称: {user.nick_name}")
                print(f"用户卡片: {data_counts['user_cards']}")
                print(f"匹配记录: {data_counts['matches']}")
                print(f"发送消息: {data_counts['sent_messages']}")
                print(f"接收消息: {data_counts['received_messages']}")
                print(f"聊天会话: {data_counts['chat_conversations']}")
            
            if dry_run:
                return {
                    "status": "dry_run",
                    "user_id": user_id,
                    "phone": user.phone,
                    "nick_name": user.nick_name,
                    "data_counts": data_counts,
                    "message": "这是模拟删除，实际数据未删除"
                }
            
            # 开始事务删除
            self.deleted_counts = {}
            
            # 按顺序删除数据（避免外键约束）
            deleted_chat = self.delete_user_chat_data(session, user_id)
            deleted_cards = self.delete_user_cards(session, user_id)
            deleted_matches = self.delete_user_matches(session, user_id)
            deleted_user = self.delete_user_account(session, user_id)
            
            session.commit()
            
            return {
                "status": "success",
                "user_id": user_id,
                "phone": user.phone,
                "nick_name": user.nick_name,
                "deleted_counts": {
                    **self.deleted_counts,
                    **deleted_chat
                },
                "message": "用户数据已成功删除"
            }
            
        except SQLAlchemyError as e:
            session.rollback()
            return {"error": f"数据库错误: {str(e)}"}
        except Exception as e:
            session.rollback()
            return {"error": f"删除失败: {str(e)}"}
        finally:
            session.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="用户数据管理工具")
    parser.add_argument("--user-id", type=str, help="用户ID")
    parser.add_argument("--phone", type=str, help="手机号")
    parser.add_argument("--dry-run", action="store_true", help="模拟删除，不实际删除数据")
    parser.add_argument("--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("--list-users", action="store_true", help="列出所有用户")
    
    args = parser.parse_args()
    
    manager = UserDataManager()
    
    if args.list_users:
        session = manager.SessionLocal()
        try:
            users = manager.list_all_users(session)
            print("\n=== 用户列表 ===")
            for user in users:
                print(f"ID: {user['id']}")
                print(f"手机: {user['phone']}")
                print(f"昵称: {user['nick_name']}")
                print(f"创建时间: {user['created_at']}")
                print(f"状态: {'激活' if user['is_active'] else '禁用'}")
                print("-" * 40)
            print(f"总计: {len(users)} 个用户")
        finally:
            session.close()
        return
    
    if not args.user_id and not args.phone:
        print("错误: 请提供 --user-id 或 --phone 参数")
        parser.print_help()
        return
    
    # 获取用户ID
    user_id = args.user_id
    if args.phone and not user_id:
        session = manager.SessionLocal()
        try:
            user = manager.get_user_by_phone(session, args.phone)
            if user:
                user_id = user.id
                print(f"找到用户: {user.phone} -> {user_id}")
            else:
                print(f"错误: 手机号 {args.phone} 对应的用户不存在")
                return
        finally:
            session.close()
    
    if user_id:
        result = manager.safe_delete_user(
            user_id=user_id,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        if "error" in result:
            print(f"错误: {result['error']}")
        else:
            print("\n=== 删除结果 ===")
            print(f"用户: {result.get('phone', user_id)}")
            print(f"昵称: {result.get('nick_name', 'N/A')}")
            
            if result.get('status') == 'dry_run':
                print("\n[模拟删除] 数据量统计:")
                counts = result['data_counts']
            else:
                print("\n[实际删除] 已删除数据:")
                counts = result.get('deleted_counts', {})
            
            for key, count in counts.items():
                print(f"  {key}: {count}")
            
            print(f"\n{result.get('message', '')}")

if __name__ == "__main__":
    main()