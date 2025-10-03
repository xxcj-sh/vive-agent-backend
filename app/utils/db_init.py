from app.utils.db_config import Base, engine
from app.models import User, Match, MatchDetail
from app.models.match_action import MatchAction, MatchResult
from app.models.user_profile import UserProfile

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")