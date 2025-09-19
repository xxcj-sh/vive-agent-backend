from app.models.user_card import CardCreate, CardUpdate, Card
from pydantic import ValidationError
import json

# 测试数据 - 数组格式
test_data = {
    'role_type': 'housing_seeker',
    'scene_type': 'housing',
    'display_name': '测试卡片',
    'trigger_and_output': [
        {
            'id': '123',
            'trigger': '对方喜欢户外运动',
            'output': '推荐一起爬山活动',
            'description': '',
            'isActive': True,
            'hasFrequencyLimit': False,
            'priority': 5
        }
    ]
}

try:
    # 测试 CardCreate
    card_create = CardCreate(**test_data)
    print('✅ CardCreate 验证通过')
    print(f'trigger_and_output 类型: {type(card_create.trigger_and_output)}')
    print(f'trigger_and_output 内容: {card_create.trigger_and_output}')
    
    # 测试 Card
    card_data = {
        'id': 'test_id',
        'user_id': 'user_123',
        'is_active': 1,
        'is_deleted': 0,
        'created_at': '2024-01-01T00:00:00',
        'role_type': 'housing_seeker',
        'scene_type': 'housing', 
        'display_name': '测试卡片',
        'trigger_and_output': test_data['trigger_and_output']
    }
    card = Card(**card_data)
    print('✅ Card 验证通过')
    
    # 测试 CardUpdate
    update_data = {'trigger_and_output': test_data['trigger_and_output']}
    card_update = CardUpdate(**update_data)
    print('✅ CardUpdate 验证通过')
    
except ValidationError as e:
    print(f'❌ 验证失败: {e}')
except Exception as e:
    print(f'❌ 其他错误: {e}')