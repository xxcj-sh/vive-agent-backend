# 匹配系统API使用示例

## 概述

匹配系统实现了用户之间的双向匹配功能，支持多种场景（房源、交友、活动等）。当两个用户在同一场景下互相喜欢时，系统会自动创建匹配记录。

## 核心功能

### 1. 提交匹配操作

**接口**: `POST /api/v1/matches/actions`

**功能**: 用户对其他用户执行匹配操作（喜欢/不喜欢/超级喜欢）

**请求示例**:
```json
{
  "cardId": "profile_housing_seeker_001",
  "action": "like",
  "matchType": "housing",
  "sceneContext": "朝阳区找房"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "isMatch": true,
    "matchId": "match_12345",
    "actionId": "action_67890",
    "message": "操作成功"
  }
}
```

**操作类型说明**:
- `like`: 喜欢
- `dislike`: 不喜欢
- `super_like`: 超级喜欢
- `pass`: 跳过

### 2. 滑动卡片

**接口**: `POST /api/v1/matches/swipes`

**功能**: 通过滑动手势执行匹配操作

**请求示例**:
```json
{
  "cardId": "profile_housing_seeker_001",
  "direction": "right",
  "matchType": "housing"
}
```

**滑动方向映射**:
- `right`: 喜欢 (like)
- `left`: 不喜欢 (dislike)
- `up`: 超级喜欢 (super_like)
- `down`: 跳过 (pass)

### 3. 获取匹配列表

**接口**: `GET /api/v1/matches`

**功能**: 获取用户的匹配列表

**请求参数**:
- `status`: 状态筛选 (all/new/contacted)
- `page`: 页码，默认1
- `pageSize`: 每页数量，默认10

**请求示例**:
```
GET /api/v1/matches?status=all&page=1&pageSize=10
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "matches": [
      {
        "id": "match_12345",
        "user": {
          "id": "user_002",
          "name": "小王",
          "avatar": "https://example.com/avatar.jpg"
        },
        "matchedAt": "2025-01-29T10:00:00Z",
        "lastActivity": "2025-01-29T10:00:00Z",
        "matchType": "housing",
        "status": "matched"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 10,
      "total": 1,
      "totalPages": 1
    }
  }
}
```

### 4. 获取匹配详情

**接口**: `GET /api/v1/matches/{matchId}`

**功能**: 获取特定匹配的详细信息

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "match_12345",
    "user": {
      "id": "user_002",
      "name": "小王",
      "avatar": "https://example.com/avatar.jpg",
      "age": 25,
      "location": ["北京", "朝阳区"],
      "occupation": "设计师",
      "bio": "热爱生活的设计师"
    },
    "matchedAt": "2025-01-29T10:00:00Z",
    "matchType": "housing",
    "status": "matched",
    "reason": "你们都在寻找合适的住房"
  }
}
```

### 5. 获取操作历史

**接口**: `GET /api/v1/matches/actions/history`

**功能**: 获取用户的匹配操作历史记录

**请求参数**:
- `matchType`: 匹配类型筛选 (可选)
- `page`: 页码，默认1
- `pageSize`: 每页数量，默认20

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "actions": [
      {
        "id": "action_67890",
        "targetUser": {
          "id": "user_002",
          "name": "小王"
        },
        "actionType": "like",
        "matchType": "housing",
        "createdAt": "2025-01-29T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 1
    }
  }
}
```

## 匹配逻辑说明

### 双向匹配检测

1. 用户A对用户B执行"喜欢"操作
2. 系统记录操作到 `match_actions` 表
3. 系统检查用户B是否也对用户A执行过"喜欢"操作
4. 如果双方都喜欢，系统创建匹配记录到 `match_results` 表
5. 返回 `isMatch: true` 和匹配ID

### 防重复操作

- 系统通过唯一约束防止同一用户对同一目标重复操作
- 如果检测到重复操作，返回相应提示信息

### 匹配状态管理

- `pending`: 等待对方操作
- `matched`: 双向匹配成功
- `unmatched`: 未匹配
- `expired`: 已过期

## 数据库设计

### match_actions 表
记录所有用户的匹配操作：
- `user_id`: 操作用户ID
- `target_user_id`: 目标用户ID
- `target_card_id`: 目标卡片ID
- `action_type`: 操作类型
- `match_type`: 匹配场景类型

### match_results 表
记录成功的匹配结果：
- `user1_id`, `user2_id`: 匹配的两个用户ID
- `user1_card_id`, `user2_card_id`: 对应的卡片ID
- `match_type`: 匹配场景类型
- `status`: 匹配状态
- `matched_at`: 匹配时间

## 使用场景

### 房源匹配场景
```javascript
// 用户喜欢某个房源
const response = await fetch('/api/v1/matches/actions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cardId: 'property_12345',
    action: 'like',
    matchType: 'housing'
  })
});

if (response.data.isMatch) {
  // 双向匹配成功，可以开始聊天
  console.log('匹配成功！', response.data.matchId);
}
```

### 交友匹配场景
```javascript
// 右滑喜欢某个用户
const response = await fetch('/api/v1/matches/swipes', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cardId: 'user_profile_67890',
    direction: 'right',
    matchType: 'dating'
  })
});
```

## 错误处理

### 常见错误码
- `400`: 请求参数错误
- `404`: 匹配记录不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

### 错误响应示例
```json
{
  "code": 400,
  "message": "缺少必要参数: cardId, action, matchType",
  "data": null
}
```

## 测试建议

1. 使用测试模式头部 `X-Test-Mode: true`
2. 创建多个测试用户进行双向匹配测试
3. 验证重复操作的防护机制
4. 测试不同场景类型的匹配功能

## 性能优化

1. 数据库索引优化
2. 缓存热门匹配数据
3. 异步处理匹配检测
4. 分页查询大量数据

## 安全考虑

1. 用户身份验证
2. 操作频率限制
3. 敏感信息脱敏
4. 防止恶意操作