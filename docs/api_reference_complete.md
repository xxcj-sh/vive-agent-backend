# VMatch API 完整参考文档

## API 路径总览

### 认证管理 (Authentication)
- `POST /auth/sessions` - 微信登录
- `POST /auth/sessions/phone` - 手机号登录  
- `POST /auth/sms-codes` - 发送验证码
- `GET /auth/sessions/current` - 验证会话
- `DELETE /auth/sessions/current` - 登出

### 用户管理 (Users)
- `GET /users/me` - 获取当前用户信息
- `PUT /users/me` - 更新当前用户信息
- `GET /users/{userId}` - 获取其他用户信息
- `GET /users/me/stats` - 获取用户统计
- `GET /users/me/profiles` - 获取用户所有角色资料
- `GET /users/me/profiles/{scene_type}` - 获取特定场景下的角色资料
- `GET /users/me/profiles/{scene_type}/{role_type}` - 获取特定角色的资料
- `POST /users/me/profiles` - 创建用户角色资料
- `PUT /users/me/profiles/{profile_id}` - 更新用户角色资料
- `DELETE /users/me/profiles/{profile_id}` - 删除用户角色资料
- `PATCH /users/me/profiles/{profile_id}/toggle` - 切换资料激活状态

### 匹配管理 (Matches)
- `GET /matches/cards` - 获取匹配卡片
- `POST /matches/actions` - 提交匹配操作
- `POST /matches/swipes` - 滑动卡片
- `GET /matches` - 获取匹配列表
- `GET /matches/{matchId}` - 获取匹配详情

### 消息管理 (Messages)
- `GET /messages` - 获取消息列表
- `POST /messages` - 发送消息
- `PUT /messages/read` - 标记已读

### 文件管理 (Files)
- `POST /files` - 上传文件

### 会员管理 (Memberships)
- `GET /memberships/me` - 获取会员信息
- `POST /memberships/orders` - 创建会员订单
- `GET /memberships/orders` - 查询会员订单列表
- `GET /memberships/orders/{order_id}` - 查询单个会员订单详情

### 7.3 查询会员订单列表
**GET** `/memberships/orders`

查询用户的会员订单列表

**查询参数:**
- `user_id` (string, required): 用户ID
- `status` (string, optional): 订单状态过滤 (pending, paid, cancelled, refunded)
- `page` (int, optional): 页码，默认1
- `page_size` (int, optional): 每页数量，默认10，最大100

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "orders": [
      {
        "id": "20230615001",
        "planName": "月度会员",
        "amount": 19.9,
        "date": "2023-06-15",
        "status": "paid",
        "statusText": "已支付"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

### 7.4 查询单个会员订单详情
**GET** `/memberships/orders/{order_id}`

查询单个会员订单详情

**路径参数:**
- `order_id` (string): 订单ID

**查询参数:**
- `user_id` (string, required): 用户ID

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": "20230615001",
    "planName": "月度会员",
    "amount": 19.9,
    "date": "2023-06-15",
    "status": "paid",
    "statusText": "已支付"
  }
}
```

### 房源管理 (Properties)
- `GET /properties/{propertyId}` - 获取房源详情

### 场景配置 (Scenes)
- `GET /scenes` - 获取所有场景配置
- `GET /scenes/{sceneKey}` - 获取指定场景配置
- `GET /scenes/{sceneKey}/roles` - 获取场景角色
- `GET /scenes/{sceneKey}/tags` - 获取场景标签

---

## 基本信息
- **Base URL**: `http://localhost:8000/api/v1`
- **API 版本**: 2.0.0
- **设计规范**: RESTful
- **认证方式**: JWT Token (生产环境) / X-Test-Mode Header (测试环境)

## 测试模式
在任何请求中添加以下头部即可启用测试模式，无需认证：
```http
X-Test-Mode: true
```

## 统一响应格式
```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## HTTP 状态码
- `200 OK` - 成功的 GET, PUT 请求
- `201 Created` - 成功的 POST 请求
- `204 No Content` - 成功的 DELETE 请求
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未授权访问
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `422 Unprocessable Entity` - 验证错误
- `500 Internal Server Error` - 服务器错误

---

## 1. 认证管理 (Authentication)

### 1.1 创建会话（登录）
**POST** `/auth/sessions`

微信小程序登录，创建用户会话。

**请求体：**
```json
{
  "code": "wx_login_code",
  "userInfo": {
    "nickName": "用户昵称",
    "avatarUrl": "头像URL",
    "gender": 1
  }
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "jwt_token_string",
    "expiresIn": 7200,
    "user": {
      "id": "user_001",
      "nickName": "用户昵称",
      "avatarUrl": "头像URL"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**测试示例：**
```bash
curl -X POST http://localhost:8000/api/v1/auth/sessions \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{"code": "test_wx_code"}'
```

### 1.2 手机号登录
**POST** `/auth/sessions/phone`

使用手机号和验证码登录。

**请求体：**
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

### 1.3 发送短信验证码
**POST** `/auth/sms-codes`

发送手机验证码。

**请求体：**
```json
{
  "phone": "13800138000"
}
```

### 1.4 验证当前会话
**GET** `/auth/sessions/current`

验证当前用户的登录状态。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": true,
    "user": {
      "id": "user_001",
      "nickName": "用户昵称"
    }
  }
}
```

### 1.5 登出
**DELETE** `/auth/sessions/current`

注销当前会话。

---

## 2. 用户管理 (Users)

### 2.1 获取当前用户信息
**GET** `/users/me`

获取当前登录用户的基本信息。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "user_001",
    "nickName": "用户昵称",
    "avatarUrl": "头像URL",
    "phone": "13800138000",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**测试示例：**
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "X-Test-Mode: true"
```

### 2.2 更新当前用户信息
**PUT** `/users/me`

更新当前用户的基本信息。

**请求体：**
```json
{
  "nickName": "新昵称",
  "avatarUrl": "新头像URL"
}
```

### 2.3 获取其他用户信息
**GET** `/users/{userId}`

根据用户ID获取其他用户的公开信息。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "user_002",
    "nickname": "其他用户",
    "avatar": "头像URL",
    "age": 25,
    "gender": "男",
    "location": ["北京", "朝阳区"],
    "occupation": "软件工程师",
    "bio": "个人简介"
  }
}
```

### 2.4 获取用户统计信息
**GET** `/users/me/stats`

获取当前用户的统计数据。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "matchCount": 10,
    "messageCount": 50,
    "favoriteCount": 5
  }
}
```

