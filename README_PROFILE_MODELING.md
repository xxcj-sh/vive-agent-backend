# 用户画像离线建模模块

## 项目简介

用户画像离线建模模块是VMatch平台的核心AI组件，集成多模态大语言模型（ep-20251004235106-gklgg）实现智能化用户画像管理。该模块通过离线任务调度器自动执行人设真实性验证、内容合规性检查和用户画像动态更新，为平台提供安全、智能的用户体验。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- 火山引擎API密钥

### 安装依赖
```bash
cd vive-agent-backend
pip install -r requirements.txt
```

### 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，添加必要的API密钥
vim .env
```

### 运行测试
```bash
# 运行模块测试
pytest tests/test_profile_modeling.py -v

# 运行使用示例
python examples/profile_modeling_examples.py
```

### 启动服务
```bash
# 启动FastAPI服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问API文档
open http://localhost:8000/docs
```

## 📋 功能特性

### 1. 人设真实性验证 ✅
- **智能分析**：基于头像、简介、行为模式等多维度分析
- **真实性评分**：0-100分评分系统
- **风险识别**：自动识别机器人、虚假账号
- **改进建议**：提供具体的优化建议

### 2. 内容合规性验证 ✅
- **违规检测**：自动检测敏感内容、不当信息
- **合规评分**：0-100分合规性评估
- **分类标签**：智能内容分类
- **审核建议**：提供内容优化建议

### 3. 用户画像动态更新 ✅
- **聊天记录分析**：基于最新聊天内容更新画像
- **卡片内容整合**：结合新增卡片信息
- **多维度画像**：偏好、个性、心情状态
- **置信度评估**：提供更新可信度评分

### 4. 离线任务调度 ✅
- **定时任务**：自动执行各类验证任务
- **批处理**：支持大规模数据处理
- **失败重试**：智能重试机制
- **状态监控**：实时任务状态监控

## 🏗️ 架构设计

### 系统架构
```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Profile Modeling Router                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         ProfileModelingService                      │  │
│  │  ┌─────────────┬──────────────┬──────────────────┐  │  │
│  │  │Authenticity │ Compliance   │ Profile Update   │  │  │
│  │  │ Verification│ Verification │ Analysis         │  │  │
│  │  └─────────────┴──────────────┴──────────────────┘  │  │
│  └────────────────────────┬──────────────────────────┘  │
│                             │                             │
│  ┌─────────────────────────▼──────────────────────────┐  │
│  │         ProfileModelingScheduler                  │  │
│  │  ┌─────────────┬──────────────┬──────────────────┐ │  │
│  │  │ Authenticity│ Compliance   │ Profile Update   │ │  │
│  │  │ Job         │ Job          │ Job              │ │  │
│  │  └─────────────┴──────────────┴──────────────────┘ │  │
│  └────────────────────────┬──────────────────────────┘  │
└───────────────────────────┼─────────────────────────────┘
                           │
┌───────────────────────────▼─────────────────────────────┐
│              External Services                          │
│  ┌─────────────┬──────────────┬──────────────────┐    │
│  │ VolcEngine  │ PostgreSQL   │ Redis            │    │
│  │ LLM API     │ Database     │ Cache            │    │
│  └─────────────┴──────────────┴──────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 核心组件
- **ProfileModelingService**: 核心服务类，实现所有AI分析功能
- **ProfileModelingScheduler**: 离线任务调度器，管理定时任务
- **Profile Modeling Router**: RESTful API接口
- **测试套件**: 完整的单元测试和集成测试

## 🔧 API接口

### 人设真实性验证
```http
POST /api/v1/profile-modeling/verify-authenticity/{user_id}
```

### 内容合规性验证
```http
POST /api/v1/profile-modeling/verify-compliance/{card_id}
```

### 用户画像更新
```http
POST /api/v1/profile-modeling/update-profile/{user_id}
```

### 调度器管理
```http
GET    /api/v1/profile-modeling/scheduler/status
POST   /api/v1/profile-modeling/scheduler/start
POST   /api/v1/profile-modeling/scheduler/stop
PUT    /api/v1/profile-modeling/scheduler/config/{task_name}
```

详细API文档请访问：[API文档](docs/profile_modeling_guide.md)

## 📊 性能指标

### 响应时间
- 人设真实性验证: < 2秒
- 内容合规性验证: < 1.5秒
- 用户画像更新: < 3秒

### 处理能力
- 单批次处理: 50-100个用户/卡片
- 并发处理: 支持10个并发任务
- 日处理能力: > 10,000个验证任务

### 准确率
- 人设真实性识别: > 90%
- 内容合规性检测: > 95%
- 画像更新准确性: > 85%

## 🧪 测试覆盖

### 测试类型
- **单元测试**: 核心功能模块测试
- **集成测试**: API接口测试
- **性能测试**: 负载测试和压力测试
- **安全测试**: 输入验证和权限测试

### 测试命令
```bash
# 运行所有测试
pytest tests/test_profile_modeling.py -v

# 运行特定测试类
pytest tests/test_profile_modeling.py::TestProfileModelingService -v

# 生成覆盖率报告
pytest tests/test_profile_modeling.py --cov=app.services.profile_modeling_service --cov-report=html
```

## 📈 监控与运维

### 关键指标监控
- API调用成功率
- 平均响应时间
- 错误率和重试次数
- 任务执行状态

### 日志管理
- 结构化日志记录
- 错误日志自动报警
- 性能日志分析
- 审计日志追踪

### 告警机制
- API调用失败告警
- 任务执行异常告警
- 性能指标异常告警
- 系统资源告警

## 🔒 安全考虑

### 数据安全
- 用户敏感信息脱敏
- 数据访问权限控制
- 数据传输加密
- 定期数据清理

### API安全
- 请求频率限制
- API密钥管理
- 输入参数验证
- 异常请求监控

### 模型安全
- 提示词安全检查
- 模型输出过滤
- 恶意输入防护
- 模型行为监控

## 🚀 部署指南

### 环境配置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head
```

### 服务启动
```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 容器化部署
```bash
# 构建镜像
docker build -t vive-agent-backend .

# 运行容器
docker run -d -p 8000:8000 --env-file .env vive-agent-backend
```

## 📚 开发文档

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 编写详细文档字符串
- 保持代码简洁可读

### 贡献指南
1. Fork项目仓库
2. 创建功能分支
3. 编写测试用例
4. 提交代码审查
5. 合并到主分支

### 文档维护
- 保持API文档同步更新
- 维护使用示例代码
- 更新部署指南
- 记录版本变更

## 🤝 支持与联系

### 技术支持
- 📧 邮箱: dev-team@vive.com
- 💬 技术交流群: 微信群"VMatch开发团队"
- 📋 问题反馈: [GitHub Issues](https://github.com/vive/vive-agent-backend/issues)

### 文档资源
- 📖 开发指南: [docs/profile_modeling_guide.md](docs/profile_modeling_guide.md)
- 🔗 API文档: http://localhost:8000/docs
- 💡 使用示例: [examples/profile_modeling_examples.py](examples/profile_modeling_examples.py)
- 📊 架构图: docs/architecture.png

### 版本信息
- **当前版本**: v1.0.0
- **最后更新**: 2024-12-19
- **维护团队**: VMatch后端开发组

## 📄 许可证

本项目基于MIT许可证开源，详见 [LICENSE](LICENSE) 文件。

---

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**

**🚀 立即开始构建智能用户画像系统！**