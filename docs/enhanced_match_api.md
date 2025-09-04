# 增强匹配撮合功能 API 文档

## 概述

增强匹配撮合功能提供智能的用户匹配推荐服务，通过分析用户资料、偏好和行为数据，为用户推荐最合适的匹配对象。系统支持房源匹配、交友匹配和活动匹配三种场景。

## 核心功能

### 1. 智能匹配算法
- **兼容性计算**: 基于多维度数据计算用户间的兼容性分数
- **个性化推荐**: 根据用户偏好和历史行为生成个性化推荐
- **实时更新**: 支持实时更新推荐列表和缓存管理

### 2. 离线任务调度
- **每日推荐生成**: 每天凌晨2点自动生成匹配推荐
- **数据清理**: 每小时清理过期数据和无效记录
- **统计更新**: 每30分钟更新匹配统计信息

### 3. 缓存管理
- **推荐缓存**: 缓存用户推荐结果，提高响应速度
- **过期管理**: 自动清理过期缓存数据
- **手动刷新**: 支持用户主动刷新推荐缓存

## API 接口

### 1. 获取匹配推荐

**接口地址**: `GET /api/v1/enhanced-match/recommendations`

**请求参数**:
```json
{
  "matchType": "housing|dating|activity",  // 必填，匹配类型
  "maxRecommendations": 10,                // 可选，最大推荐数量，默认10
  "refreshCache": false                    // 可选，是否刷新缓存，默认false
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "recommendations": [
      {
        "user_id": "user123",
        "user_info": {
          "id": "user123",
          "name": "张三",
          "avatar": "https://example.com/avatar.jpg",
          "age": 28,
          "occupation": "软件工程师",
          "location": ["北京市", "朝阳区"]
        },
        "profile_data": {
          "housing_price": 5000,
          "housing_area": 80,
          "location": "朝阳区"
        },
        "compatibility_score": 85.5,
        "match_reasons": [
          "价格符合预算",
          "地理位置匹配",
          "房屋类型匹配"
        ]
      }
    ],
    "total": 10,
    "fromCache": false,
    "matchType": "housing",
    "generatedAt": "2024-01-15T10:30:00"
  }
}
```

### 2. 获取匹配统计

**接口地址**: `GET /api/v1/enhanced-match/statistics`

**请求参数**:
```json
{
  "matchType": "housing"  // 可选，匹配类型筛选
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_actions": 150,
    "likes_count": 80,
    "super_likes_count": 20,
    "dislikes_count": 50,
    "total_matches": 25,
    "active_matches": 20,
    "match_rate": 25.0,
    "recent_actions": 15,
    "recent_matches": 3,
    "activity_level": "活跃"
  }
}
```

### 3. 计算兼容性分数

**接口地址**: `GET /api/v1/enhanced-match/compatibility/{target_user_id}`

**请求参数**:
```json
{
  "matchType": "housing"  // 必填，匹配类型
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "targetUserId": "user456",
    "matchType": "housing",
    "compatibilityScore": 78.5,
    "matchReasons": [
      "价格符合预算",
      "地理位置匹配"
    ],
    "compatibilityLevel": "较为匹配"
  }
}
```

### 4. 批量生成推荐（管理员）

**接口地址**: `POST /api/v1/enhanced-match/batch-generate`

**请求体**:
```json
{
  "matchType": "housing",
  "batchSize": 100
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "批量生成任务已启动",
  "data": {
    "matchType": "housing",
    "batchSize": 100,
    "status": "started"
  }
}
```

### 5. 调度器状态查询

**接口地址**: `GET /api/v1/enhanced-match/scheduler/status`

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "is_running": true,
    "last_run_times": {
      "daily_generation": "2024-01-15T02:00:00",
      "hourly_cleanup": "2024-01-15T10:00:00",
      "statistics_update": "2024-01-15T10:30:00"
    },
    "next_scheduled_runs": {
      "daily_generation": "每天 02:00",
      "hourly_cleanup": "每小时",
      "statistics_update": "每30分钟"
    }
  }
}
```

### 6. 手动触发任务（管理员）

**接口地址**: `POST /api/v1/enhanced-match/scheduler/trigger`

**请求体**:
```json
{
  "taskName": "daily_generation"  // daily_generation, hourly_cleanup, statistics_update
}
```

### 7. 清除推荐缓存

**接口地址**: `DELETE /api/v1/enhanced-match/cache`

**请求参数**:
```json
{
  "matchType": "housing"  // 可选，指定匹配类型，不填则清除所有
}
```

## 匹配算法说明

### 房源匹配算法

**权重分配**:
- 价格匹配: 30%
- 地理位置: 25%
- 房屋类型: 20%
- 租期匹配: 15%
- 生活习惯: 10%

**计算逻辑**:
1. 价格在预算范围内得满分，偏差500元内得部分分数
2. 地理位置完全匹配得满分，部分匹配得部分分数
3. 房屋类型、租期完全匹配得满分
4. 生活习惯根据共同偏好数量计分

### 交友匹配算法

**权重分配**:
- 兴趣爱好: 30%
- 年龄匹配: 20%
- 地理位置: 20%
- 教育背景: 15%
- 职业匹配: 15%

**计算逻辑**:
1. 共同兴趣越多分数越高
2. 年龄差距在3岁内得满分，5岁内得部分分数
3. 同城用户得满分，同省得部分分数
4. 相同教育背景和职业得满分

### 活动匹配算法

**权重分配**:
- 活动类型: 35%
- 时间匹配: 25%
- 地点匹配: 20%
- 预算匹配: 20%

## 部署和运行

### 1. 启动调度器

```bash
# 进入项目目录
cd vmatch-backend

# 运行调度器
python scripts/start_match_scheduler.py
```

### 2. 环境要求

- Python 3.8+
- FastAPI
- SQLAlchemy
- Schedule
- 数据库（SQLite/PostgreSQL/MySQL）

### 3. 配置说明

调度器任务时间可在 `match_scheduler.py` 中配置：

```python
# 每天凌晨2点执行匹配推荐生成
schedule.every().day.at("02:00").do(self.run_daily_match_generation)

# 每小时执行数据清理
schedule.every().hour.do(self.run_hourly_match_cleanup)

# 每30分钟更新统计信息
schedule.every(30).minutes.do(self.run_match_statistics_update)
```

## 性能优化建议

### 1. 数据库优化
- 为匹配相关字段添加索引
- 定期清理历史数据
- 使用数据库连接池

### 2. 缓存策略
- 使用Redis替代内存缓存
- 设置合理的缓存过期时间
- 实现缓存预热机制

### 3. 算法优化
- 批量处理用户数据
- 异步执行耗时计算
- 使用机器学习优化匹配算法

## 监控和日志

### 1. 日志记录
- 调度器执行日志
- API请求响应日志
- 错误异常日志

### 2. 性能监控
- 匹配推荐生成耗时
- API响应时间
- 缓存命中率

### 3. 业务指标
- 用户匹配成功率
- 推荐点击率
- 用户活跃度

## 故障排查

### 1. 常见问题
- 调度器无法启动：检查数据库连接和权限
- 推荐结果为空：检查用户资料完整性
- 兼容性分数异常：检查算法参数配置

### 2. 日志分析
- 查看 `match_scheduler.log` 了解调度器状态
- 检查API错误日志定位问题
- 分析性能日志优化系统

### 3. 数据修复
- 清理异常匹配数据
- 重建推荐缓存
- 修复用户资料数据