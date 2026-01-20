from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import user_card, users, auth, membership, membership_orders, scenes, file, llm, chats, topic_cards, user_connections, vote_cards, feed, content_moderation, points
from app.routers.user_profile import router as user_profile_router

from app.utils.db_init import init_db
from app.config import settings
import os

# 初始化应用
app = FastAPI(
    title="Vive Agent API",
    description="Vive Agent Backend API for WeChat Mini Program",
    version="0.1.0",
)

# 添加CORS中间件支持前后端联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 确保上传目录存在并挂载静态文件
upload_path = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(upload_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

# 包含路由
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(scenes.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(membership.router, prefix="/api/v1")
app.include_router(membership_orders.router, prefix="/api/v1")
app.include_router(file.router, prefix="/files")
# 话题卡片路由（需要在通配符路由之前注册，避免被拦截）
app.include_router(topic_cards.router, prefix="/api/v1/topic-cards")
# 用户连接路由（需要在通配符路由之前注册，避免被拦截）
app.include_router(user_connections.router, prefix="/api/v1/user-connections")
app.include_router(user_card.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")


# 用户画像系统路由（包含所有画像相关功能）
app.include_router(user_profile_router, prefix="/api/v1")


app.include_router(chats.router, prefix="/api/v1")



# 投票卡片路由
app.include_router(vote_cards.router, prefix="/api/v1/vote-cards")

# 统一卡片流路由
app.include_router(feed.router, prefix="/api/v1/feed")

# 内容审核路由
app.include_router(content_moderation.router, prefix="/api/v1/content-moderation")

# 积分管理路由
app.include_router(points.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to Vive Agent API"}

@app.get("/api/v1")
def api_info():
    return {
        "version": "2.0.0",
        "design": "RESTful",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "files": "/api/v1/files"
        }
    }

@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "vive-agent-backend",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Vive Agent Backend Server")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务器主机 (默认: 0.0.0.0)")
    
    # 解析参数
    args = parser.parse_args()
    
    print(f"🚀 启动服务器: {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)