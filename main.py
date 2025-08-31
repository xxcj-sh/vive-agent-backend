from fastapi import FastAPI
from app.routers import membership_orders, match
from app.database import engine
from app.models.order import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VMatch Backend API",
    description="微信小程序后端API服务",
    version="1.0.0"
)

# 注册路由
app.include_router(membership_orders.router)
app.include_router(match.router, prefix="/api/v1/matches", tags=["matches"])

@app.get("/")
async def root():
    return {"message": "VMatch Backend API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)