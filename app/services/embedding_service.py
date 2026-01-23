"""
用户画像向量嵌入服务
提供用户画像语义向量生成功能，使用豆包模型生成1024维向量
"""

import json
import asyncio
from typing import Optional, List
import httpx
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """用户画像向量嵌入服务类"""

    def __init__(self):
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"
        self.model_name = "doubao-embedding-vision-251215"
        self.vector_dimension = 1024
        self.encoding_format = "float"
        self.timeout = 30.0

    async def generate_profile_embedding(self, text: str) -> Optional[str]:
        """
        生成用户画像文本的语义向量

        Args:
            text: 用户画像文本内容

        Returns:
            向量字符串，格式为 '[0.1, 0.2, ...]'
        """
        if not text or not text.strip():
            logger.warning("输入文本为空，无法生成向量")
            return None

        try:
            api_key = settings.LLM_API_KEY
            if not api_key:
                logger.error("未配置 LLM_API_KEY，无法调用豆包向量模型")
                return None

            payload = {
                "model": self.model_name,
                "input": [
                    {
                        "type": "text",
                        "text": text
                    }
                ],
                "dimensions": self.vector_dimension,
                "encoding_format": self.encoding_format
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"豆包向量模型调用失败: {response.status_code} - {response.text}")
                    return None

                result = response.json()

                if result.get("data") and len(result["data"]) > 0:
                    embedding = result["data"][0].get("embedding")
                    if embedding:
                        vector_str = self._format_vector(embedding)
                        logger.info(f"成功生成用户画像向量，维度: {len(embedding)}")
                        return vector_str

                logger.warning("豆包向量模型返回数据为空")
                return None

        except httpx.TimeoutException:
            logger.error("豆包向量模型调用超时")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析豆包向量模型响应失败: {e}")
            return None
        except Exception as e:
            logger.error(f"生成用户画像向量时发生错误: {e}")
            return None

    def _format_vector(self, embedding: List[float]) -> str:
        """
        格式化向量为字符串

        Args:
            embedding: 向量列表

        Returns:
            格式化的向量字符串
        """
        return json.dumps(embedding, ensure_ascii=False)

    async def generate_embedding_with_retry(
        self,
        text: str,
        max_retries: int = 2,
        retry_delay: float = 1.0
    ) -> Optional[str]:
        """
        带重试机制的向量生成

        Args:
            text: 用户画像文本内容
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            向量字符串
        """
        for attempt in range(max_retries):
            embedding = await self.generate_profile_embedding(text)
            if embedding:
                return embedding

            if attempt < max_retries - 1:
                logger.warning(f"向量生成失败，{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)

        logger.error(f"向量生成失败，已重试 {max_retries} 次")
        return None


embedding_service = EmbeddingService()
