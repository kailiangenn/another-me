"""
Embedding数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class EmbeddingResult:
    """Embedding结果"""
    vector: List[float]                    # 向量
    dimension: int                         # 维度
    model: str                             # 使用的模型
    usage: Optional[Dict[str, int]] = None # Token使用情况
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据"""
        if len(self.vector) != self.dimension:
            raise ValueError(
                f"向量长度({len(self.vector)})与维度({self.dimension})不匹配"
            )


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    model: str = "text-embedding-ada-002"  # 模型名称
    dimension: int = 1536                  # 向量维度
    batch_size: int = 100                  # 批量处理大小
    max_retries: int = 3                   # 最大重试次数
    timeout: int = 30                      # 超时时间(秒)
    api_base: Optional[str] = None         # API地址
    api_key: Optional[str] = None          # API密钥
    metadata: Dict[str, Any] = field(default_factory=dict)
