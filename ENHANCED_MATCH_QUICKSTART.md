# 增强匹配撮合功能 - 快速启动指南

## ✅ 功能状态
- **开发完成**: ✅ 所有核心功能已实现
- **测试通过**: ✅ 兼容性算法测试通过
- **依赖安装**: ✅ 所有依赖项已安装
- **模块导入**: ✅ 所有模块可正常导入

## 🚀 快速启动

### 1. 启动后端API服务
```bash
cd vmatch-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动匹配调度器（可选）
```bash
# 在新的终端窗口中运行
cd vmatch-backend
python scripts/start_match_scheduler.py
```

### 3. 测试API接口
```bash
# 检查调度器状态
curl http://localhost:8000/api/v1/enhanced-match/scheduler/status

# 获取匹配推荐（需要有用户数据）
curl "http://localhost:8000/api/v1/enhanced-match/recommendations?matchType=housing&maxRecommendations=5"

# 获取匹配统计
curl http://localhost:8000/api/v1/enhanced-match/statistics
```

## 📋 核心功能

### 1. 智能匹配算法
- **房源匹配**: 价格、位置、类型、租期、生活习惯多维度匹配
- **交友匹配**: 兴趣、年龄、位置、教育、职业综合匹配  
- **活动匹配**: 类型、时间、地点、预算全方位匹配

### 2. 离线任务调度
- **每日推荐**: 凌晨2点自动生成用户推荐
- **数据清理**: 每小时清理过期数据
- **统计更新**: 每30分钟更新匹配统计

### 3. API接口
- `GET /enhanced-match/recommendations` - 获取智能推荐
- `GET /enhanced-match/statistics` - 获取匹配统计
- `GET /enhanced-match/compatibility/{user_id}` - 计算兼容性
- `DELETE /enhanced-match/cache` - 清除推荐缓存

## 🔧 配置说明

### 算法权重配置
在 `app/services/enhanced_match_service.py` 中可调整匹配权重：

```python
# 房源匹配权重
HOUSING_WEIGHTS = {
    'price': 0.30,      # 价格匹配 30%
    'location': 0.25,   # 地理位置 25%
    'type': 0.20,       # 房屋类型 20%
    'lease': 0.15,      # 租期匹配 15%
    'habits': 0.10      # 生活习惯 10%
}
```

### 调度任务配置
在 `app/services/match_scheduler.py` 中可调整执行时间：

```python
# 每日推荐生成时间
schedule.every().day.at("02:00").do(self.run_daily_match_generation)

# 数据清理频率
schedule.every().hour.do(self.run_hourly_match_cleanup)

# 统计更新频率  
schedule.every(30).minutes.do(self.run_match_statistics_update)
```

## 📊 测试结果

最新测试结果显示：
- **房源匹配兼容性**: 92.0% (优秀)
- **交友匹配兼容性**: 82.0% (良好)
- **所有核心算法**: ✅ 测试通过

## 🔗 前端集成

参考 `vmatch-frontend/dev_reference/enhanced_match_integration.md` 进行前端集成：

1. 更新 API 服务添加增强匹配接口
2. 修改首页逻辑优先使用智能推荐
3. 添加兼容性分数和匹配原因显示
4. 实现推荐缓存刷新功能

## 📚 详细文档

- **API文档**: `docs/enhanced_match_api.md`
- **部署指南**: `docs/enhanced_match_deployment.md`  
- **前端集成**: `vmatch-frontend/dev_reference/enhanced_match_integration.md`

## 🐛 故障排查

### 常见问题
1. **模块导入错误**: 确保已安装 `schedule==1.2.0`
2. **推荐结果为空**: 检查用户数据是否完整
3. **调度器无法启动**: 检查数据库连接和端口占用

### 解决方案
```bash
# 安装缺失依赖
python -m pip install schedule==1.2.0

# 检查用户数据
python -c "from app.database import get_db; from app.models.user import User; db=next(get_db()); print(f'用户数量: {db.query(User).count()}')"

# 重启服务
pkill -f uvicorn
python -m uvicorn app.main:app --reload
```

## 🎯 下一步计划

1. **性能优化**: 添加Redis缓存支持
2. **机器学习**: 集成ML模型优化匹配算法
3. **实时推送**: 添加WebSocket实时匹配通知
4. **A/B测试**: 实现多种匹配策略对比

---

**增强匹配撮合功能已完成开发并可投入使用！** 🎉