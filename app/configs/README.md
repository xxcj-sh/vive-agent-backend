# Prompt配置管理器

这个模块负责管理所有的LLM提示词配置，支持从独立的JSON文件中加载和管理提示词模板。

## 功能特性

- **独立配置管理**: 将提示词模板从代码中分离，便于统一管理和维护
- **多场景支持**: 支持系统提示词、场景提示词、任务提示词等多种类型
- **模板变量替换**: 支持在提示词模板中使用变量占位符
- **配置热重载**: 支持运行时重新加载配置文件
- **错误容错**: 配置文件加载失败时提供默认提示词，不影响主要功能

## 配置文件结构

```
app/configs/prompts/
├── system_prompts.json      # 系统提示词配置
├── mock_responses.json      # 模拟响应数据配置  
├── scene_prompts.json       # 场景化提示词配置
├── task_prompts.json        # 任务专用提示词配置
├── stream_configs.json      # 流式响应配置
└── README.json              # 配置说明文档
```

## 使用方法

### 1. 导入配置管理器

```python
from app.configs.prompt_config_manager import prompt_config_manager
```

### 2. 获取系统提示词

```python
# 根据任务类型获取系统提示词
system_prompt = prompt_config_manager.get_system_prompt("PROFILE_ANALYSIS")
```

### 3. 获取场景提示词

```python
# 获取对话建议场景的提示词
scene_prompt = prompt_config_manager.get_scene_prompt(
    "conversation_suggestions", 
    "stream",
    max_suggestions=3,
    user_personality="外向开朗",
    chat_history="[]"
)
```

### 4. 获取任务专用提示词

```python
# 获取用户画像分析任务的提示词
task_prompt = prompt_config_manager.get_task_prompt(
    "profile_analysis",
    card_type="个人卡片",
    profile_data='{"name": "张三", "age": 25}'
)
```

### 5. 重新加载配置

```python
# 在配置文件更新后重新加载
prompt_config_manager.reload_configs()
```

## 配置格式

### 系统提示词配置 (system_prompts.json)

```json
{
  "system_prompts": {
    "PROFILE_ANALYSIS": {
      "role": "专业的用户画像分析师",
      "description": "分析用户的资料数据，提供深入的洞察和个性化建议",
      "requirements": ["用中文回复", "确保分析结果准确有用"],
      "prompt": "你是一个专业的用户画像分析师..."
    }
  }
}
```

### 场景提示词配置 (scene_prompts.json)

```json
{
  "scene_prompts": {
    "conversation_suggestions": {
      "templates": {
        "stream": {
          "template": "请根据以下信息生成对话建议: {base_info}"
        }
      }
    }
  }
}
```

## 错误处理

- 配置文件加载失败时，系统会使用内置的默认提示词
- 配置项缺失时，会返回空字符串或默认配置
- 所有错误都会被记录，但不会中断主要功能

## 维护建议

1. **版本控制**: 配置文件应与代码一起进行版本控制
2. **定期更新**: 根据业务需求定期更新提示词内容
3. **测试验证**: 更新配置后需要进行充分的测试验证
4. **备份策略**: 重要的配置更改前应进行备份