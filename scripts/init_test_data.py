"""
初始化测试数据脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.order import MembershipOrder, OrderStatus, Base
from datetime import datetime

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tests/vmatch_dev.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# 创建表
Base.metadata.create_all(bind=engine)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_test_data():
    """初始化测试数据"""
    db = SessionLocal()
    
    try:
        # 清空现有数据
        db.query(MembershipOrder).delete()
        
        # 创建测试订单数据
        test_orders = [
            MembershipOrder(
                id="20230615001",
                plan_name="月度会员",
                amount=29.9,
                date=datetime(2023, 6, 15),
                status=OrderStatus.PAID,
                user_id="test_user_001",
                created_at=datetime(2023, 6, 15, 10, 30, 0),
                updated_at=datetime(2023, 6, 15, 10, 30, 0)
            ),
            MembershipOrder(
                id="20230515001", 
                plan_name="月度会员",
                amount=29.9,
                date=datetime(2023, 5, 15),
                status=OrderStatus.PAID,
                user_id="test_user_001",
                created_at=datetime(2023, 5, 15, 14, 20, 0),
                updated_at=datetime(2023, 5, 15, 14, 20, 0)
            ),
            MembershipOrder(
                id="20230715001",
                plan_name="年度会员",
                amount=299.9,
                date=datetime(2023, 7, 15),
                status=OrderStatus.PENDING,
                user_id="test_user_001",
                created_at=datetime(2023, 7, 15, 9, 15, 0),
                updated_at=datetime(2023, 7, 15, 9, 15, 0)
            ),
            MembershipOrder(
                id="20230415001",
                plan_name="月度会员", 
                amount=29.9,
                date=datetime(2023, 4, 15),
                status=OrderStatus.CANCELLED,
                user_id="test_user_002",
                created_at=datetime(2023, 4, 15, 16, 45, 0),
                updated_at=datetime(2023, 4, 16, 10, 0, 0)
            )
        ]
        
        # 批量插入数据
        db.add_all(test_orders)
        db.commit()
        
        print(f"成功初始化 {len(test_orders)} 条测试订单数据")
        
        # 验证数据
        count = db.query(MembershipOrder).count()
        print(f"数据库中共有 {count} 条订单记录")
        
    except Exception as e:
        db.rollback()
        print(f"初始化测试数据失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()