### 2.5 用户角色资料管理

用户角色资料系统允许同一用户在不同场景下拥有多个不同的角色资料。每个用户可以创建多个资料，用于不同的匹配场景（如找房、交友、活动等）。

#### 支持的场景和角色

**1. 找房场景 (housing)**
- `housing_seeker`: 找房者
- `housing_provider`: 房源提供者

**2. 交友场景 (dating)**
- `dating_seeker`: 交友者

**3. 活动场景 (activity)**
- `activity_organizer`: 活动组织者
- `activity_participant`: 活动参与者

#### 2.5.1 获取用户所有角色资料
**GET** `/users/me/profiles`

获取当前用户的所有角色资料，按场景分组显示。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)

**响应格式:**
```json
{
  "user_id": "string",
  "total_count": "integer",
  "active_count": "integer", 
  "by_scene": [
    {
      "scene_type": "string",
      "profiles": [UserProfile]
    }
  ],
  "all_profiles": [UserProfile],
  "user_basic_info": {UserBasicInfo}
}
```

**UserProfile 数据结构:**
```json
{
  "id": "string - 资料ID",
  "user_id": "string - 用户ID", 
  "role_type": "string - 角色类型",
  "scene_type": "string - 场景类型",
  "display_name": "string - 显示名称",
  "avatar_url": "string - 头像URL",
  "bio": "string - 个人简介",
  "profile_data": "object - 角色特定数据",
  "preferences": "object - 偏好设置",
  "tags": "array - 标签列表",
  "is_active": "integer - 激活状态(1-激活,0-停用)",
  "visibility": "string - 可见性(public/private)",
  "created_at": "datetime - 创建时间",
  "updated_at": "datetime - 更新时间"
}
```

**响应示例:**
```json
{
  "user_id": "test_user_001",
  "total_count": 3,
  "active_count": 2,
  "by_scene": [
    {
      "scene_type": "housing",
      "profiles": [
        {
          "id": "profile_housing_seeker_001",
          "user_id": "test_user_001",
          "role_type": "housing_seeker",
          "scene_type": "housing",
          "display_name": "小李找房",
          "avatar_url": "https://example.com/avatars/housing_seeker.jpg",
          "bio": "刚毕业的程序员，寻找合适的合租房源",
          "profile_data": {
            "budget_range": [2000, 3500],
            "preferred_areas": ["朝阳区", "海淀区"],
            "room_type": "single_room",
            "move_in_date": "2024-02-01",
            "lease_duration": "12_months",
            "lifestyle": "quiet",
            "work_schedule": "9_to_5",
            "pets": false,
            "smoking": false,
            "occupation": "软件工程师",
            "company_location": "中关村"
          },
          "preferences": {
            "roommate_gender": "any",
            "roommate_age_range": [22, 35],
            "shared_facilities": ["kitchen", "living_room"],
            "transportation": ["subway"],
            "nearby_facilities": ["supermarket", "gym"]
          },
          "tags": ["程序员", "安静", "整洁"],
          "is_active": 1,
          "visibility": "public",
          "created_at": "2025-01-29T01:00:00Z",
          "updated_at": "2025-01-29T01:00:00Z"
        }
      ]
    },
    {
      "scene_type": "activity", 
      "profiles": [
        {
          "id": "profile_activity_organizer_001",
          "user_id": "test_user_001",
          "role_type": "activity_organizer",
          "scene_type": "activity",
          "display_name": "活动达人小李",
          "avatar_url": "https://example.com/avatars/organizer.jpg",
          "bio": "热爱组织户外活动，让大家一起享受生活",
          "profile_data": {
            "activity_cover": "https://example.com/activity_cover.jpg",
            "activity_name": "周末户外徒步活动",
            "activity_types": ["户外运动", "社交聚会"],
            "activity_start_time": "2024-01-15T09:00:00Z",
            "activity_city": "北京",
            "activity_end_time": "2024-01-15T17:00:00Z",
            "activity_location": "香山公园",
            "activity_min_participants": 5,
            "activity_max_participants": 20,
            "activity_cost": "免费",
            "activity_description": "一起享受户外徒步的乐趣，结识新朋友",
            "organizing_experience": "3年活动组织经验",
            "specialties": ["户外运动", "团队建设"],
            "group_size_preference": "10-20人",
            "frequency": "每周一次",
            "locations": ["香山", "奥森公园", "颐和园"],
            "past_activities": [
              {
                "name": "春季踏青活动",
                "date": "2024-03-20",
                "participants": 15
              }
            ],
            "contact_info": {
              "wechat": "organizer_li",
              "phone": "13800138000"
            }
          },
          "preferences": {
            "participant_requirements": {
              "age_range": [18, 45],
              "fitness_level": "basic"
            },
            "activity_types": ["户外", "运动", "社交"],
            "weather_dependency": "flexible"
          },
          "tags": ["户外", "社交", "健康", "领导力"],
          "is_active": 1,
          "visibility": "public",
          "created_at": "2025-01-29T02:00:00Z",
          "updated_at": "2025-01-29T02:00:00Z"
        }
      ]
    }
  ],
  "all_profiles": [...],
  "user_basic_info": {
    "id": "test_user_001",
    "nick_name": "小李",
    "avatar_url": "https://example.com/avatar.jpg",
    "age": 25,
    "gender": 1,
    "occupation": "软件工程师",
    "location": ["北京", "朝阳区"],
    "phone": "13800138000"
  }
}
```

**测试示例:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me/profiles \
  -H "X-Test-Mode: true"
