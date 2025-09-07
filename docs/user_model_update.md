# 用户模型更新文档

## 变更概述

本次更新在用户模型中新增了 `register_at` 和 `status` 字段，用于记录用户注册时间和状态管理。

## 具体变更

### 1. 数据库模型变更

**文件**: `app/models/user.py`

- **新增字段**:
  - `register_at`: DateTime类型，可空，记录用户注册成功时间
  - `status`: String类型，默认值为"pending"，用户状态枚举

- **状态枚举值**:
  - `pending`: 待激活
  - `active`: 正常
  - `suspended`: 暂停
  - `deleted`: 已删除

### 2. Pydantic模型更新

- **UserBase**: 新增status和register_at可选字段
- **UserCreate**: 继承UserBase，支持新字段
- **UserResponse**: 新增register_at字段
- **UserProfileUpdate**: 新增status和register_at字段

### 3. 服务层变更

**文件**: `app/services/auth.py`

- **register方法**: 创建用户时自动设置status="active"和register_at=当前时间
- **login_by_phone方法**: 创建新用户时同样设置新字段

### 4. API接口更新

**文件**: `app/routers/users.py`

- **get_current_user_info**: 返回数据新增registerAt字段

### 5. 数据库迁移

**文件**: `scripts/add_register_fields.py`

- 自动添加register_at字段到users表
- 更新status字段默认值为"pending"
- 为现有用户设置合理的status和register_at值

## 使用方法

### 创建用户时
```python
# 系统会自动设置status和register_at字段
user_data = {
    "phone": "13800138000",
    "nick_name": "新用户",
    # 无需手动设置status和register_at
}
```

### 查询用户信息时
```json
{
  "id": "user_id",
  "nick_name": "用户名",
  "status": "active",
  "register_at": "2024-01-15T10:30:00",
  "registerAt": "2024-01-15T10:30:00"
}
```

### 更新用户状态
```python
# 通过UserProfileUpdate模型更新状态
update_data = {
    "status": "suspended"
}
```

## 状态管理建议

1. **注册流程**: 用户注册成功后自动设置为"active"
2. **用户管理**: 管理员可通过接口调整用户状态
3. **权限控制**: 根据status字段控制用户访问权限
4. **数据清理**: 定期清理"deleted"状态的用户数据

## 测试验证

运行测试脚本验证新字段功能：
```bash
python scripts/test_new_fields.py
```

## 后续优化

- 考虑添加状态变更日志
- 实现状态变更通知机制
- 支持批量状态更新操作