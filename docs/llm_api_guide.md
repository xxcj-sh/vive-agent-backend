# 大语言模型API使用指南

本文档介绍如何使用VMatch的大语言模型（LLM）API接口，包括用户资料分析、兴趣分析、聊天记录分析和智能问答等功能。

## 功能概述

大语言模型模块提供以下核心功能：

1. **用户资料分析** - 深度分析用户资料，提供个性化洞察
2. **兴趣分析** - 分析用户兴趣爱好，提供匹配建议
3. **聊天记录分析** - 分析聊天内容，评估关系质量
4. **智能问答** - 基于上下文回答用户问题
5. **使用统计** - 跟踪API调用情况和资源消耗

## 环境配置

### 1. 配置环境变量

在 `.env` 文件中添加LLM相关配置：

```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 可选的其他提供商配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM调用限制
LLM_MAX_TOKENS=1000
LLM_TIMEOUT=30
LLM_RATE_LIMIT_PER_MINUTE=60
```

### 2. 初始化数据库表

运行数据库迁移脚本：

```bash
python scripts/add_llm_tables.py
```

## API接口详解

### 1. 用户资料分析

**接口地址**: `POST /api/v1/llm/analyze-profile`

**请求示例**:

```json
{
  "profile_data": {
    "budget_range": [2000, 3500],
    "preferred_areas": ["朝阳区", "海淀区"],
    "room_type": "single_room",
    "occupation": "软件工程师",
    "lifestyle": "quiet"
  },
  "card_type": "housing_seeker"
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "analysis": {
      "personality": "内向稳重，注重生活质量",
      "lifestyle": "规律作息，偏好安静环境",
      "values": ["稳定", "舒适", "便利"]
    },
    "key_insights": [
      "用户偏好安静的生活环境",
      "对交通便利性要求较高",
      "预算相对充足，注重性价比"
    ],
    "recommendations": [
      "推荐靠近地铁的房源",
      "建议选择南向采光好的房间",
      "优先考虑有独立卫生间的房源"
    ],
    "usage": {
      "prompt_tokens": 156,
      "completion_tokens": 89,
      "total_tokens": 245
    },
    "duration": 1.23
  }
}
```

### 2. 兴趣分析

**接口地址**: `POST /api/v1/llm/analyze-interests`

**请求示例**:

```json
{
  "user_interests": ["阅读", "旅行", "摄影", "美食", "音乐"],
  "context_data": {
    "match_type": "dating",
    "location": "北京"
  }
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "interests": ["阅读", "旅行", "摄影"],
    "categories": {
      "indoor": ["阅读", "音乐"],
      "outdoor": ["旅行", "摄影", "美食"]
    },
    "match_suggestions": [
      "推荐同样喜欢阅读的用户",
      "可以匹配摄影爱好者",
      "建议参加美食主题活动"
    ],
    "usage": {
      "prompt_tokens": 89,
      "completion_tokens": 67,
      "total_tokens": 156
    },
    "duration": 0.87
  }
}
```

### 3. 聊天记录分析

**接口地址**: `POST /api/v1/llm/analyze-chat`

**请求示例**:

```json
{
  "chat_history": [
    {
      "sender": "user_A",
      "content": "你好，看到你喜欢摄影，我也很喜欢拍照",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "sender": "user_B", 
      "content": "真的吗？你主要拍什么类型的照片？",
      "timestamp": "2024-01-15T10:32:00Z"
    }
  ],
  "analysis_type": "sentiment"
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "sentiment": "positive",
    "summary": "对话氛围友好，围绕共同兴趣摄影展开",
    "key_topics": ["摄影", "兴趣爱好", "经验交流"],
    "relationship_score": 0.75,
    "usage": {
      "prompt_tokens": 234,
      "completion_tokens": 123,
      "total_tokens": 357
    },
    "duration": 1.45
  }
}
```

### 4. 智能问答

**接口地址**: `POST /api/v1/llm/ask`

**请求示例**:

```json
{
  "question": "如何提高我的匹配成功率？",
  "context": {
    "user_type": "housing_seeker",
    "location": "北京",
    "budget": 3000
  }
}
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "根据您的情况，建议：1) 完善个人资料，突出稳定职业优势；2) 选择交通便利的区域；3) 上传真实清晰的照片；4) 主动与房东沟通，展现诚意",
    "confidence": 0.92,
    "sources": ["用户资料", "平台数据", "最佳实践"],
    "usage": {
      "prompt_tokens": 145,
      "completion_tokens": 89,
      "total_tokens": 234
    },
    "duration": 1.12
  }
}
```

