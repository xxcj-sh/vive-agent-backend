# 卡片返回数据 JSON 样本参考文档

本文档整理了 vmatch-backend 项目中各个不同类型卡片通过 `get_card_by_id` 函数返回的数据结构 JSON 样本，供前端开发参考。

## 📋 目录

1. [通用数据结构](#通用数据结构)
2. [活动组织者卡片](#活动组织者卡片)
3. [活动参与者卡片](#活动参与者卡片)
4. [找房者卡片](#找房者卡片)
5. [房源卡片](#房源卡片)
6. [约会交友卡片](#约会交友卡片)
7. [用户基础信息结构](#用户基础信息结构)

---

## 通用数据结构

所有卡片类型都包含以下基础字段：

```json
{
  "id": "card_activity_activity_organizer_abc12345",
  "user_id": "user_123456789",
  "role_type": "activity_organizer",
  "scene_type": "activity",
  "display_name": "张三",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/user123.jpg",
  "bio": "我是一个热爱组织活动的人",
  "profile_data": {...},
  "preferences": {...},
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:20:00",
  "username": "张三",
  "email": null,
  "nick_name": "张三",
  "age": 28,
  "gender": 1,
  "occupation": "产品经理",
  "location": ["北京市", "朝阳区"],
  "phone": "13800138000",
  "education": "本科",
  "interests": ["户外运动", "摄影", "旅行"]
}
```

---

## 活动组织者卡片

### 场景类型：`activity`
### 角色类型：`activity_organizer`

```json
{
  "id": "card_activity_activity_organizer_abc12345",
  "user_id": "user_123456789",
  "role_type": "activity_organizer",
  "scene_type": "activity",
  "display_name": "户外达人小明",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/organizer123.jpg",
  "bio": "专业户外活动组织者，5年经验，已成功举办100+场活动",
  "profile_data": {
    "activity_start_time": "2024-02-10T09:00:00",
    "activity_cost": "100-200元/人",
    "activity_city": "北京",
    "activity_types": ["徒步", "露营", "登山", "骑行"],
    "activity_end_time": "2024-02-10T17:00:00",
    "activity_location": "香山公园",
    "activity_max_participants": 20,
    "activity_min_participants": 5,
    "organizing_experience": "5年专业户外活动组织经验",
    "specialties": ["路线规划", "安全指导", "团队建设"],
    "frequency": "每周2-3次",
    "locations": ["香山", "西山", "密云", "怀柔"],
    "past_activities": [
      {
        "name": "香山徒步",
        "date": "2024-01-20",
        "participants": 15,
        "rating": 4.8
      },
      {
        "name": "露营观星",
        "date": "2024-01-13",
        "participants": 8,
        "rating": 4.9
      }
    ]
  },
  "preferences": {
    "participant_requirements": {
      "min_age": 18,
      "max_age": 60,
      "fitness_level": "中等以上",
      "experience": "不限"
    },
    "activity_types": ["徒步", "露营", "登山"],
    "weather_dependency": "flexible",
    "group_size_preference": "5-20人"
  },
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:20:00",
  "username": "户外达人小明",
  "nick_name": "户外达人小明",
  "age": 32,
  "gender": 1,
  "occupation": "户外教练",
  "location": ["北京市", "海淀区"],
  "phone": "13900139000",
  "education": "大专",
  "interests": ["户外运动", "摄影", "探险"]
}
```

---

## 活动参与者卡片

### 场景类型：`activity`
### 角色类型：`activity_participant`

```json
{
  "id": "card_activity_activity_participant_def67890",
  "user_id": "user_987654321",
  "role_type": "activity_participant",
  "scene_type": "activity",
  "display_name": "小李",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/participant456.jpg",
  "bio": "喜欢参加各种户外活动，希望认识志同道合的朋友",
  "profile_data": {
    "interests": ["徒步", "摄影", "美食", "旅行"],
    "availability": {
      "weekday": "18:00-22:00",
      "weekend": "全天",
      "holiday": "全天"
    },
    "experience_level": {
      "hiking": "中级",
      "camping": "初级",
      "photography": "高级"
    },
    "transportation": ["自驾", "地铁", "公交"],
    "budget_range": {
      "min": 50,
      "max": 300,
      "currency": "元"
    }
  },
  "preferences": {
    "activity_types": ["徒步", "摄影", "美食探索", "文化体验"],
    "group_size": "5-15人",
    "duration": "半天到一天",
    "difficulty_level": ["简单", "中等"],
    "location_preference": "北京市内及周边"
  },
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-20T09:15:00",
  "updated_at": "2024-01-20T11:30:00",
  "username": "小李",
  "nick_name": "小李",
  "age": 26,
  "gender": 2,
  "occupation": "设计师",
  "location": ["北京市", "朝阳区"],
  "phone": "13700137000",
  "education": "本科",
  "interests": ["摄影", "美食", "旅行", "瑜伽"]
}
```

---

## 找房者卡片

### 场景类型：`housing`
### 角色类型：`housing_seeker`

```json
{
  "id": "card_housing_housing_seeker_ghi12345",
  "user_id": "user_111222333",
  "role_type": "housing_seeker",
  "scene_type": "housing",
  "display_name": "小王找房",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/seeker789.jpg",
  "bio": "在望京工作的程序员，希望找到安静舒适的住所",
  "profile_data": {
    "budget_range": [3000, 5000],
    "preferred_areas": ["望京", "酒仙桥", "朝阳公园", "三元桥"],
    "room_type": "主卧独卫",
    "move_in_date": "2024-02-01",
    "lease_duration": "一年",
    "lifestyle": "安静，不抽烟，偶尔做饭",
    "work_schedule": "朝九晚六，偶尔加班",
    "pets": false,
    "smoking": false,
    "occupation": "软件工程师",
    "company_location": "望京SOHO"
  },
  "preferences": {
    "roommate_gender": "any",
    "roommate_age_range": [22, 35],
    "shared_facilities": ["厨房", "洗衣机", "阳台"],
    "transportation": ["地铁14号线", "地铁15号线", "公交"],
    "nearby_facilities": ["超市", "餐厅", "健身房", "公园"]
  },
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-18T16:45:00",
  "updated_at": "2024-01-19T10:20:00",
  "username": "小王",
  "nick_name": "小王",
  "age": 27,
  "gender": 1,
  "occupation": "软件工程师",
  "location": ["北京市", "朝阳区"],
  "phone": "13600136000",
  "education": "本科",
  "interests": ["编程", "阅读", "羽毛球"]
}
```

---

## 房源卡片

### 场景类型：`housing`
### 角色类型：`housing_provider`

```json
{
  "id": "card_housing_housing_provider_jkl67890",
  "user_id": "user_444555666",
  "role_type": "housing_provider",
  "scene_type": "housing",
  "display_name": "李房东",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/landlord321.jpg",
  "bio": "个人房东，直租无中介费，欢迎爱干净、作息规律的租客",
  "profile_data": {
    "title": "望京精装主卧独卫出租",
    "house_type": "合租",
    "room_count": 4,
    "area": 25.5,
    "floor": 15,
    "total_floors": 28,
    "orientation": "南向",
    "community_name": "望京花园",
    "district": "朝阳区",
    "address": "北京市朝阳区望京街10号",
    "nearby_stations": ["望京站", "阜通站"],
    "monthly_rent": 3800,
    "deposit": 3800,
    "payment_method": "押一付三",
    "furniture": ["床", "衣柜", "书桌", "椅子", "空调"],
    "appliances": ["洗衣机", "冰箱", "热水器", "微波炉"],
    "facilities": ["电梯", "燃气", "暖气", "宽带"],
    "landlord_type": "个人",
    "response_time": "2小时内回复",
    "viewing_available": true,
    "tags": ["近地铁", "精装修", "随时看房", "拎包入住"],
    "highlights": ["南向采光好", "独立卫生间", "小区环境优美", "近地铁站"],
    "images": [
      "http://192.168.71.103:8000/uploads/houses/room1.jpg",
      "http://192.168.71.103:8000/uploads/houses/room2.jpg",
      "http://192.168.71.103:8000/uploads/houses/bathroom.jpg"
    ],
    "description": "房子是3室1厅的合租，出租的是主卧带独立卫生间，南向采光好，精装修，家具家电齐全，拎包入住。小区环境优美，绿化率高，24小时保安，近地铁14号线望京站，步行5分钟，周边配套设施齐全。",
    "available_date": "2024-01-25",
    "lease_term": "一年起租",
    "pet_allowed": false,
    "smoking_allowed": false,
    "created_at": "2024-01-15T14:30:00",
    "updated_at": "2024-01-19T09:15:00"
  },
  "preferences": {
    "tenant_requirements": {
      "stable_income": true,
      "no_pets": true,
      "no_smoking": true,
      "quiet_lifestyle": true
    },
    "payment_methods": ["微信", "支付宝", "银行转账"]
  },
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-15T14:30:00",
  "updated_at": "2024-01-19T09:15:00",
  "username": "李房东",
  "nick_name": "李房东",
  "age": 45,
  "gender": 1,
  "occupation": "个体经营",
  "location": ["北京市", "朝阳区"],
  "phone": "13500135000",
  "education": "高中",
  "interests": ["房地产投资", "旅游", "美食"]
}
```

---

## 约会交友卡片

### 场景类型：`dating`
### 角色类型：`dating_seeker`

```json
{
  "id": "card_dating_dating_seeker_mno54321",
  "user_id": "user_777888999",
  "role_type": "dating_seeker",
  "scene_type": "dating",
  "display_name": "Cathy",
  "avatar_url": "http://192.168.71.103:8000/uploads/avatars/dating789.jpg",
  "bio": "温柔善良的女生，喜欢旅行和美食，希望找到真诚、有责任感的另一半",
  "profile_data": {
    "age": 26,
    "height": 165,
    "education": "硕士",
    "occupation": "市场经理",
    "income_range": "15k-20k",
    "relationship_status": "single",
    "looking_for": "认真交往，以结婚为目的",
    "hobbies": ["旅行", "摄影", "烹饪", "瑜伽", "阅读"],
    "personality": ["温柔", "开朗", "善解人意", "有责任心"],
    "lifestyle": {
      "diet": "荤素搭配",
      "exercise": "每周3-4次",
      "social": "偶尔聚会",
      "travel": "每年2-3次长途旅行"
    }
  },
  "preferences": {
    "age_range": [26, 35],
    "height_range": [175, 185],
    "education_level": ["本科", "硕士", "博士"],
    "personality_preferences": ["成熟稳重", "幽默风趣", "有上进心", "善良体贴"],
    "lifestyle_preferences": {
      "smoking": "不接受",
      "drinking": "偶尔可以接受",
      "exercise": "最好有规律运动习惯"
    },
    "relationship_goals": "认真交往，以结婚为目的"
  },
  "visibility": "public",
  "is_active": 1,
  "created_at": "2024-01-20T20:00:00",
  "updated_at": "2024-01-21T10:30:00",
  "username": "Cathy",
  "nick_name": "Cathy",
  "age": 26,
  "gender": 2,
  "occupation": "市场经理",
  "location": ["北京市", "海淀区"],
  "phone": "13400134000",
  "education": "硕士",
  "interests": ["旅行", "摄影", "美食", "瑜伽"]
}
```

---

## 用户基础信息结构

所有卡片都包含以下用户基础信息字段：

```json
{
  "username": "显示的用户名",
  "email": null,
  "nick_name": "用户昵称",
  "age": 28,
  "gender": 1, // 1: 男性, 2: 女性, 0: 未知
  "occupation": "职业",
  "location": ["北京市", "朝阳区"],
  "phone": "13800138000",
  "education": "本科",
  "interests": ["兴趣1", "兴趣2", "兴趣3"]
}
```

---

## 📌 使用说明

### API 调用示例

```javascript
// 获取特定卡片信息
const response = await fetch('/api/users/me/cards/activity/activity_organizer');
const cardData = await response.json();

// 或者通过卡片ID获取
const response = await fetch('/api/users/{user_id}/cards/{scene_type}/{role_type}');
const cardData = await response.json();
```

### 字段说明

- **scene_type**: 场景类型，可选值：`housing`, `dating`, `activity`
- **role_type**: 角色类型，根据场景不同而变化
- **profile_data**: 具体角色的详细资料数据
- **preferences**: 用户的偏好设置
- **visibility**: 可见性，可选值：`public`, `private`, `friends`
- **is_active**: 激活状态，1 为激活，0 为未激活

### 注意事项

1. 所有图片 URL 都包含完整的服务器地址前缀
2. 时间字段使用 ISO 8601 格式
3. 位置信息以数组形式存储，便于前端展示
4. 空值字段可能返回 `null` 或空数组/对象
5. 所有数字类型的字段都可能为 0 或负数，前端需要做好空值处理

---

*最后更新时间：2024年1月*