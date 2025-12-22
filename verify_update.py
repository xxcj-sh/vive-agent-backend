from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建数据库连接
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def verify_update():
    with engine.connect() as conn:
        # 检查表结构
        result = conn.execute(text("""
            DESCRIBE user_card_topic_relations
        """))
        
        print("user_card_topic_relations 表结构:")
        for row in result:
            print(f"列名: {row.Field}, 类型: {row.Type}, 可为空: {row.Null}, 键: {row.Key}, 默认值: {row.Default}, 额外: {row.Extra}")
        
        # 检查索引
        result = conn.execute(text("""
            SHOW INDEX FROM user_card_topic_relations
        """))
        
        print("\n索引信息:")
        for row in result:
            print(f"索引名: {row.Key_name}, 列名: {row.Column_name}, 唯一: {row.Non_unique == 0}")
        
        # 检查数据
        result = conn.execute(text("""
            SELECT COUNT(*) as total FROM user_card_topic_relations
        """))
        total = result.scalar()
        print(f"\n总记录数: {total}")
        
        if total > 0:
            result = conn.execute(text("""
                SELECT * FROM user_card_topic_relations LIMIT 1
            """))
            row = result.first()
            print(f"\n示例记录: {row}")

if __name__ == "__main__":
    verify_update()