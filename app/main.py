from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import users, match, auth, membership, membership_orders, scenes, file, properties, chat, enhanced_match
from app.routers.profile_by_id import router as profile_by_id_router
from app.utils.db_init import init_db
from app.config import settings
import os

# 初始化应用
app = FastAPI(
    title="VMatch API",
    description="VMatch Backend API for WeChat Mini Program",
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
app.include_router(match.router, prefix="/api/v1/matches")
app.include_router(chat.router, prefix="/api/v1")

app.include_router(membership.router, prefix="/api/v1")
app.include_router(membership_orders.router, prefix="/api/v1")
app.include_router(file.router, prefix="/api/v1/files")
app.include_router(properties.router, prefix="/api/v1")
app.include_router(router=profile_by_id_router, prefix="/api/v1")
app.include_router(enhanced_match.router, prefix="/api/v1/enhanced-match", tags=["enhanced-match"])

@app.get("/")
def read_root():
    return {"message": "Welcome to VMatch API"}

@app.get("/api/v1")
def api_info():
    return {
        "version": "2.0.0",
        "design": "RESTful",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "matches": "/api/v1/matches",
            "messages": "/api/v1/messages",
            "files": "/api/v1/files"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)