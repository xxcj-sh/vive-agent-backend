from app.utils.db_config import Base, engine
from app.models import User, Match, MatchDetail
from app.models.match_action import MatchAction, MatchResult
from app.models.user_profile import UserProfile
from app.models.user_card_db import UserCard
from app.models.llm_usage_log import LLMUsageLog
from app.models.order import MembershipOrder

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")