```

#### 2.5.2 获取特定场景下的角色资料
**GET** `/users/me/profiles/{scene_type}`

获取当前用户在指定场景下的所有角色资料。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)

**路径参数:**
- `scene_type` (string, required): 场景类型
  - `housing` - 找房场景
  - `dating` - 交友场景  
  - `activity` - 活动场景

**响应格式:**
```json
{
  "code": 0,
  "message": "success", 
  "data": {
    "scene_type": "string",
    "profiles": [UserProfile]
  }
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scene_type": "housing",
    "profiles": [
      {
        "id": "profile_housing_seeker_001",
        "user_id": "test_user_001",
        "role_type": "housing_seeker",
        "scene_type": "housing",
        "display_name": "小李找房",
        "avatar_url": "https://example.com/avatars/housing_seeker.jpg",
        "bio": "刚毕业的程序员，寻找合适的合租房源",
        "profile_data": {
          "budget_range": [2000, 3500],
          "preferred_areas": ["朝阳区", "海淀区"],
          "room_type": "single_room",
          "move_in_date": "2024-02-01",
          "lease_duration": "12_months",
          "lifestyle": "quiet",
          "work_schedule": "9_to_5",
          "pets": false,
          "smoking": false,
          "occupation": "软件工程师",
          "company_location": "中关村"
        },
        "preferences": {
          "roommate_gender": "any",
          "roommate_age_range": [22, 35],
          "shared_facilities": ["kitchen", "living_room"],
          "transportation": ["subway"],
          "nearby_facilities": ["supermarket", "gym"]
        },
        "tags": ["程序员", "安静", "整洁"],
        "is_active": 1,
        "visibility": "public",
        "created_at": "2025-01-29T01:00:00Z",
        "updated_at": "2025-01-29T01:00:00Z"
      },
      {
        "id": "profile_housing_provider_001", 
        "user_id": "test_user_001",
        "role_type": "housing_provider",
        "scene_type": "housing",
        "display_name": "房东小李",
        "avatar_url": "https://example.com/avatars/provider.jpg",
        "bio": "有多套优质房源出租",
        "profile_data": {
          "properties": [
            {
              "id": "property_001",
              "title": "精装两居室",
              "rent": 4500,
              "area": 80,
              "location": "朝阳区三里屯",
              "images": ["https://example.com/room1.jpg"]
            }
          ],
          "landlord_type": "individual",
          "response_time": "within_24_hours",
          "viewing_available": true,
          "lease_terms": ["押一付三", "包物业费"]
        },
        "preferences": {
          "tenant_requirements": {
            "stable_income": true,
            "no_pets": false,
            "no_smoking": true,
            "quiet_lifestyle": true
          },
          "payment_methods": ["bank_transfer", "alipay"]
        },
        "tags": ["靠谱房东", "响应快", "房源优质"],
        "is_active": 1,
        "visibility": "public",
        "created_at": "2025-01-29T01:30:00Z",
        "updated_at": "2025-01-29T01:30:00Z"
      }
    ]
  }
}
```

**错误响应:**
- `401 Unauthorized`: 用户未认证
- `404 Not Found`: 指定场景下没有找到资料

**测试示例:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me/profiles/housing \
  -H "X-Test-Mode: true"
```

#### 2.5.3 获取特定角色的资料
**GET** `/users/me/profiles/{scene_type}/{role_type}`

获取当前用户在指定场景和角色下的详细资料，包含用户基础信息。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)

**路径参数:**
- `scene_type` (string, required): 场景类型
  - `housing` - 找房场景
  - `dating` - 交友场景
  - `activity` - 活动场景
- `role_type` (string, required): 角色类型
  - 找房场景: `housing_seeker`, `housing_provider`
  - 交友场景: `dating_seeker`
  - 活动场景: `activity_organizer`, `activity_participant`

**响应格式:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "string - 资料ID",
    "user_id": "string - 用户ID",
    "role_type": "string - 角色类型", 
    "scene_type": "string - 场景类型",
    "display_name": "string - 显示名称",
    "avatar_url": "string - 头像URL",
    "bio": "string - 个人简介",
    "profile_data": "object - 角色特定数据",
    "preferences": "object - 偏好设置",
    "tags": "array - 标签列表",
    "is_active": "integer - 激活状态",
    "visibility": "string - 可见性",
    "created_at": "datetime - 创建时间",
    "updated_at": "datetime - 更新时间",
    "username": "string - 用户名",
    "email": "string - 邮箱",
    "nick_name": "string - 昵称",
    "age": "integer - 年龄",
    "gender": "integer - 性别",
    "occupation": "string - 职业",
    "location": "array - 位置信息",
    "phone": "string - 手机号",
    "education": "string - 教育程度",
    "interests": "array - 兴趣爱好"
  }
}
```

**找房者资料响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_001",
    "user_id": "test_user_001",
    "role_type": "housing_seeker",
    "scene_type": "housing",
    "display_name": "小李找房",
    "avatar_url": "https://example.com/avatars/housing_seeker.jpg",
    "bio": "刚毕业的程序员，寻找合适的合租房源",
    "profile_data": {
      "budget_range": [2000, 3500],
      "preferred_areas": ["朝阳区", "海淀区"],
      "room_type": "single_room",
      "move_in_date": "2024-02-01",
      "lease_duration": "12_months",
      "lifestyle": "quiet",
      "work_schedule": "9_to_5",
      "pets": false,
      "smoking": false,
      "occupation": "软件工程师",
      "company_location": "中关村"
    },
    "preferences": {
      "roommate_gender": "any",
      "roommate_age_range": [22, 35],
      "shared_facilities": ["kitchen", "living_room"],
      "transportation": ["subway"],
      "nearby_facilities": ["supermarket", "gym"]
    },
    "tags": ["程序员", "安静", "整洁"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T01:00:00Z",
    "updated_at": "2025-01-29T01:00:00Z",
    "username": "test_user_001",
    "email": "test@example.com",
    "nick_name": "小李",
    "age": 25,
    "gender": 1,
    "occupation": "软件工程师",
    "location": ["北京", "朝阳区"],
    "phone": "13800138000",
    "education": "本科",
    "interests": ["编程", "音乐", "旅行"]
  }
}
```

