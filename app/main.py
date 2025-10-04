from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import card, users, matches, auth, membership, membership_orders, scenes, file, properties, llm, user_profile
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
app.include_router(matches.router, prefix="/api/v1")
app.include_router(membership.router, prefix="/api/v1")
app.include_router(membership_orders.router, prefix="/api/v1")
app.include_router(file.router, prefix="/files")
app.include_router(properties.router, prefix="/api/v1")
app.include_router(card.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(user_profile.router, prefix="/api/v1")

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
            "matcheses": "/api/v1/matcheses",
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
    uvicorn.run(app, host="0.0.0.0", port=8000)