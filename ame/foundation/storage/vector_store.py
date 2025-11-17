"""
向量存储 - Faiss 实现

提供高性能向量相似度检索能力

特性：
- 毫秒级语义检索
- 支持 IVF 索引（速度与精度平衡）
- 自动 ID 映射管理
- 持久化存储
- GPU 加速支持
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import pickle

import numpy as np
import faiss

from .base import StorageBase, StorageConfig

logger = logging.getLogger(__name__)


class VectorStore(StorageBase):
    """
    Faiss 向量存储实现
    
    使用 IVF (Inverted File) 索引实现快速向量检索
    """
    
    def __init__(
        self,
        dimension: int = 1536,
        index_path: Optional[str] = None,
        nlist: int = 100,
        use_gpu: bool = False
    ):
        """
        初始化向量存储
        
        Args:
            dimension: 向量维度（OpenAI ada-002: 1536）
            index_path: 索引文件路径
            nlist: IVF 聚类中心数量（建议 sqrt(N)）
            use_gpu: 是否使用 GPU 加速（需要 faiss-gpu）
        """
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        self.nlist = nlist
        self.use_gpu = use_gpu
        
        # ID 映射：faiss_id <-> doc_id
        self.id_map: Dict[int, str] = {}
        self.reverse_id_map: Dict[str, int] = {}
        
        # Faiss 索引
        self.index: Optional[faiss.Index] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化存储"""
        try:
            # 创建索引
            self.index = self._create_index()
            
            # 如果索引文件存在，加载
            if self.index_path and self.index_path.exists():
                await self._load()
            
            self._initialized = True
            logger.info(f"向量存储初始化成功 (dimension={self.dimension}, nlist={self.nlist})")
            return True
        
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}", exc_info=True)
            return False
    
    def _create_index(self) -> faiss.Index:
        """创建 Faiss IVF 索引"""
        # 量化器：用于聚类
        quantizer = faiss.IndexFlatL2(self.dimension)
        
        # IVF 索引：速度与精度平衡
        index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
        
        # GPU 加速（如果启用且可用）
        if self.use_gpu and faiss.get_num_gpus() > 0:
            try:
                res = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(res, 0, index)
                logger.info("GPU 加速已启用")
            except Exception as e:
                logger.warning(f"GPU 加速启用失败，使用 CPU: {e}")
        
        return index
    
    async def add(self, item: Dict[str, Any]) -> str:
        """
        添加向量
        
        Args:
            item: {"doc_id": str, "embedding": List[float]}
        
        Returns:
            doc_id: 文档 ID
        """
        if not self._initialized:
            await self.initialize()
        
        doc_id = item["doc_id"]
        embedding = item["embedding"]
        
        # 转换为 numpy 数组
        vector = np.array([embedding], dtype=np.float32)
        
        # 训练索引（首次添加时）
        if not self.index.is_trained:
            self.index.train(vector)
        
        # 获取新的 Faiss ID
        faiss_id = self.index.ntotal
        
        # 添加向量
        self.index.add(vector)
        
        # 更新映射
        self.id_map[faiss_id] = doc_id
        self.reverse_id_map[doc_id] = faiss_id
        
        logger.debug(f"添加向量: doc_id={doc_id}, faiss_id={faiss_id}")
        
        return doc_id
    
    async def add_batch(
        self,
        embeddings: List[List[float]],
        doc_ids: List[str]
    ) -> List[str]:
        """
        批量添加向量（性能优化）
        
        Args:
            embeddings: 向量列表
            doc_ids: 文档 ID 列表
        
        Returns:
            doc_ids: 添加的文档 ID 列表
        """
        if not self._initialized:
            await self.initialize()
        
        if len(embeddings) != len(doc_ids):
            raise ValueError("embeddings 和 doc_ids 长度不一致")
        
        # 转换为 numpy 数组
        vectors = np.array(embeddings, dtype=np.float32)
        
        # 训练索引
        if not self.index.is_trained:
            self.index.train(vectors)
        
        # 批量添加
        start_id = self.index.ntotal
        self.index.add(vectors)
        
        # 更新映射
        for i, doc_id in enumerate(doc_ids):
            faiss_id = start_id + i
            self.id_map[faiss_id] = doc_id
            self.reverse_id_map[doc_id] = faiss_id
        
        logger.info(f"批量添加 {len(doc_ids)} 个向量")
        
        return doc_ids
    
    async def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取向量（Faiss 不支持直接获取，需要重建）
        
        Args:
            item_id: 文档 ID
        
        Returns:
            None（Faiss 不支持反向查询）
        """
        # Faiss 只支持向量检索，不支持反向获取向量
        logger.warning("VectorStore 不支持 get 操作")
        return None
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新向量
        
        Faiss 不支持原地更新，需要先删除再添加
        
        Args:
            item_id: 文档 ID
            updates: {"embedding": List[float]}
        
        Returns:
            success: 是否成功
        """
        if item_id not in self.reverse_id_map:
            return False
        
        # 删除旧向量
        await self.delete(item_id)
        
        # 添加新向量
        await self.add({
            "doc_id": item_id,
            "embedding": updates["embedding"]
        })
        
        return True
    
    async def delete(self, item_id: str) -> bool:
        """
        删除向量
        
        注意：Faiss 不支持高效删除，采用标记删除策略
        当删除量达到阈值时，需要重建索引
        
        Args:
            item_id: 文档 ID
        
        Returns:
            success: 是否成功
        """
        if item_id not in self.reverse_id_map:
            return False
        
        faiss_id = self.reverse_id_map[item_id]
        
        # 从映射中删除（标记删除）
        del self.id_map[faiss_id]
        del self.reverse_id_map[item_id]
        
        logger.debug(f"删除向量（标记）: doc_id={item_id}")
        
        # TODO: 当删除量达到阈值时，自动重建索引
        deleted_ratio = (self.index.ntotal - len(self.reverse_id_map)) / max(self.index.ntotal, 1)
        if deleted_ratio > 0.3:  # 删除超过30%时重建
            logger.warning(f"删除比例过高 ({deleted_ratio:.1%})，建议重建索引")
        
        return True
    
    async def search(
        self,
        query: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        向量相似度检索
        
        Args:
            query: 查询向量
            top_k: 返回前 K 个结果
            filters: 过滤条件（暂不支持）
        
        Returns:
            results: [{"doc_id": str, "score": float, "distance": float}]
        """
        if not self._initialized or self.index.ntotal == 0:
            return []
        
        # 转换查询向量
        query_vector = np.array([query], dtype=np.float32)
        
        # 执行检索
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)
        
        # 转换结果
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1 and idx in self.id_map:
                # L2 距离转相似度分数（距离越小，分数越高）
                score = 1.0 / (1.0 + float(dist))
                results.append({
                    "doc_id": self.id_map[idx],
                    "score": score,
                    "distance": float(dist),
                    "source": "vector"
                })
        
        return results
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计向量数量"""
        return len(self.reverse_id_map)
    
    async def clear(self) -> bool:
        """清空存储"""
        try:
            self.index = self._create_index()
            self.id_map.clear()
            self.reverse_id_map.clear()
            logger.info("向量存储已清空")
            return True
        except Exception as e:
            logger.error(f"清空向量存储失败: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    async def rebuild_index(
        self,
        embeddings: List[List[float]],
        doc_ids: List[str]
    ):
        """
        重建索引（删除累积后使用）
        
        Args:
            embeddings: 有效向量列表
            doc_ids: 有效文档 ID 列表
        """
        logger.info(f"开始重建索引 (vectors={len(embeddings)})")
        
        # 清空旧索引
        self.index = self._create_index()
        self.id_map.clear()
        self.reverse_id_map.clear()
        
        # 批量添加
        await self.add_batch(embeddings, doc_ids)
        
        logger.info("索引重建完成")
    
    async def save(self):
        """保存索引到磁盘"""
        if not self.index_path:
            raise ValueError("未设置 index_path")
        
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存 Faiss 索引
            faiss.write_index(self.index, str(self.index_path))
            
            # 保存 ID 映射
            mapping_path = self.index_path.with_suffix(".mapping")
            with open(mapping_path, "wb") as f:
                pickle.dump({
                    "id_map": self.id_map,
                    "reverse_id_map": self.reverse_id_map
                }, f)
            
            logger.info(f"索引已保存: {self.index_path}")
        
        except Exception as e:
            logger.error(f"保存索引失败: {e}", exc_info=True)
            raise
    
    async def _load(self):
        """从磁盘加载索引"""
        if not self.index_path or not self.index_path.exists():
            raise FileNotFoundError(f"索引文件不存在: {self.index_path}")
        
        try:
            # 加载 Faiss 索引
            self.index = faiss.read_index(str(self.index_path))
            
            # 加载 ID 映射
            mapping_path = self.index_path.with_suffix(".mapping")
            if mapping_path.exists():
                with open(mapping_path, "rb") as f:
                    data = pickle.load(f)
                    self.id_map = data["id_map"]
                    self.reverse_id_map = data["reverse_id_map"]
            
            logger.info(f"索引已加载: {self.index_path} (vectors={self.index.ntotal})")
        
        except Exception as e:
            logger.error(f"加载索引失败: {e}", exc_info=True)
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "is_trained": self.index.is_trained if self.index else False,
            "active_docs": len(self.reverse_id_map),
            "deleted_docs": (self.index.ntotal if self.index else 0) - len(self.reverse_id_map),
            "deletion_ratio": (
                ((self.index.ntotal if self.index else 0) - len(self.reverse_id_map)) / 
                max(self.index.ntotal if self.index else 1, 1)
            ),
            "use_gpu": self.use_gpu,
            "nlist": self.nlist
        }