**活动组织者资料响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_activity_organizer_001",
    "user_id": "test_user_001",
    "role_type": "activity_organizer",
    "scene_type": "activity",
    "display_name": "活动达人小李",
    "avatar_url": "https://example.com/avatars/organizer.jpg",
    "bio": "热爱组织户外活动，让大家一起享受生活",
    "profile_data": {
      "activity_cover": "https://example.com/activity_cover.jpg",
      "activity_name": "周末户外徒步活动",
      "activity_types": ["户外运动", "社交聚会"],
      "activity_start_time": "2024-01-15T09:00:00Z",
      "activity_city": "北京",
      "activity_end_time": "2024-01-15T17:00:00Z",
      "activity_location": "香山公园",
      "activity_min_participants": 5,
      "activity_max_participants": 20,
      "activity_cost": "免费",
      "activity_description": "一起享受户外徒步的乐趣，结识新朋友",
      "organizing_experience": "3年活动组织经验",
      "specialties": ["户外运动", "团队建设"],
      "group_size_preference": "10-20人",
      "frequency": "每周一次",
      "locations": ["香山", "奥森公园", "颐和园"],
      "past_activities": [
        {
          "name": "春季踏青活动",
          "date": "2024-03-20",
          "participants": 15
        }
      ],
      "contact_info": {
        "wechat": "organizer_li",
        "phone": "13800138000"
      }
    },
    "preferences": {
      "participant_requirements": {
        "age_range": [18, 45],
        "fitness_level": "basic"
      },
      "activity_types": ["户外", "运动", "社交"],
      "weather_dependency": "flexible"
    },
    "tags": ["户外", "社交", "健康", "领导力"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T02:00:00Z",
    "updated_at": "2025-01-29T02:00:00Z",
    "username": "test_user_001",
    "email": "test@example.com",
    "nick_name": "小李",
    "age": 25,
    "gender": 1,
    "occupation": "软件工程师",
    "location": ["北京", "朝阳区"],
    "phone": "13800138000",
    "education": "本科",
    "interests": ["编程", "音乐", "旅行", "户外运动"]
  }
}
```

**错误响应:**
- `401 Unauthorized`: 用户未认证
- `404 Not Found`: 指定的角色资料不存在或未激活

**测试示例:**
```bash
# 获取找房者资料
curl -X GET http://localhost:8000/api/v1/users/me/profiles/housing/housing_seeker \
  -H "X-Test-Mode: true"

# 获取活动组织者资料  
curl -X GET http://localhost:8000/api/v1/users/me/profiles/activity/activity_organizer \
  -H "X-Test-Mode: true"
```

#### 2.5.4 创建用户角色资料
**POST** `/users/me/profiles`

为当前用户创建新的角色资料。每个用户在同一场景和角色组合下只能有一个资料。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)
- `Content-Type: application/json`

**请求体参数:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| role_type | string | 是 | 角色类型 |
| scene_type | string | 是 | 场景类型 |
| display_name | string | 是 | 显示名称 |
| avatar_url | string | 否 | 头像URL |
| bio | string | 否 | 个人简介 |
| profile_data | object | 否 | 角色特定数据 |
| preferences | object | 否 | 偏好设置 |
| tags | array | 否 | 标签列表 |
| visibility | string | 否 | 可见性，默认"public" |

**角色类型说明:**
- **找房场景 (housing):**
  - `housing_seeker`: 找房者
  - `housing_provider`: 房源提供者
- **交友场景 (dating):**
  - `dating_seeker`: 交友者
- **活动场景 (activity):**
  - `activity_organizer`: 活动组织者
  - `activity_participant`: 活动参与者

**找房者资料请求示例:**
```json
{
  "role_type": "housing_seeker",
  "scene_type": "housing",
  "display_name": "小李找房",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "刚毕业的程序员，寻找合适的合租房源",
  "profile_data": {
    "budget_range": [2000, 3500],
    "preferred_areas": ["朝阳区", "海淀区"],
    "room_type": "single_room",
    "move_in_date": "2024-02-01",
    "lease_duration": "12_months",
    "lifestyle": "quiet",
    "work_schedule": "9_to_5",
    "pets": false,
    "smoking": false,
    "occupation": "软件工程师",
    "company_location": "中关村"
  },
  "preferences": {
    "roommate_gender": "any",
    "roommate_age_range": [22, 35],
    "shared_facilities": ["kitchen", "living_room"],
    "transportation": ["subway"],
    "nearby_facilities": ["supermarket", "gym"]
  },
  "tags": ["程序员", "安静", "整洁"],
  "visibility": "public"
}
```

**房源提供者资料请求示例:**
```json
{
  "role_type": "housing_provider",
  "scene_type": "housing",
  "display_name": "房东小王",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "有多套优质房源出租，诚信经营",
  "profile_data": {
    "properties": [
      {
        "id": "property_001",
        "title": "精装两居室",
        "rent": 4500,
        "area": 80,
        "location": "朝阳区三里屯",
        "images": ["https://example.com/room1.jpg"]
      }
    ],
    "landlord_type": "individual",
    "response_time": "within_24_hours",
    "viewing_available": true,
    "lease_terms": ["押一付三", "包物业费"]
  },
  "preferences": {
    "tenant_requirements": {
      "stable_income": true,
      "no_pets": false,
      "no_smoking": true,
      "quiet_lifestyle": true
    },
    "payment_methods": ["bank_transfer", "alipay"]
  },
  "tags": ["靠谱房东", "响应快", "房源优质"],
  "visibility": "public"
}
```

**活动组织者资料请求示例:**
```json
{
  "role_type": "activity_organizer",
  "scene_type": "activity",
  "display_name": "活动达人小王",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "热爱组织各种有趣的活动，让大家一起享受生活",
  "profile_data": {
    "activity_cover": "https://example.com/activity_cover.jpg",
    "activity_name": "周末户外徒步活动",
    "activity_types": ["户外运动", "社交聚会"],
    "activity_start_time": "2024-01-15T09:00:00Z",
    "activity_city": "北京",
    "activity_end_time": "2024-01-15T17:00:00Z",
    "activity_location": "香山公园",
    "activity_min_participants": 5,
    "activity_max_participants": 20,
    "activity_cost": "免费",
    "activity_description": "一起享受户外徒步的乐趣，结识新朋友",
    "organizing_experience": "3年活动组织经验",
    "specialties": ["户外运动", "团队建设"],
    "group_size_preference": "10-20人",
    "frequency": "每周一次",
    "locations": ["香山", "奥森公园", "颐和园"],
    "past_activities": [
      {
        "name": "春季踏青活动",
        "date": "2024-03-20",
        "participants": 15
      }
    ],
    "contact_info": {
      "wechat": "organizer_wang",
      "phone": "13800138000"
    }
  },
  "preferences": {
    "participant_requirements": {
      "age_range": [18, 45],
      "fitness_level": "basic"
    },
    "activity_types": ["户外", "运动", "社交"],
    "weather_dependency": "flexible"
  },
  "tags": ["户外", "社交", "健康", "领导力"],
  "visibility": "public"
}
```

**交友者资料请求示例:**
```json
{
  "role_type": "dating_seeker",
  "scene_type": "dating",
  "display_name": "阳光小李",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "热爱生活，寻找志同道合的伴侣",
  "profile_data": {
    "age": 25,
    "height": 175,
    "education": "本科",
    "occupation": "软件工程师",
    "income_range": "10k-20k",
    "relationship_status": "single",
    "looking_for": "serious_relationship",
    "hobbies": ["音乐", "旅行", "摄影", "健身"],
    "personality": ["开朗", "幽默", "责任心强"],
    "lifestyle": {
      "smoking": false,
      "drinking": "occasionally",
      "exercise": "regularly",
      "diet": "balanced"
    }
  },
  "preferences": {
    "age_range": [22, 30],
    "height_range": [160, 180],
    "education_level": ["本科", "硕士"],
    "personality_preferences": ["温柔", "善良", "有趣"],
    "lifestyle_preferences": {
      "smoking": false,
      "drinking": "any",
      "exercise": "preferred"
    },
    "relationship_goals": "long_term"
  },
  "tags": ["阳光", "上进", "有趣", "靠谱"],
  "visibility": "public"
}
```

**成功响应示例:**
```json
{
  "id": "profile_housing_seeker_002",
  "user_id": "current_user_id",
  "role_type": "housing_seeker",
  "scene_type": "housing",
  "display_name": "小李找房",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "刚毕业的程序员，寻找合适的合租房源",
  "profile_data": {
    "budget_range": [2000, 3500],
    "preferred_areas": ["朝阳区", "海淀区"]
  },
  "preferences": {
    "roommate_gender": "any",
    "roommate_age_range": [22, 35]
  },
  "tags": ["程序员", "安静", "整洁"],
  "is_active": 1,
  "visibility": "public",
  "created_at": "2025-01-29T01:00:00Z",
  "updated_at": "2025-01-29T01:00:00Z"
}
```

**错误响应:**
- `400 Bad Request`: 该场景和角色的资料已存在
- `401 Unauthorized`: 用户未认证
- `422 Unprocessable Entity`: 请求参数验证失败

**测试示例:**
```bash
# 创建找房者资料
curl -X POST http://localhost:8000/api/v1/users/me/profiles \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{
    "role_type": "housing_seeker",
    "scene_type": "housing", 
    "display_name": "小李找房",
    "bio": "寻找合适的合租房源",
    "profile_data": {
      "budget_range": [2000, 3500],
      "preferred_areas": ["朝阳区"]
    },
    "tags": ["程序员", "安静"]
  }'