### 5. 使用日志查询

**接口地址**: `GET /api/v1/llm/usage-logs`

**查询参数**:
- `user_id` (可选): 用户ID过滤
- `task_type` (可选): 任务类型过滤
- `provider` (可选): 提供商过滤
- `limit` (可选): 返回数量限制，默认20，最大100
- `offset` (可选): 偏移量，默认0

**请求示例**:

```bash
GET /api/v1/llm/usage-logs?limit=10&task_type=profile_analysis
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "logs": [
      {
        "id": "log_123456",
        "user_id": "user_789",
        "task_type": "profile_analysis",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "total_tokens": 245,
        "prompt_tokens": 156,
        "completion_tokens": 89,
        "duration": 1.23,
        "status": "success",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "limit": 10,
      "offset": 0,
      "total": 25
    }
  }
}
```

### 6. 使用统计

**接口地址**: `GET /api/v1/llm/usage-stats`

**查询参数**:
- `user_id` (可选): 用户ID过滤
- `days` (可选): 统计天数，默认7，最大30

**请求示例**:

```bash
GET /api/v1/llm/usage-stats?days=7
```

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "period": {
      "start_date": "2024-01-08T00:00:00Z",
      "end_date": "2024-01-15T23:59:59Z",
      "days": 7
    },
    "summary": {
      "total_calls": 15,
      "total_tokens": 3456,
      "total_cost": 3.46,
      "avg_tokens_per_call": 230.4
    },
    "task_stats": [
      {
        "task_type": "profile_analysis",
        "count": 8,
        "tokens": 1872,
        "percentage": 53.3
      },
      {
        "task_type": "interest_analysis",
        "count": 5,
        "tokens": 1045,
        "percentage": 33.3
      }
    ],
    "provider_stats": [
      {
        "provider": "openai",
        "count": 15,
        "tokens": 3456,
        "percentage": 100
      }
    ]
  }
}
```

## 错误处理

API调用可能返回以下错误：

- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `429 Too Many Requests`: 超过调用频率限制
- `500 Internal Server Error`: 服务器内部错误

## 最佳实践

### 1. 请求优化

- **分批处理**: 大量数据建议分批发送
- **缓存结果**: 相同分析结果可缓存，避免重复调用
- **超时处理**: 设置合理的超时时间，避免长时间等待

### 2. 成本控制

- **监控使用**: 定期查看使用统计，了解token消耗
- **选择合适的模型**: 根据需求选择GPT-3.5或GPT-4
- **限制调用频率**: 实施客户端调用频率限制

### 3. 数据隐私

- **敏感信息处理**: 避免在请求中包含敏感个人信息
- **日志清理**: 定期清理旧的调用日志
- **权限控制**: 确保用户只能查看自己的使用记录

## 集成示例

### Python客户端示例

```python
import requests

# 用户资料分析
response = requests.post(
    "http://localhost:8000/api/v1/llm/analyze-profile",
    json={
        "profile_data": {
            "budget_range": [2000, 3000],
            "occupation": "软件工程师"
        },
        "card_type": "housing_seeker"
    },
    headers={"Authorization": "Bearer your_token_here"}
)

result = response.json()
print(result["data"]["analysis"])
```

### JavaScript客户端示例

```javascript
// 聊天记录分析
const response = await fetch('/api/v1/llm/analyze-chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    chat_history: [
      { sender: 'user1', content: '你好' },
      { sender: 'user2', content: '很高兴认识你' }
    ],
    analysis_type: 'summary'
  })
});

const result = await response.json();
console.log(result.data.summary);
```

## 性能监控

建议监控以下指标：

- **响应时间**: 平均API响应时间
- **成功率**: API调用成功百分比
- **token消耗**: 每日/每周token使用量
- **错误率**: 各类错误的发生频率

## 扩展支持

当前支持以下LLM提供商：

- **OpenAI** (已集成): GPT-3.5, GPT-4
- **Anthropic** (预留): Claude
- **Google** (预留): Gemini
- **百度** (预留): ERNIE
- **阿里** (预留): 通义千问

如需添加新的提供商，请联系开发团队。