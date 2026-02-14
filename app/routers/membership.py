from fastapi import APIRouter, Depends
from app.models.schemas import BaseResponse
from app.services.auth import auth_service
from typing import Dict, Any
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/memberships", tags=["memberships"])

class PaymentRequest(BaseModel):
    planId: str

@router.get("/me", response_model=BaseResponse)
async def get_membership_info(current_user: Dict[str, Any] = Depends(auth_service.get_current_user)):
    """获取会员信息"""
    # 在测试模式下，返回模拟的会员信息
    # TODO
    membership_data = {
        "level": "free",
        "levelName": "普通会员",
        "expireDate": None,
        "features": ["基础卡片流", "基础 AI 分身", "基础触发条件"]
    }
    
    return BaseResponse(
        code=0,
        message="success",
        data=membership_data
    )

@router.post("/orders", response_model=BaseResponse)
async def create_membership_payment(
    request: PaymentRequest,
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """创建会员支付"""
    import time
    import hashlib
    import random
    import string
    
    # 生成订单ID
    order_id = f"order_{uuid.uuid4().hex[:16]}"
    
    # 生成微信支付所需参数
    timestamp = str(int(time.time()))
    nonce_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # 模拟prepay_id（实际应该调用微信统一下单接口获取）
    prepay_id = f"wx{int(time.time())}{random.randint(1000, 9999)}"
    package = f"prepay_id={prepay_id}"
    
    # 生成签名（简化版本，实际应该按微信支付签名规则）
    sign_string = f"appId=your_app_id&nonceStr={nonce_str}&package={package}&signType=MD5&timeStamp={timestamp}&key=your_api_key"
    pay_sign = hashlib.md5(sign_string.encode()).hexdigest().upper()
    
    # 在测试模式下，返回模拟的支付信息
    payment_data = {
        "orderId": order_id,
        "amount": 30.00,
        "status": "pending",
        "paymentUrl": "https://example.com/payment",
        # 微信支付参数
        "wxPayParams": {
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "MD5",
            "paySign": pay_sign
        }
    }
    
    return BaseResponse(
        code=0,
        message="success",
        data=payment_data
    )