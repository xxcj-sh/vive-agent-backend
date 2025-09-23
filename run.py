#!/usr/bin/env python3
"""
WeMatch 微信小程序服务端启动脚本
"""
import uvicorn
import os
import sys

def main():
    """启动应用"""
    print("🚀 启动 VMatch Backend 服务...")
    print("📱 支持微信小程序登录注册")
    print("🔐 开发阶段固定验证码: 123456")
    print("🌐 服务地址: http://0.0.0.0:8000")
    print("📚 API文档: http://0.0.0.0:8000/docs")
    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # 启动FastAPI应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()