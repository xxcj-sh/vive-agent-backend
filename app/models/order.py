from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class OrderStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class MembershipOrder(Base):
    __tablename__ = "membership_orders"
    
    id = Column(String(36), primary_key=True)
    plan_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    user_id = Column(String(36), nullable=False)  # 关联用户ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        status_text_map = {
            OrderStatus.PENDING: "待支付",
            OrderStatus.PAID: "已支付", 
            OrderStatus.CANCELLED: "已取消",
            OrderStatus.REFUNDED: "已退款"
        }
        
        return {
            "id": self.id,
            "planName": self.plan_name,
            "amount": self.amount,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
            "status": self.status.value if self.status else None,
            "statusText": status_text_map.get(self.status, "未知状态")
        }