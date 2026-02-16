"""自定义 JSON 类型，能够优雅处理无效的 JSON 数据"""

from sqlalchemy import types
import json


class SafeJSON(types.TypeDecorator):
    """安全的 JSON 类型，当 JSON 无效时返回默认值而不是抛出异常"""
    
    impl = types.JSON
    cache_ok = True
    
    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return self.default
        
        if isinstance(value, (dict, list)):
            return value
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError):
            if self.default is None:
                # 根据常见情况推断默认类型
                if self._is_likely_array(value):
                    return []
                return {}
            return self.default
    
    def _is_likely_array(self, value):
        """判断值是否可能是一个数组"""
        if isinstance(value, str):
            value = value.strip()
            return value.startswith('[')
        return False
