"""
整合后的匹配服务模块

该模块整合了原有的match_card_strategy.py、match_service_simple.py和match_service.py的功能，
提供了一个统一的、模块化的匹配服务实现。

主要组件：
- core.py: MatchService核心类，处理匹配逻辑
- card_strategy.py: MatchCardStrategy类，处理卡片推荐策略
- models.py: 数据模型和枚举定义
- legacy_compat.py: 兼容性层，确保原有代码可以正常运行

使用示例：
    from app.services.match_service import MatchService, MatchCardStrategy
    
    match_service = MatchService(db_session)
    card_strategy = MatchCardStrategy(db_session)
"""

from .core import MatchService
from .card_strategy import MatchCardStrategy
from .models import MatchResult, MatchActionType, MatchStatistics, MatchCard

# 兼容性导入 - 确保原有代码可以正常运行
from .legacy_compat import (
    MatchService as LegacyMatchService,
    MatchServiceSimple as LegacyMatchServiceSimple,
    MatchCardStrategyCompat as LegacyMatchCardStrategy
)

__all__ = [
    # 新的统一接口
    'MatchService',
    'MatchCardStrategy',
    'MatchResult',
    'MatchActionType',
    'MatchStatistics',
    'MatchCard',
    
    # 兼容性接口
    'LegacyMatchService',
    'LegacyMatchServiceSimple',
    'LegacyMatchCardStrategy',
]

# 版本信息
__version__ = "2.0.0"
__description__ = "整合后的匹配服务模块"
__author__ = "vmatch-backend"