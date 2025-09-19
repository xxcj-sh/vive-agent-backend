import sqlite3
import os

# 找到数据库文件
db_path = None
for path in ['vmatch_dev.db', 'vmatch.db', '../vmatch_dev.db']:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print('找不到数据库文件')
    exit(1)

print(f'使用数据库: {db_path}')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='match_actions'")
    if not cursor.fetchone():
        print('match_actions 表不存在')
        exit(1)
    
    # 统计总记录数
    cursor.execute('SELECT COUNT(*) FROM match_actions')
    total = cursor.fetchone()[0]
    print(f'MatchAction 总记录数: {total}')
    
    # 按操作类型统计
    cursor.execute('SELECT action_type, COUNT(*) FROM match_actions GROUP BY action_type')
    action_stats = cursor.fetchall()
    print('\n按操作类型统计:')
    for action_type, count in action_stats:
        print(f'  {action_type}: {count}')
    
    # 按场景类型统计
    cursor.execute('SELECT scene_type, COUNT(*) FROM match_actions GROUP BY scene_type')
    scene_stats = cursor.fetchall()
    print('\n按场景类型统计:')
    for scene_type, count in scene_stats:
        print(f'  {scene_type}: {count}')
    
    # 查看最新的5条记录
    cursor.execute('SELECT id, user_id, target_user_id, action_type, scene_type, created_at FROM match_actions ORDER BY created_at DESC LIMIT 5')
    latest_actions = cursor.fetchall()
    print('\n最新的5条记录:')
    for action in latest_actions:
        action_id, user_id, target_user_id, action_type, scene_type, created_at = action
        print(f'  ID: {action_id[:8]}..., 用户: {user_id[:8]}..., 目标: {target_user_id[:8]}..., 类型: {action_type}, 场景: {scene_type}, 时间: {created_at}')
    
    # 检查是否有收藏操作
    cursor.execute('SELECT COUNT(*) FROM match_actions WHERE action_type = ?', ('collection',))
    collection_count = cursor.fetchone()[0]
    print(f'\n收藏操作数量: {collection_count}')
    
finally:
    conn.close()