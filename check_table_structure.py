import sys
sys.path.append('.')
from app.database import engine
from sqlalchemy import text
import traceback

def check_table_structure():
    """检查数据库表结构"""
    print("🔍 检查数据库表结构...")
    
    try:
        with engine.connect() as conn:
            # 检查 users 表结构
            result = conn.execute(text("DESCRIBE users"))
            users_columns = result.fetchall()
            print("\n📋 users 表结构:")
            for col in users_columns:
                print(f"  {col[0]}: {col[1]} {col[2]} {col[3]}")
            
            # 检查 user_cards 表结构
            result = conn.execute(text("DESCRIBE user_cards"))
            cards_columns = result.fetchall()
            print("\n📋 user_cards 表结构:")
            for col in cards_columns:
                print(f"  {col[0]}: {col[1]} {col[2]} {col[3]}")
                
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        traceback.print_exc()

def check_existing_data():
    """检查现有数据"""
    print("\n🔍 检查现有数据...")
    
    try:
        with engine.connect() as conn:
            # 检查所有用户
            result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
            total_users = result.fetchone()[0]
            print(f"📊 总用户数: {total_users}")
            
            # 检查我们的小红书用户
            result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE phone LIKE '2000%'"))
            xiaohongshu_users = result.fetchone()[0]
            print(f"📱 小红书用户: {xiaohongshu_users}")
            
            # 检查用户卡片
            result = conn.execute(text("SELECT COUNT(*) as count FROM user_cards"))
            total_cards = result.fetchone()[0]
            print(f"💳 总卡片数: {total_cards}")
            
            # 检查社交助手卡片
            result = conn.execute(text("SELECT COUNT(*) as count FROM user_cards WHERE role_type = 'social_assistant'"))
            social_cards = result.fetchone()[0]
            print(f"🤝 社交助手卡片: {social_cards}")
            
            # 显示一些样本数据
            if xiaohongshu_users > 0:
                print(f"\n📋 小红书用户样本:")
                result = conn.execute(text("SELECT phone, nick_name, status FROM users WHERE phone LIKE '2000%' LIMIT 5"))
                samples = result.fetchall()
                for sample in samples:
                    print(f"  手机: {sample[0]}, 昵称: {sample[1]}, 状态: {sample[2]}")
            
    except Exception as e:
        print(f"❌ 检查数据失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure()
    check_existing_data()
    print("\n✅ 检查完成！")