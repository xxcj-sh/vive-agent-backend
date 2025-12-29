import sys
sys.path.append('.')
from app.database import engine
from sqlalchemy import text
import json

def verify_data():
    print('🔍 验证小红书美妆博主数据导入结果:')
    
    with engine.connect() as conn:
        # Check users table for our Xiaohongshu influencers
        result = conn.execute(text("""
            SELECT id, phone, nick_name, status, created_at 
            FROM users 
            WHERE phone LIKE '2000%' 
            ORDER BY phone
        """))
        users = result.fetchall()
        print(f'✅ 小红书用户: 找到 {len(users)} 条记录')
        
        for user in users:
            print(f"  📱 手机号: {user.phone}, 昵称: {user.nick_name}, 状态: {user.status}")
        
        # Check user_cards table for our influencers
        result = conn.execute(text("""
            SELECT uc.id, uc.user_id, uc.role_type, uc.scene_type, uc.display_name, uc.bio, u.phone 
            FROM user_cards uc 
            JOIN users u ON uc.user_id = u.id 
            WHERE u.phone LIKE '2000%' AND uc.role_type = 'social_assistant' 
            ORDER BY u.phone
        """))
        cards = result.fetchall()
        print(f'\n✅ 小红书用户卡片: 找到 {len(cards)} 条记录')
        
        for card in cards:
            print(f"  💳 用户: {card.phone}, 角色: {card.role_type}, 场景: {card.scene_type}, 显示名: {card.display_name}")
            print(f"     简介: {card.bio[:50]}...")
        
        # Check profile_data for persona information
        result = conn.execute(text("""
            SELECT uc.display_name, uc.profile_data 
            FROM user_cards uc 
            JOIN users u ON uc.user_id = u.id 
            WHERE u.phone LIKE '2000%' AND uc.role_type = 'social_assistant' 
            ORDER BY u.phone
        """))
        profiles = result.fetchall()
        print(f'\n✅ Profile_data人设数据: {len(profiles)} 条记录包含人设数据')
        
        for profile in profiles:
            if profile.profile_data:
                try:
                    persona_data = json.loads(profile.profile_data)
                    persona_text = persona_data.get('persona', '')
                    print(f"   昵称: {profile.display_name}, 人设长度: {len(persona_text)} 字符")
                except:
                    print(f"   昵称: {profile.display_name}, 人设数据格式异常")
            else:
                print(f"   昵称: {profile.display_name}, 无人设数据")

if __name__ == "__main__":
    verify_data()
    print('\n✅ 数据验证完成！')