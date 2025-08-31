#!/usr/bin/env python3
"""
测试脚本：查询数据库现有用户信息
用于展示数据库中所有用户的完整信息
"""

import sys
import os
from datetime import datetime
from typing import List, Optional

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models.user import User


def format_user_info(user: User) -> str:
    """格式化用户信息为可读字符串"""
    info = f"""
{'='*60}
用户ID: {user.id}
微信OpenID: {user.wechat_openid}
昵称: {user.nickname or '未设置'}
性别: {user.gender or '未设置'}
年龄: {user.age or '未设置'}
身高: {user.height or '未设置'}
体重: {user.weight or '未设置'}
职业: {user.occupation or '未设置'}
教育程度: {user.education or '未设置'}
兴趣爱好: {user.interests or '未设置'}
个人简介: {user.bio or '未设置'}
头像URL: {user.avatar_url or '未设置'}
位置信息: {user.location or '未设置'}
是否激活: {'是' if user.is_active else '否'}
创建时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '未知'}
更新时间: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else '未知'}
{'='*60}
    """
    return info


def query_all_users() -> List[User]:
    """查询所有用户"""
    db: Session = next(get_db())
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        print(f"查询用户时发生错误: {e}")
        return []
    finally:
        db.close()


def query_user_by_id(user_id: int) -> Optional[User]:
    """根据ID查询特定用户"""
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception as e:
        print(f"查询用户ID {user_id} 时发生错误: {e}")
        return None
    finally:
        db.close()


def query_user_by_openid(openid: str) -> Optional[User]:
    """根据微信OpenID查询用户"""
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.wechat_openid == openid).first()
        return user
    except Exception as e:
        print(f"查询OpenID {openid} 时发生错误: {e}")
        return None
    finally:
        db.close()


def get_user_statistics() -> dict:
    """获取用户统计信息"""
    db: Session = next(get_db())
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        inactive_users = total_users - active_users
        
        # 性别统计
        male_count = db.query(User).filter(User.gender == '男').count()
        female_count = db.query(User).filter(User.gender == '女').count()
        unknown_gender = total_users - male_count - female_count
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'male_count': male_count,
            'female_count': female_count,
            'unknown_gender': unknown_gender
        }
    except Exception as e:
        print(f"获取统计信息时发生错误: {e}")
        return {}
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 80)
    print("数据库用户查询测试脚本")
    print("=" * 80)
    
    # 获取用户统计信息
    print("\n📊 用户统计信息:")
    stats = get_user_statistics()
    if stats:
        print(f"总用户数: {stats['total_users']}")
        print(f"活跃用户: {stats['active_users']}")
        print(f"非活跃用户: {stats['inactive_users']}")
        print(f"男性用户: {stats['male_count']}")
        print(f"女性用户: {stats['female_count']}")
        print(f"未知性别: {stats['unknown_gender']}")
    
    # 查询所有用户
    print("\n👥 所有用户信息:")
    users = query_all_users()
    
    if not users:
        print("数据库中暂无用户数据")
        return
    
    print(f"找到 {len(users)} 个用户:")
    
    for i, user in enumerate(users, 1):
        print(f"\n第 {i} 个用户:")
        print(format_user_info(user))
    
    # 交互式查询
    print("\n" + "=" * 80)
    print("交互式查询 (输入 'quit' 退出)")
    print("=" * 80)
    
    while True:
        print("\n选择查询方式:")
        print("1. 根据用户ID查询")
        print("2. 根据微信OpenID查询")
        print("3. 重新显示所有用户")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            try:
                user_id = int(input("请输入用户ID: "))
                user = query_user_by_id(user_id)
                if user:
                    print(f"\n找到用户:")
                    print(format_user_info(user))
                else:
                    print(f"未找到ID为 {user_id} 的用户")
            except ValueError:
                print("请输入有效的数字ID")
        
        elif choice == '2':
            openid = input("请输入微信OpenID: ").strip()
            if openid:
                user = query_user_by_openid(openid)
                if user:
                    print(f"\n找到用户:")
                    print(format_user_info(user))
                else:
                    print(f"未找到OpenID为 {openid} 的用户")
            else:
                print("OpenID不能为空")
        
        elif choice == '3':
            users = query_all_users()
            if users:
                print(f"\n找到 {len(users)} 个用户:")
                for i, user in enumerate(users, 1):
                    print(f"\n第 {i} 个用户:")
                    print(format_user_info(user))
            else:
                print("数据库中暂无用户数据")
        
        elif choice == '4' or choice.lower() == 'quit':
            print("退出查询程序")
            break
        
        else:
            print("无效选择，请输入 1-4")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行时发生错误: {e}")
        import traceback
        traceback.print_exc()