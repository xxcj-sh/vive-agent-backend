import uuid
from app.services.user_profile.user_profile_service import UserProfileService
from app.models.user_profile import UserProfileCreate, UserProfileUpdate
from app.database import SessionLocal

# 创建测试数据
db = SessionLocal()
service = UserProfileService(db)

user_id = str(uuid.uuid4())
print(f'用户ID: {user_id}')

# 创建画像
profile_data = UserProfileCreate(
    user_id=user_id,
    raw_profile='{"version": 1}',
    update_reason="初始创建"
)
profile = service.create_user_profile(profile_data)
print(f'创建画像ID: {profile.id}')

# 更新两次
for i in range(2, 4):
    update_data = UserProfileUpdate(
        raw_profile=f'{{"version": {i}}}',
        update_reason=f"更新到版本 {i}"
    )
    service.update_user_profile(profile.id, update_data)
    print(f'更新到版本 {i}')

# 获取历史记录
history = service.get_profile_history(user_id)
print(f'历史记录数量: {len(history)}')
for i, h in enumerate(history):
    print(f'记录 {i}: version={h.version}, created_at={h.created_at}, change_type={h.change_type}')

db.close()