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

#### 获取用户所有角色资料
**GET** `/users/me/profiles`

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "test_user_001",
    "total_count": 5,
    "active_count": 5,
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
            "profile_data": {...},
            "preferences": {...},
            "tags": ["程序员", "安静", "整洁"],
            "is_active": 1,
            "visibility": "public",
            "created_at": "2025-01-29T01:00:00",
            "updated_at": "2025-01-29T01:00:00"
          }
        ]
      }
    ],
    "all_profiles": [...]
  }
}
```

#### 获取特定场景下的角色资料
**GET** `/users/me/profiles/{scene_type}`

**路径参数:**
- `scene_type`: 场景类型 (housing/dating/activity)

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
        "role_type": "housing_seeker",
        "display_name": "小李找房",
        "avatar_url": "https://example.com/avatars/housing_seeker.jpg",
        "bio": "刚毕业的程序员，寻找合适的合租房源",
        "profile_data": {...},
        "preferences": {...},
        "tags": ["程序员", "安静", "整洁"],
        "is_active": 1,
        "visibility": "public",
        "created_at": "2025-01-29T01:00:00",
        "updated_at": "2025-01-29T01:00:00"
      }
    ]
  }
}
```

#### 获取特定角色的资料
**GET** `/users/me/profiles/{scene_type}/{role_type}`

**路径参数:**
- `scene_type`: 场景类型
- `role_type`: 角色类型

**响应示例:**
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
    "profile_data": {
      "budget_range": [2000, 3500],
      "preferred_areas": ["朝阳区", "海淀区"],
      "room_type": "single_room",
      "occupation": "软件工程师"
    },
    "preferences": {
      "roommate_gender": "any",
      "shared_facilities": ["kitchen", "living_room"]
    },
    "tags": ["程序员", "安静", "整洁"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T01:00:00",
    "updated_at": "2025-01-29T01:00:00"
  }
}
```

#### 创建用户角色资料
**POST** `/users/me/profiles`

**请求体:**
```json
{
  "role_type": "housing_seeker",
  "scene_type": "housing",
  "display_name": "小李找房",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "寻找合适的合租房源",
  "profile_data": {
    "budget_range": [2000, 3500],
    "preferred_areas": ["朝阳区"]
  },
  "preferences": {
    "roommate_gender": "any"
  },
  "tags": ["程序员", "安静"],
  "visibility": "public"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_002",
    "user_id": "current_user_id",
    "role_type": "housing_seeker",
    "scene_type": "housing",
    "display_name": "小李找房",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "寻找合适的合租房源",
    "profile_data": {
      "budget_range": [2000, 3500],
      "preferred_areas": ["朝阳区"]
    },
    "preferences": {
      "roommate_gender": "any"
    },
    "tags": ["程序员", "安静"],
    "is_active": 1,
    "visibility": "public",
    "created_at": "2025-01-29T01:00:00",
    "updated_at": "2025-01-29T01:00:00"
  }
}
```

#### 更新用户角色资料
**PUT** `/users/me/profiles/{profile_id}`

**路径参数:**
- `profile_id`: 资料ID

**请求体:** (所有字段都是可选的)
```json
{
  "display_name": "更新后的名称",
  "bio": "更新后的简介",
  "profile_data": {...},
  "preferences": {...},
  "tags": [...],
  "visibility": "private"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_001",
    "display_name": "更新后的名称",
    "bio": "更新后的简介",
    "updated_at": "2025-01-29T02:00:00"
  }
}
```

#### 删除用户角色资料
**DELETE** `/users/me/profiles/{profile_id}`

**路径参数:**
- `profile_id`: 资料ID

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "deleted_profile_id": "profile_housing_seeker_001"
  }
}
```

#### 切换资料激活状态
**PATCH** `/users/me/profiles/{profile_id}/toggle`

**路径参数:**
- `profile_id`: 资料ID

**查询参数:**
- `is_active`: 激活状态 (1-激活, 0-停用)

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "profile_housing_seeker_001",
    "is_active": 1,
    "updated_at": "2025-01-29T02:00:00"
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