# 创建活动组织者资料
curl -X POST http://localhost:8000/api/v1/users/me/profiles \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{
    "role_type": "activity_organizer",
    "scene_type": "activity",
    "display_name": "活动达人小王",
    "bio": "热爱组织户外活动",
    "profile_data": {
      "activity_cover": "https://example.com/cover.jpg",
      "activity_name": "周末徒步活动"
    },
    "tags": ["户外", "社交"]
  }'
```

#### 2.5.5 更新用户角色资料
**PUT** `/users/me/profiles/{profile_id}`

更新指定的用户角色资料。只有资料的所有者才能更新。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)
- `Content-Type: application/json`

**路径参数:**
- `profile_id` (string, required): 资料ID

**请求体参数:** (所有字段都是可选的)
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| display_name | string | 否 | 显示名称 |
| avatar_url | string | 否 | 头像URL |
| bio | string | 否 | 个人简介 |
| profile_data | object | 否 | 角色特定数据 |
| preferences | object | 否 | 偏好设置 |
| tags | array | 否 | 标签列表 |
| visibility | string | 否 | 可见性(public/private) |
| is_active | integer | 否 | 激活状态(1-激活,0-停用) |

**请求体示例:**
```json
{
  "display_name": "更新后的名称",
  "bio": "更新后的个人简介",
  "profile_data": {
    "budget_range": [3000, 4500],
    "preferred_areas": ["朝阳区", "海淀区", "西城区"],
    "room_type": "single_room",
    "move_in_date": "2024-03-01"
  },
  "preferences": {
    "roommate_gender": "female",
    "roommate_age_range": [25, 35],
    "shared_facilities": ["kitchen", "living_room", "balcony"]
  },
  "tags": ["程序员", "安静", "整洁", "爱干净"],
  "visibility": "public"
}
```

**部分更新示例:**
```json
{
  "display_name": "小李找房(急)",
  "profile_data": {
    "budget_range": [2500, 4000],
    "move_in_date": "2024-02-15"
  },
  "tags": ["程序员", "安静", "整洁", "急租"]
}
```

**成功响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_001",
    "user_id": "test_user_001",
    "role_type": "housing_seeker",
    "scene_type": "housing",
    "display_name": "更新后的名称",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "更新后的个人简介",
    "profile_data": {
      "budget_range": [3000, 4500],
      "preferred_areas": ["朝阳区", "海淀区", "西城区"],
      "room_type": "single_room",
      "move_in_date": "2024-03-01",
      "lease_duration": "12_months",
      "lifestyle": "quiet",
      "work_schedule": "9_to_5",
      "pets": false,
      "smoking": false,
      "occupation": "软件工程师",
      "company_location": "中关村"
    },
    "preferences": {
      "roommate_gender": "female",
      "roommate_age_range": [25, 35],
      "shared_facilities": ["kitchen", "living_room", "balcony"],
      "transportation": ["subway"],
      "nearby_facilities": ["supermarket", "gym"]
    },
    "tags": ["程序员", "安静", "整洁", "爱干净"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T01:00:00Z",
    "updated_at": "2025-01-29T02:00:00Z"
  }
}
```

**错误响应:**
- `401 Unauthorized`: 用户未认证
- `404 Not Found`: 资料不存在或不属于当前用户
- `422 Unprocessable Entity`: 请求参数验证失败

**测试示例:**
```bash
# 更新找房者资料
curl -X PUT http://localhost:8000/api/v1/users/me/profiles/profile_housing_seeker_001 \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{
    "display_name": "小李找房(急)",
    "bio": "急需找房，预算可适当调整",
    "profile_data": {
      "budget_range": [2500, 4000],
      "move_in_date": "2024-02-15"
    },
    "tags": ["程序员", "安静", "整洁", "急租"]
  }'

# 只更新部分字段
curl -X PUT http://localhost:8000/api/v1/users/me/profiles/profile_activity_organizer_001 \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{
    "display_name": "户外活动专家小王",
    "tags": ["户外", "专业", "安全", "有趣"]
  }'
```

#### 2.5.6 删除用户角色资料
**DELETE** `/users/me/profiles/{profile_id}`

