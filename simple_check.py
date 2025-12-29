import sys
sys.path.append('.')
from app.database import engine
from sqlalchemy import text

def simple_check():
    print("🔍 简单数据检查...")
    
    with engine.connect() as conn:
        # 检查总用户数
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        total_users = result.fetchone()[0]
        print(f"📊 总用户数: {total_users}")
        
        # 检查小红书用户
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE phone LIKE '2000%'"))
        xiaohongshu_users = result.fetchone()[0]
        print(f"📱 小红书用户: {xiaohongshu_users}")
        
        # 显示前几个用户
        if xiaohongshu_users > 0:
            result = conn.execute(text("SELECT phone, nick_name FROM users WHERE phone LIKE '2000%' ORDER BY phone LIMIT 3"))
            users = result.fetchall()
            print("📋 前3个用户:")
            for user in users:
                print(f"  手机: {user[0]}, 昵称: {user[1]}")
        
        # 检查用户卡片
        result = conn.execute(text("SELECT COUNT(*) FROM user_cards WHERE role_type = 'social_assistant'"))
        social_cards = result.fetchone()[0]
        print(f"💳 社交助手卡片: {social_cards}")

if __name__ == "__main__":
    simple_check()
    print("\n✅ 检查完成！")