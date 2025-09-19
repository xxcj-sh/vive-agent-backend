import sqlite3
conn = sqlite3.connect('vmatch_dev.db')
cursor = conn.cursor()

# 检查收藏操作
print('收藏操作详情:')
cursor.execute("SELECT id, user_id, target_user_id, target_card_id, scene_type, created_at FROM match_actions WHERE action_type = 'COLLECTION' ORDER BY created_at DESC")
collection_actions = cursor.fetchall()
print(f'收藏操作总数: {len(collection_actions)}')

for action in collection_actions:
    action_id, user_id, target_user_id, target_card_id, scene_type, created_at = action
    print(f'  ID: {action_id[:8]}...')
    print(f'    用户ID: {user_id[:8]}...')
    print(f'    目标用户ID: {target_user_id[:8]}...')
    print(f'    目标卡片ID: {target_card_id[:8]}...' if len(target_card_id) > 8 else f'    目标卡片ID: {target_card_id}')
    print(f'    场景类型: {scene_type}')
    print(f'    创建时间: {created_at}')
    print()

# 检查所有操作类型
print('所有操作类型:')
cursor.execute("SELECT DISTINCT action_type FROM match_actions")
action_types = cursor.fetchall()
for action_type in action_types:
    print(f'  {action_type[0]}')

conn.close()