永久删除指定的用户角色资料。只有资料的所有者才能删除。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)

**路径参数:**
- `profile_id` (string, required): 资料ID

**成功响应示例:**
```json
{
  "code": 0,
  "message": "Profile deleted successfully",
  "data": {
    "deleted_profile_id": "profile_housing_seeker_001"
  }
}
```

**错误响应:**
- `401 Unauthorized`: 用户未认证
- `404 Not Found`: 资料不存在或不属于当前用户

**测试示例:**
```bash
curl -X DELETE http://localhost:8000/api/v1/users/me/profiles/profile_housing_seeker_001 \
  -H "X-Test-Mode: true"
```

#### 2.5.7 切换资料激活状态
**PATCH** `/users/me/profiles/{profile_id}/toggle`

切换指定用户角色资料的激活状态。停用的资料不会在匹配中显示。

**请求头:**
- `Authorization: Bearer {token}` (生产环境)
- `X-Test-Mode: true` (测试环境)

**路径参数:**
- `profile_id` (string, required): 资料ID

**查询参数:**
- `is_active` (integer, required): 激活状态
  - `1` - 激活资料
  - `0` - 停用资料

**成功响应示例:**
```json
{
  "code": 0,
  "message": "Profile status updated successfully",
  "data": {
    "id": "profile_housing_seeker_001",
    "user_id": "test_user_001",
    "role_type": "housing_seeker",
    "scene_type": "housing",
    "display_name": "小李找房",
    "is_active": 1,
    "updated_at": "2025-01-29T02:00:00Z"
  }
}
```

**错误响应:**
- `401 Unauthorized`: 用户未认证
- `404 Not Found`: 资料不存在或不属于当前用户
- `422 Unprocessable Entity`: is_active参数无效

**测试示例:**
```bash
# 激活资料
curl -X PATCH "http://localhost:8000/api/v1/users/me/profiles/profile_housing_seeker_001/toggle?is_active=1" \
  -H "X-Test-Mode: true"

# 停用资料
curl -X PATCH "http://localhost:8000/api/v1/users/me/profiles/profile_housing_seeker_001/toggle?is_active=0" \
  -H "X-Test-Mode: true"
```

#### 2.5.8 获取其他用户的角色资料
**GET** `/users/{user_id}/profiles/{scene_type}/{role_type}`

获取指定用户在特定场景和角色下的公开资料信息。

**路径参数:**
- `user_id` (string, required): 用户ID或资料ID
- `scene_type` (string, required): 场景类型
- `role_type` (string, required): 角色类型

**成功响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_001",
    "user_id": "other_user_001",
    "role_type": "housing_seeker",
    "scene_type": "housing",
    "display_name": "小张找房",
    "avatar_url": "https://example.com/avatars/other_user.jpg",
    "bio": "在北京工作的设计师，寻找合租室友",
    "profile_data": {
      "budget_range": [3000, 4500],
      "preferred_areas": ["朝阳区", "东城区"],
      "room_type": "single_room",
      "occupation": "UI设计师"
    },
    "preferences": {
      "roommate_gender": "any",
      "shared_facilities": ["kitchen", "living_room"]
    },
    "tags": ["设计师", "爱干净", "好相处"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T01:00:00Z",
    "updated_at": "2025-01-29T01:00:00Z"
  }
}
```

**错误响应:**
- `404 Not Found`: 用户或资料不存在，或资料不公开

**测试示例:**
```bash
curl -X GET http://localhost:8000/api/v1/users/other_user_001/profiles/housing/housing_seeker \
  -H "X-Test-Mode: true"
```

### 2.6 角色资料数据结构说明

#### 找房者 (housing_seeker) 数据结构

**profile_data 字段:**
```json
{
  "budget_range": [2000, 3500],           // 预算范围 [最低, 最高]
  "preferred_areas": ["朝阳区", "海淀区"],  // 偏好区域列表
  "room_type": "single_room",             // 房间类型: single_room, shared_room, entire_apartment
  "move_in_date": "2024-02-01",          // 期望入住日期
  "lease_duration": "12_months",          // 租期: 3_months, 6_months, 12_months, flexible
  "lifestyle": "quiet",                   // 生活方式: quiet, social, flexible
  "work_schedule": "9_to_5",             // 工作时间: 9_to_5, flexible, night_shift
  "pets": false,                         // 是否有宠物
  "smoking": false,                      // 是否吸烟
  "occupation": "软件工程师",              // 职业
  "company_location": "中关村"            // 公司位置
}
```

**preferences 字段:**
```json
{
  "roommate_gender": "any",                    // 室友性别偏好: male, female, any
  "roommate_age_range": [22, 35],             // 室友年龄范围
  "shared_facilities": ["kitchen", "living_room"], // 共享设施
  "transportation": ["subway"],                // 交通方式偏好
  "nearby_facilities": ["supermarket", "gym"] // 附近设施需求
}
```

#### 房源提供者 (housing_provider) 数据结构

**profile_data 字段:**
```json
{
  "properties": [                        // 房源列表
    {
      "id": "property_001",
      "title": "精装两居室",
      "rent": 4500,
      "area": 80,
      "location": "朝阳区三里屯",
      "images": ["https://example.com/room1.jpg"]
    }
  ],
  "landlord_type": "individual",         // 房东类型: individual, agency
  "response_time": "within_24_hours",    // 响应时间: within_1_hour, within_24_hours, flexible
  "viewing_available": true,             // 是否可看房
  "lease_terms": ["押一付三", "包物业费"]  // 租赁条款
}
```

#### 活动组织者 (activity_organizer) 数据结构

**profile_data 字段:**
```json
{
  "activity_cover": "https://example.com/cover.jpg",    // 活动封面 (必填)
  "activity_name": "周末户外徒步活动",                    // 活动名称 (必填)
  "activity_types": ["户外运动", "社交聚会"],            // 活动类型列表
  "activity_start_time": "2024-01-15T09:00:00Z",      // 活动开始时间
  "activity_city": "北京",                             // 活动城市
  "activity_end_time": "2024-01-15T17:00:00Z",        // 活动结束时间
  "activity_location": "香山公园",                      // 活动地点
  "activity_min_participants": 5,                     // 最少参与人数
  "activity_max_participants": 20,                    // 最多参与人数
  "activity_cost": "免费",                             // 活动费用
  "activity_description": "一起享受户外徒步的乐趣",      // 活动描述
  "organizing_experience": "3年活动组织经验",           // 组织经验
  "specialties": ["户外运动", "团队建设"],              // 专长领域
  "group_size_preference": "10-20人",                 // 偏好群体大小
  "frequency": "每周一次",                             // 活动频率
  "locations": ["香山", "奥森公园"],                    // 常用地点
  "past_activities": [                                // 过往活动
    {
      "name": "春季踏青活动",
      "date": "2024-03-20",
      "participants": 15
    }
  ],
  "contact_info": {                                   // 联系方式
    "wechat": "organizer_wang",
    "phone": "13800138000"
  }
}
```

#### 交友者 (dating_seeker) 数据结构

**profile_data 字段:**
```json
{
  "age": 25,                                    // 年龄
  "height": 175,                               // 身高(cm)
  "education": "本科",                          // 教育程度
  "occupation": "软件工程师",                    // 职业
  "income_range": "10k-20k",                   // 收入范围
  "relationship_status": "single",             // 感情状态
  "looking_for": "serious_relationship",       // 寻找类型
  "hobbies": ["音乐", "旅行", "摄影"],          // 兴趣爱好
  "personality": ["开朗", "幽默", "责任心强"],   // 性格特点
  "lifestyle": {                               // 生活方式
    "smoking": false,
    "drinking": "occasionally",
    "exercise": "regularly",
    "diet": "balanced"
  }
}
```

---

## 3. 个人资料 (Profiles)

### 3.1 获取个人资料
**GET** `/profiles/me`

获取当前用户的详细个人资料。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "user_001",
    "nickName": "用户昵称",
    "avatarUrl": "头像URL",
    "age": 25,
    "occupation": "软件工程师",
    "location": ["北京", "朝阳区"],
    "bio": "个人简介",
    "interests": ["音乐", "旅行", "摄影"],
    "preferences": {
      "ageRange": [20, 30],
      "location": "北京"
    }
  }
}
```

