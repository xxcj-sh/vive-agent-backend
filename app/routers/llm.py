"""
大语言模型API路由
提供LLM相关的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.config import settings

from app.database import get_db
from app.services.auth import auth_service
from app.services.llm_service import LLMService

router = APIRouter(prefix="/llm", tags=["大语言模型"])