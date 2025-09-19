import sys
sys.path.append('.')
from app.database import SessionLocal
from app.models.user_card_db import UserCard

db = SessionLocal()

# 检查卡片ID是否存在
card_id = '4c9bfbb9-78dc-49af-86b0-19d4b27bd636'
card = db.query(UserCard).filter(UserCard.id == card_id).first()

print(f'卡片ID {card_id} 存在: {card is not None}')

if card:
    print(f'卡片信息:')
    print(f'  ID: {card.id}')
    print(f'  用户ID: {card.user_id}')
    print(f'  场景: {card.scene_type}')
    print(f'  角色: {card.role_type}')
    print(f'  显示名称: {card.display_name}')
    print(f'  是否激活: {card.is_active}')
else:
    # 检查数据库中有哪些卡片
    print('数据库中的前5个卡片:')
    cards = db.query(UserCard).limit(5).all()
    for c in cards:
        print(f'  ID: {c.id}, 用户ID: {c.user_id}, 场景: {c.scene_type}, 角色: {c.role_type}')

db.close()