### 3.2 更新个人资料
**PUT** `/profiles/me`

更新当前用户的个人资料。

**请求体：**
```json
{
  "age": 26,
  "occupation": "高级软件工程师",
  "bio": "更新的个人简介",
  "interests": ["音乐", "旅行", "摄影", "编程"]
}
```

**测试示例：**
```bash
curl -X PUT http://localhost:8000/api/v1/profiles/me \
  -H "Content-Type: application/json" \
  -H "X-Test-Mode: true" \
  -d '{"age": 26, "bio": "更新的简介"}'
```

---

## 4. 匹配管理 (Matches)

### 4.1 获取匹配卡片
**GET** `/matches/cards`

获取可供滑动的匹配卡片。

**查询参数：**
- `matchType` (必需): 匹配类型 (housing/activity/dating)
- `userRole` (必需): 用户角色 (seeker/provider)
- `page` (可选): 页码，默认 1
- `pageSize` (可选): 每页数量，默认 10

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "cards": [
      {
        "id": "card_001",
        "type": "housing",
        "title": "精装两居室",
        "images": ["image1.jpg"],
        "price": 3000,
        "location": "朝阳区"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 10,
      "total": 100,
      "hasMore": true
    }
  }
}
```

**测试示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/matches/cards?matchType=housing&userRole=seeker" \
  -H "X-Test-Mode: true"
```

### 4.2 提交匹配操作
**POST** `/matches/actions`

对卡片执行匹配操作（喜欢/不喜欢/超级喜欢）。

**请求体：**
```json
{
  "cardId": "card_001",
  "action": "like",
  "matchType": "housing"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "isMatch": true,
    "matchId": "match_001"
  }
}
```

### 4.3 滑动卡片
**POST** `/matches/swipes`

通过滑动方向执行匹配操作。

**请求体：**
```json
{
  "cardId": "card_001",
  "direction": "right"
}
```

### 4.4 获取匹配列表
**GET** `/matches`

获取用户的匹配列表。

**查询参数：**
- `status` (可选): 状态筛选 (all/new/contacted)
- `page` (可选): 页码
- `pageSize` (可选): 每页数量

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "matches": [
      {
        "id": "match_001",
        "user": {
          "id": "user_002",
          "name": "匹配用户",
          "avatar": "头像URL"
        },
        "lastMessage": {
          "content": "最后一条消息",
          "timestamp": "2024-01-01T10:00:00Z"
        },
        "unreadCount": 2
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 10,
      "total": 20
    }
  }
}
```

### 4.5 获取匹配详情
**GET** `/matches/{matchId}`

获取特定匹配的详细信息。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "match_001",
    "user": {
      "id": "user_002",
      "name": "匹配用户",
      "avatar": "头像URL",
      "age": 25,
      "location": "北京",
      "occupation": "设计师"
    },
    "matchedAt": "2024-01-01T00:00:00Z",
    "reason": "你们都喜欢旅行"
  }
}
```

---

## 5. 消息管理 (Messages)

### 5.1 获取消息列表
**GET** `/messages`

获取指定匹配的聊天消息。

**查询参数：**
- `matchId` (必需): 匹配ID
- `page` (可选): 页码，默认 1
- `limit` (可选): 每页数量，默认 20

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "messages": [
      {
        "id": "msg_001",
        "senderId": "user_002",
        "content": "你好！",
        "type": "text",
        "timestamp": "2024-01-01T10:00:00Z",
        "isRead": true
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100
    }
  }
}
```

**测试示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/messages?matchId=match_001" \
  -H "X-Test-Mode: true"
```

### 5.2 发送消息
**POST** `/messages`

发送新消息。

**请求体：**
```json
{
  "matchId": "match_001",
  "content": "你好，很高兴认识你！",
  "type": "text"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "msg_002",
    "timestamp": "2024-01-01T10:01:00Z"
  }
}
```

### 5.3 标记消息已读
**PUT** `/messages/read`

标记指定匹配的消息为已读。

**请求体：**
```json
{
  "matchId": "match_001"
}
```

---

## 6. 文件管理 (Files)

### 6.1 上传文件
**POST** `/files`

上传图片或其他文件。

**请求格式：** `multipart/form-data`

**表单字段：**
- `file`: 文件内容
- `type`: 文件类型 (avatar/photo/document)

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "url": "https://cdn.example.com/files/file_id.jpg",
    "filename": "original_name.jpg",
    "size": 1024000,
    "type": "image/jpeg"
  }
}
```

**测试示例：**
```bash
curl -X POST http://localhost:8000/api/v1/files \
  -H "X-Test-Mode: true" \
  -F "file=@test.jpg" \
  -F "type=avatar"
