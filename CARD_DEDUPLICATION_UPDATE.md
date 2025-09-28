# 收藏卡片去重功能更新记录

## 修改概述
修复了用户统计服务中收藏卡片数量的统计逻辑，现在会根据 `target_card_id` 进行去重，避免同一卡片被多次收藏时重复计数的问题。

## 修改详情

### 文件位置
- 文件：`/Users/liukun/Documents/workspace/codebase/VMatch/vmatch-backend/app/services/user_stats_service.py`
- 方法：`_get_favorite_stats` 和 `_get_collect_stats`

### 具体修改
**修改前：**
```python
# 用户收藏的名片数量（COLLECTION操作）
favorite_cards = self.db.query(MatchAction).filter(
    MatchAction.user_id == user_id,
    MatchAction.action_type == MatchActionType.COLLECTION
).count()

# 用户的喜欢操作数量
total_favorites = self.db.query(MatchAction).filter(
    MatchAction.user_id == user_id,
    MatchAction.action_type == MatchActionType.COLLECTION
).count()
```

**修改后：**
```python
# 用户收藏的名片数量（COLLECTION操作）- 根据target_card_id去重
favorite_cards = self.db.query(MatchAction.target_card_id).filter(
    MatchAction.user_id == user_id,
    MatchAction.action_type == MatchActionType.COLLECTION
).distinct().count()

# 用户的收藏操作数量（根据target_card_id去重）
total_favorites = self.db.query(MatchAction.target_card_id).filter(
    MatchAction.user_id == user_id,
    MatchAction.action_type == MatchActionType.COLLECTION
).distinct().count()
```

### 技术变更
1. **查询字段变更**：从查询整个 `MatchAction` 对象改为只查询 `target_card_id` 字段
2. **添加去重逻辑**：使用 `.distinct()` 方法对 `target_card_id` 进行去重
3. **保持计数功能**：仍然使用 `.count()` 方法获取最终数量

## 问题背景

### 原始问题
在用户收藏卡片的统计中，如果用户对同一张卡片进行多次收藏操作，系统会将每次操作都计入统计，导致收藏数量虚高。

### 业务需求
用户统计应该反映用户实际收藏的不同卡片数量，而不是收藏操作的总次数。

## 测试验证

### 测试场景
- 创建测试用户对同一张卡片进行3次收藏操作
- 创建测试用户对另一张卡片进行1次收藏操作
- 验证去重后的统计结果

### 测试结果
- ✅ 去重前：4次收藏操作
- ✅ 去重后：2张不同的卡片
- ✅ 两个统计方法都正确实现了去重

## 影响范围

### 直接影响
- 用户个人中心的收藏统计显示
- 管理后台的用户数据统计
- 任何调用 `_get_favorite_stats` 和 `_get_collect_stats` 方法的功能

### 数据准确性
- 收藏卡片数量现在更准确反映实际收藏的不同卡片数
- 避免了重复操作导致的统计偏差
- 提升了用户数据的可信度

## 兼容性
- ✅ 数据库结构无需变更
- ✅ 现有API接口保持不变
- ✅ 向后兼容，不影响现有功能
- ✅ 性能影响极小（distinct操作在索引支持下效率良好）

## 最佳实践
这种去重统计方法可以推广到其他类似的统计场景，如：
- 用户点赞统计
- 用户浏览历史统计
- 用户互动行为统计