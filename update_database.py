from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建数据库连接
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_database():
    db = SessionLocal()
    try:
        # 修改 user_card_topic_relations 表，将 user_card_id 改为 user_id
        print("开始更新数据库表结构...")
        
        # 1. 尝试删除原有的外键约束，如果不存在则忽略
        try:
            db.execute(text("""
                ALTER TABLE user_card_topic_relations 
                DROP FOREIGN KEY user_card_topic_relations_ibfk_1
            """))
            print("已删除原有的外键约束")
        except Exception as e:
            print(f"外键约束不存在或已删除: {e}")
        
        # 2. 检查 user_id 字段是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'user_card_topic_relations' AND COLUMN_NAME = 'user_id'
        """))
        user_id_exists = result.scalar() > 0
        
        if not user_id_exists:
            # 3. 添加 user_id 字段
            db.execute(text("""
                ALTER TABLE user_card_topic_relations 
                ADD COLUMN user_id VARCHAR(36) NULL
            """))
            print("已添加 user_id 字段")
        else:
            print("user_id 字段已存在，跳过添加")
        
        # 4. 从 user_cards 表中获取 user_id 并更新到 user_card_topic_relations
        db.execute(text("""
            UPDATE user_card_topic_relations uctr
            JOIN user_cards uc ON uctr.user_card_id = uc.id
            SET uctr.user_id = uc.user_id
        """))
        print("已更新 user_id 字段值")
        
        # 5. 将 user_id 字段设置为 NOT NULL
        db.execute(text("""
            ALTER TABLE user_card_topic_relations 
            MODIFY COLUMN user_id VARCHAR(36) NOT NULL
        """))
        print("已将 user_id 字段设置为 NOT NULL")
        
        # 6. 尝试添加外键约束，如果已存在则忽略
        try:
            db.execute(text("""
                ALTER TABLE user_card_topic_relations 
                ADD CONSTRAINT fk_user_card_topic_relations_user_id 
                FOREIGN KEY (user_id) REFERENCES users(id)
            """))
            print("已添加外键约束")
        except Exception as e:
            print(f"外键约束已存在或添加失败: {e}")
        
        # 7. 删除 user_card_id 字段
        db.execute(text("""
            ALTER TABLE user_card_topic_relations 
            DROP COLUMN user_card_id
        """))
        print("已删除 user_card_id 字段")
        
        # 8. 创建索引
        db.execute(text("""
            CREATE INDEX idx_user_card_topic_relations_user_id 
            ON user_card_topic_relations(user_id)
        """))
        print("已创建 user_id 索引")
        
        db.commit()
        print("数据库表结构更新完成！")
        
    except Exception as e:
        db.rollback()
        print(f"更新过程中出现错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_database()