```

---

## 7. 会员管理 (Memberships)

### 7.1 获取会员信息
**GET** `/memberships/me`

获取当前用户的会员状态。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "level": "premium",
    "levelName": "高级会员",
    "expireDate": "2024-12-31T23:59:59Z",
    "features": ["无限滑动", "超级喜欢", "查看喜欢我的人"],
    "remainingSwipes": -1,
    "totalSwipes": -1
  }
}
```

### 7.2 创建会员订单
**POST** `/memberships/orders`

创建会员购买订单。

**请求参数：**
- 需要认证
- Content-Type: `application/json`

**请求体参数：**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| planId | string | 是 | 会员套餐ID，用于标识要购买的会员计划 |

**请求体示例：**
```json
{
  "planId": "premium_monthly"
}
```

**可能的错误：**
- `422 Unprocessable Entity`: 请求参数验证失败
  - 缺少必填字段 `planId`
  - `planId` 字段类型不正确（必须为字符串）
  - `planId` 字段为空或null

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "orderId": "order_123456",
    "amount": 30.00,
    "status": "pending",
    "paymentUrl": "https://pay.example.com/order_123456",
    "wxPayParams": {
      "timeStamp": "1640995200",
      "nonceStr": "abcd1234efgh5678ijkl9012mnop3456",
      "package": "prepay_id=wx20211231123456789012",
      "signType": "MD5",
      "paySign": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
    }
  }
}
```

**微信小程序调用示例：**
```javascript
// 获取支付参数后调用微信支付
wx.requestPayment({
  timeStamp: response.data.wxPayParams.timeStamp,
  nonceStr: response.data.wxPayParams.nonceStr,
  package: response.data.wxPayParams.package,
  signType: response.data.wxPayParams.signType,
  paySign: response.data.wxPayParams.paySign,
  success: function(res) {
    console.log('支付成功', res);
  },
  fail: function(res) {
    console.log('支付失败', res);
  }
});
```

---

## 8. 房源管理 (Properties)

### 8.1 获取房源详情
**GET** `/properties/{propertyId}`

获取房源或卡片的详细信息。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "property_001",
    "type": "housing",
    "title": "精装两居室",
    "description": "房源描述",
    "price": 3000,
    "location": "朝阳区",
    "area": 80,
    "rooms": 2,
    "floor": "10/20",
    "orientation": "南北通透",
    "decoration": "精装修",
    "images": ["image1.jpg", "image2.jpg"],
    "landlord": {
      "name": "房东姓名",
      "avatar": "头像URL",
      "phone": "13800138000"
    },
    "facilities": ["空调", "洗衣机", "冰箱"],
    "tags": ["近地铁", "拎包入住"],
    "publishTime": "2024-01-01T00:00:00Z"
  }
}
```

---

## 9. 场景配置 (Scenes)

### 9.1 获取所有场景配置
**GET** `/scenes`

获取所有可用场景的配置信息。

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scenes": {
      "housing": {
        "key": "housing",
        "label": "住房",
        "icon": "/images/house.svg",
        "description": "寻找室友或出租房源",
        "roles": {
          "seeker": {
            "key": "seeker",
            "label": "租客",
            "description": "寻找房源的租客"
          },
          "provider": {
            "key": "provider",
            "label": "房东",
            "description": "出租房源的房东"
          }
        },
        "profileFields": ["budget", "location", "houseType"],
        "tags": ["近地铁", "拎包入住", "押一付一"]
      }
    }
  }
}
```

### 9.2 获取指定场景配置
**GET** `/scenes/{sceneKey}`

获取特定场景的配置信息。

### 9.3 获取场景角色
**GET** `/scenes/{sceneKey}/roles`

获取指定场景的角色配置。

### 9.4 获取场景标签
**GET** `/scenes/{sceneKey}/tags`

获取指定场景的可用标签。

---

## 错误处理

### 常见错误响应

**401 未授权：**
```json
{
  "code": 401,
  "message": "未授权访问",
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**422 验证错误：**
```json
{
  "code": 422,
  "message": "缺少必要参数",
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**404 资源不存在：**
```json
{
  "code": 404,
  "message": "资源不存在",
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 完整测试示例

### JavaScript/TypeScript 客户端示例

```javascript
// 配置基础URL和头部
const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'X-Test-Mode': 'true'  // 测试模式
};

// 登录
async function login(code) {
  const response = await fetch(`${API_BASE}/auth/sessions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ code })
  });
  return response.json();
}

// 获取用户信息
async function getUserInfo() {
  const response = await fetch(`${API_BASE}/users/me`, { headers });
  return response.json();
}

// 获取匹配卡片
async function getMatchCards(matchType, userRole) {
  const params = new URLSearchParams({ matchType, userRole });
  const response = await fetch(`${API_BASE}/matches/cards?${params}`, { headers });
  return response.json();
}

// 发送消息
async function sendMessage(matchId, content) {
  const response = await fetch(`${API_BASE}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ matchId, content, type: 'text' })
  });
  return response.json();
}
```

### 微信小程序示例

```javascript
// 微信小程序 API 调用示例
const API_BASE = 'http://localhost:8000/api/v1';

// 登录
function wxLogin() {
  wx.login({
    success: (res) => {
      wx.request({
        url: `${API_BASE}/auth/sessions`,
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'X-Test-Mode': 'true'
        },
        data: {
          code: res.code
        },
        success: (response) => {
          console.log('登录成功', response.data);
          // 保存 token
          wx.setStorageSync('token', response.data.data.token);
        }
      });
    }
  });
}

// 获取匹配卡片
function getMatchCards() {
  wx.request({
    url: `${API_BASE}/matches/cards`,
    method: 'GET',
    header: {
      'X-Test-Mode': 'true'
    },
    data: {
      matchType: 'housing',
      userRole: 'seeker'
    },
    success: (response) => {
      console.log('匹配卡片', response.data);
    }
  });
}
```

---

## 总结

这份 API 文档提供了 WeMatch 应用的完整 RESTful API 参考。所有端点都支持测试模式，便于开发和调试。客户端开发者可以根据这份文档快速集成 API 功能。

如有疑问或需要更多示例，请参考项目中的测试文件或联系后端开发团队。