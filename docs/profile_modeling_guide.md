# 用户画像离线建模模块开发指南

## 概述

用户画像离线建模模块是一个基于大语言模型的智能分析系统，用于验证用户人设真实性、确保内容合规性，并动态更新用户画像。该模块集成了火山引擎的多模态大模型服务（模型：ep-20251004235106-gklgg），为VMatch平台提供智能化的用户画像管理服务。

## 功能特性

### 1. 人设真实性验证
- **智能分析**：基于用户头像、个人简介、行为模式等多维度信息进行分析
- **真实性评分**：生成0-100分的真实性评分，帮助识别虚假账号
- **风险评估**：识别潜在的风险因素，如机器人行为、虚假信息传播等
- **改进建议**：提供具体的改进建议，帮助用户完善真实的人设

### 2. 内容合规性验证
- **违规检测**：自动检测卡片内容中的违规信息，包括敏感词汇、不当内容等
- **合规评分**：生成0-100分的合规性评分
- **分类标签**：为内容添加适当的分类标签
- **改进建议**：提供内容优化的具体建议

### 3. 用户画像动态更新
- **聊天记录分析**：基于用户最新的聊天记录分析偏好和特征
- **卡片内容整合**：结合新增卡片内容更新用户画像
- **多维度画像**：更新用户偏好、个性特征、心情状态等多个维度
- **置信度评估**：为画像更新提供置信度评分

## 架构设计

### 核心组件

```
vive-agent-backend/
├── app/
│   ├── services/
│   │   ├── profile_modeling_service.py      # 核心服务类
│   │   └── profile_modeling_scheduler.py    # 离线任务调度器
│   ├── routers/
│   │   └── profile_modeling.py               # API路由
│   └── models/
│       ├── user_profile.py                   # 用户画像模型
│       └── user_card.py                      # 用户卡片模型
├── tests/
│   └── test_profile_modeling.py              # 测试套件
└── examples/
    └── profile_modeling_examples.py          # 使用示例
```

### 数据流

```
用户数据 → ProfileModelingService → 大语言模型 → 分析结果 → 数据库更新
```

## API接口

### 人设真实性验证
```http
POST /api/v1/profile-modeling/verify-authenticity/{user_id}
```

**响应示例：**
```json
{
  "success": true,
  "authenticity_score": 85,
  "analysis_result": "用户人设真实度较高，头像为真人照片，个人简介详细且一致",
  "key_factors": ["头像真实性", "个人简介一致性", "行为模式正常"],
  "risk_assessment": "低风险",
  "recommendations": ["可以正常展示", "建议持续监控"]
}
```

### 内容合规性验证
```http
POST /api/v1/profile-modeling/verify-compliance/{card_id}
```

**响应示例：**
```json
{
  "success": true,
  "is_compliant": true,
  "compliance_score": 92,
  "violations": [],
  "suggestions": ["内容健康积极", "可以正常展示"],
  "categories": ["社交", "娱乐"]
}
```

### 用户画像更新
```http
POST /api/v1/profile-modeling/update-profile/{user_id}
```

**响应示例：**
```json
{
  "success": true,
  "confidence_score": 88,
  "analysis_summary": "用户偏好科技类内容，性格开朗外向，当前心情愉快",
  "updated_fields": {
    "preferences": "科技、游戏、音乐",
    "personality_traits": "开朗、外向、好奇",
    "mood_status": "愉快"
  },
  "key_insights": ["对新技术很感兴趣", "喜欢分享生活"],
  "recommendations": ["推荐科技类卡片", "鼓励更多互动"]
}
```

## 使用指南

### 基本使用

```python
from app.services.profile_modeling_service import ProfileModelingService
from app.dependencies import get_db

# 获取数据库会话
db = next(get_db())

# 创建建模服务
modeling_service = ProfileModelingService(db)

# 验证人设真实性
result = await modeling_service.verify_profile_authenticity(user_id=1)

# 验证内容合规性
result = await modeling_service.verify_content_compliance(card_id=1)

# 更新用户画像
result = await modeling_service.update_user_profile_analysis(user_id=1)
```

### 批量处理

```python
# 批量验证多个用户
user_ids = [1, 2, 3, 4, 5]
results = []

for user_id in user_ids:
    result = await modeling_service.verify_profile_authenticity(user_id)
    results.append(result)
    
    # 添加延迟避免API调用过于频繁
    await asyncio.sleep(0.5)
```

