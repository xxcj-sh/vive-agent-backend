import sqlite3
conn = sqlite3.connect('vmatch_dev.db')
cursor = conn.cursor()

print('数据完整性检查:')
print('=' * 50)

# 1. 检查用户ID和目标用户ID相同的记录
print('1. 用户ID和目标用户ID相同的记录:')
cursor.execute("SELECT id, user_id, target_user_id, action_type, scene_type, created_at FROM match_actions WHERE user_id = target_user_id")
same_user_actions = cursor.fetchall()
print(f'   数量: {len(same_user_actions)}')
for action in same_user_actions:
    action_id, user_id, target_user_id, action_type, scene_type, created_at = action
    print(f'   ID: {action_id[:8]}..., 类型: {action_type}, 场景: {scene_type}, 时间: {created_at}')

print()

# 2. 检查目标卡片ID的格式
print('2. 目标卡片ID格式检查:')
cursor.execute("SELECT DISTINCT target_card_id FROM match_actions WHERE action_type = 'COLLECTION'")
card_ids = cursor.fetchall()
print(f'   收藏操作中的目标卡片ID:')
for card_id in card_ids:
    print(f'   {card_id[0]}')

print()

# 3. 检查场景类型为NULL的记录
print('3. 场景类型为NULL的记录:')
cursor.execute("SELECT id, user_id, target_user_id, action_type, scene_type, created_at FROM match_actions WHERE scene_type IS NULL OR scene_type = 'None'")
null_scene_actions = cursor.fetchall()
print(f'   数量: {len(null_scene_actions)}')
for action in null_scene_actions:
    action_id, user_id, target_user_id, action_type, scene_type, created_at = action
    print(f'   ID: {action_id[:8]}..., 类型: {action_type}, 场景: {scene_type}, 时间: {created_at}')

print()

# 4. 检查所有记录的用户ID格式
print('4. 用户ID格式统计:')
cursor.execute("SELECT user_id, COUNT(*) as count FROM match_actions GROUP BY user_id ORDER BY count DESC")
user_stats = cursor.fetchall()
print(f'   不同用户数量: {len(user_stats)}')
for user_id, count in user_stats:
    print(f'   用户ID: {user_id[:8]}...: {count} 条记录')

print()

# 5. 检查时间范围
print('5. 时间范围统计:')
cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM match_actions")
time_range = cursor.fetchone()
print(f'   最早记录: {time_range[0]}')
print(f'   最新记录: {time_range[1]}')

conn.close()