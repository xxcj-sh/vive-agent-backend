# Match Type 和 Role Type 命名规范迁移指南

## 问题总结

当前项目中存在以下命名和使用混乱：

### 1. 命名不一致
- **match_type**: 在不同表中有时用枚举，有时用字符串
- **role_type**: 前端用简化格式（seeker/provider），后端用完整格式（housing_seeker/housing_provider）

### 2. 映射关系分散
- 角色映射逻辑分布在多个服务类中
- 没有统一的转换标准

## 解决方案

### 1. 统一命名规范

#### 数据库层
- **match_type**: 统一使用字符串值：`housing`, `dating`, `activity`, `business`
- **role_type**: 统一使用完整格式：`{scene}_{role}`

#### API层
- 输入：接受简化角色格式（seeker/provider/organizer/participant）
- 输出：返回完整角色格式（housing_seeker等）

#### 内部转换
- 使用 `RoleConverter` 工具类统一处理转换

### 2. 文件结构

```
app/
├── models/
│   └── unified_enums.py          # 统一枚举定义
├── utils/
│   └── role_converter.py         # 角色转换工具
└── services/
    ├── user_card_service.py      # 已更新使用新规范
    ├── enhanced_match_service.py # 已更新使用新规范
    └── match_card_strategy.py    # 保持数据库查询使用完整格式
```

### 3. 使用示例

#### 前端调用示例
```javascript
// 前端发送简化格式
const request = {
  matchType: "housing",
  userRole: "seeker"  // 简化格式
}
```

#### 后端处理示例
```python
from app.utils.role_converter import RoleConverter

# 转换简化角色为完整角色
full_role = RoleConverter.to_full_role("housing", "seeker")  # -> "housing_seeker"

# 获取目标角色
target_role = RoleConverter.get_target_role("housing_seeker")  # -> "housing_provider"

# 验证角色组合
is_valid = RoleConverter.validate_role_pair("housing", "housing_seeker")  # -> True
```

### 4. 向后兼容性

#### API端点保持兼容
- 所有现有API端点继续工作
- 内部自动处理格式转换

#### 数据库保持兼容
- 现有数据无需迁移
- 新数据遵循统一格式

### 5. 迁移步骤

#### 步骤1：验证当前数据
```sql
-- 检查现有数据格式
SELECT DISTINCT scene_type, role_type FROM user_cards;
SELECT DISTINCT match_type FROM matches;
```

#### 步骤2：测试转换工具
```python
# 运行测试脚本
python -c "
from app.utils.role_converter import RoleConverter
print('Testing role conversion...')
print(RoleConverter.to_full_role('housing', 'seeker'))
print(RoleConverter.to_simplified_role('housing_seeker'))
print('All tests passed!')
"
```

#### 步骤3：逐步更新服务
1. 更新 `user_card_service.py` ✅ 已完成
2. 更新 `enhanced_match_service.py` ✅ 已完成
3. 更新 `match_card_strategy.py` ✅ 已完成（保持数据库查询使用完整格式）

#### 步骤4：更新测试用例
更新测试文件以使用新的角色转换工具。

### 6. 验证测试

运行以下测试确保迁移成功：

```bash
# 运行角色相关测试
python -m pytest tests/test_role_based_cards.py -v

# 运行数据库集成测试
python -m pytest tests/test_database_integration.py -v

# 运行匹配服务测试
python -m pytest tests/test_match_service.py -v
```

### 7. 监控指标

迁移后监控以下指标：
- API响应时间（转换逻辑的影响）
- 数据一致性检查
- 错误日志中的角色转换相关错误

## 注意事项

1. **数据一致性**：现有数据无需修改，新数据自动生成完整格式
2. **性能影响**：角色转换是轻量级操作，对性能影响极小
3. **错误处理**：转换工具包含完整的错误处理和验证
4. **文档更新**：相关API文档已更新以反映新的使用方式

## 联系方式

如有问题，请联系后端开发团队进行支持。