### 错误处理

```python
import asyncio

async def verify_with_retry(user_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await modeling_service.verify_profile_authenticity(user_id)
            if result["success"]:
                return result
            else:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return {"success": False, "error": str(e)}
```

## 配置参数

### 模型配置
```python
# 使用的多模态大模型
LLM_MODEL = "ep-20251004235106-gklgg"

# API配置
LLM_API_KEY = "your_api_key"
LLM_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
LLM_PROVIDER = "volcengine"
```

### 任务调度配置
```python
# 人设真实性验证任务
authenticity_config = {
    "interval_hours": 24,      # 每24小时执行一次
    "batch_size": 50,        # 每批处理50个用户
    "max_failures": 5        # 最大失败次数
}

# 内容合规性验证任务
compliance_config = {
    "interval_hours": 12,     # 每12小时执行一次
    "batch_size": 100,       # 每批处理100张卡片
    "max_failures": 3        # 最大失败次数
}

# 用户画像更新任务
profile_update_config = {
    "interval_hours": 6,      # 每6小时执行一次
    "batch_size": 30,        # 每批处理30个用户
    "max_failures": 5        # 最大失败次数
}
```

## 测试指南

### 运行测试
```bash
# 运行所有测试
pytest tests/test_profile_modeling.py -v

# 运行特定测试类
pytest tests/test_profile_modeling.py::TestProfileModelingService -v

# 运行特定测试方法
pytest tests/test_profile_modeling.py::TestProfileModelingService::test_verify_profile_authenticity_success -v
```

### 测试覆盖率
```bash
# 生成测试覆盖率报告
pytest tests/test_profile_modeling.py --cov=app.services.profile_modeling_service --cov-report=html
```

## 性能优化

### 批处理优化
- 合理设置批处理大小，避免单次处理过多数据
- 添加适当的延迟，避免API调用过于频繁
- 实现失败重试机制，提高处理成功率

### 缓存策略
- 对频繁查询的用户数据实现缓存
- 对模型响应结果进行缓存，避免重复调用
- 设置合理的缓存过期时间

### 异步处理
- 使用异步编程提高并发处理能力
- 合理设置并发数，避免资源竞争
- 实现任务队列，支持大规模数据处理

## 监控与日志

### 关键指标
- API调用成功率
- 平均响应时间
- 错误率和重试次数
- 任务执行时间

### 日志记录
```python
import logging

logger = logging.getLogger(__name__)

# 记录关键操作
logger.info(f"开始验证用户 {user_id} 的人设真实性")
logger.info(f"人设真实性验证完成，评分: {score}/100")

# 记录错误信息
logger.error(f"验证失败: {error_message}")
```

## 安全考虑

### 数据安全
- 对用户敏感信息进行脱敏处理
- 实现数据访问权限控制
- 定期清理过期数据

### API安全
- 实现API调用频率限制
- 添加请求签名验证
- 监控异常API调用模式

### 模型安全
- 对模型输入进行安全检查
- 防止提示词注入攻击
- 监控模型输出质量

## 故障排除

### 常见问题

#### API调用失败
- 检查API密钥是否正确
- 验证网络连接状态
- 确认模型名称是否正确

#### 数据库连接问题
- 检查数据库连接配置
- 确认数据库服务状态
- 验证用户权限设置

#### 任务调度异常
- 检查调度器配置参数
- 确认任务执行时间设置
- 查看任务执行日志

### 调试技巧
- 启用详细日志记录
- 使用测试数据验证功能
- 逐步执行代码定位问题

## 扩展开发

### 添加新功能
1. 在`ProfileModelingService`中添加新方法
2. 更新API路由
3. 添加相应的测试用例
4. 更新文档说明

### 集成新模型
1. 更新模型配置参数
2. 修改提示词模板
3. 调整响应解析逻辑
4. 验证新模型效果

### 性能优化
1. 分析性能瓶颈
2. 优化数据库查询
3. 改进批处理策略
4. 添加缓存机制

## 参考资料

- [火山引擎大模型API文档](https://www.volcengine.com/docs/82379/1399008)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [APScheduler文档](https://apscheduler.readthedocs.io/)

## 联系方式

如有问题或建议，请联系开发团队：
- 邮箱：dev-team@vive.com
- 技术文档：docs.vive.com
- 问题反馈：github.com/vive/vive-agent-backend/issues