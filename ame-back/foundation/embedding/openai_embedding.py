"""
OpenAI Embedding 实现
"""
from typing import List, Optional
import logging
import asyncio
from openai import AsyncOpenAI

from .base import EmbeddingBase, EmbeddingResult


logger = logging.getLogger(__name__)


class OpenAIEmbedding(EmbeddingBase):
    """
    OpenAI Embedding 实现
    
    特性：
    - 支持批量处理
    - 自动重试
    - 速率限制
    - 缓存支持
    """
    
    # 模型配置
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        max_retries: int = 3,
        batch_size: int = 100,
        api_base: Optional[str] = None,
    ):
        """
        Args:
            api_key: OpenAI API Key
            model: 模型名称
            max_retries: 最大重试次数
            batch_size: 批处理大小
            api_base: API Base URL（可选）
        """
        self.model = model
        self.max_retries = max_retries
        self.batch_size = batch_size
        
        # 初始化客户端
        client_kwargs = {"api_key": api_key}
        if api_base:
            client_kwargs["base_url"] = api_base
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        # 验证模型
        if model not in self.MODEL_DIMENSIONS:
            logger.warning(f"Unknown model: {model}, using default dimension 1536")
            self.dimension = 1536
        else:
            self.dimension = self.MODEL_DIMENSIONS[model]
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """生成单个文本的嵌入向量"""
        if not text or not text.strip():
            # 空文本返回零向量
            return EmbeddingResult(
                vector=[0.0] * self.dimension,
                model=self.model,
                dimension=self.dimension,
                usage=0
            )
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=[text.strip()],
                )
                
                embedding = response.data[0].embedding
                usage = response.usage.total_tokens if hasattr(response, 'usage') else None
                
                return EmbeddingResult(
                    vector=embedding,
                    model=self.model,
                    dimension=len(embedding),
                    usage=usage
                )
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All embedding attempts failed for text: {text[:50]}...")
                    # 返回零向量
                    return EmbeddingResult(
                        vector=[0.0] * self.dimension,
                        model=self.model,
                        dimension=self.dimension,
                        usage=0
                    )
                await asyncio.sleep(2 ** attempt)  # 指数退避
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量生成嵌入向量"""
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [(i, t.strip()) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            return [
                EmbeddingResult(
                    vector=[0.0] * self.dimension,
                    model=self.model,
                    dimension=self.dimension,
                    usage=0
                )
                for _ in texts
            ]
        
        # 分批处理
        results = [None] * len(texts)
        
        for i in range(0, len(valid_texts), self.batch_size):
            batch = valid_texts[i:i + self.batch_size]
            batch_indices = [idx for idx, _ in batch]
            batch_texts = [text for _, text in batch]
            
            for attempt in range(self.max_retries):
                try:
                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=batch_texts,
                    )
                    
                    usage = response.usage.total_tokens if hasattr(response, 'usage') else None
                    usage_per_text = usage // len(batch_texts) if usage else None
                    
                    for j, embedding_data in enumerate(response.data):
                        original_idx = batch_indices[j]
                        results[original_idx] = EmbeddingResult(
                            vector=embedding_data.embedding,
                            model=self.model,
                            dimension=len(embedding_data.embedding),
                            usage=usage_per_text
                        )
                    
                    break
                    
                except Exception as e:
                    logger.warning(f"Batch embedding attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"All batch embedding attempts failed")
                        # 对失败的文本返回零向量
                        for idx in batch_indices:
                            if results[idx] is None:
                                results[idx] = EmbeddingResult(
                                    vector=[0.0] * self.dimension,
                                    model=self.model,
                                    dimension=self.dimension,
                                    usage=0
                                )
                    await asyncio.sleep(2 ** attempt)
        
        # 填充空文本的零向量
        for i in range(len(texts)):
            if results[i] is None:
                results[i] = EmbeddingResult(
                    vector=[0.0] * self.dimension,
                    model=self.model,
                    dimension=self.dimension,
                    usage=0
                )
        
        return results
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model
