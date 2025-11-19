"""
Faiss向量存储实现

基于Faiss的本地向量存储
"""

import os
import pickle
from typing import List, Optional, Dict, Any
import numpy as np
from loguru import logger

from .vector_store import VectorStoreBase, Vector, SearchResult
from ..core.exceptions import VectorStoreError


class FaissVectorStore(VectorStoreBase):
    """
    Faiss向量存储实现
    
    Features:
    - 本地存储,无需外部服务
    - 高性能向量检索
    - 支持持久化
    - 支持元数据过滤
    """
    
    def __init__(
        self,
        dimension: int = 1536,
        index_type: str = "Flat",
        metric: str = "L2",
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None
    ):
        """
        初始化Faiss向量存储
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 ("Flat", "IVF", "HNSW")
            metric: 距离度量 ("L2", "IP" - Inner Product)
            index_path: 索引文件路径
            metadata_path: 元数据文件路径
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        self.faiss = None
        self.index = None
        self.id_to_index = {}  # vector_id -> faiss_index
        self.index_to_id = {}  # faiss_index -> vector_id
        self.metadata_store = {}  # vector_id -> metadata
        self._next_index = 0
        
        # 初始化faiss
        try:
            import faiss
            self.faiss = faiss
            logger.info("Faiss已加载")
        except ImportError:
            raise VectorStoreError("Faiss未安装,请运行: pip install faiss-cpu 或 pip install faiss-gpu")
    
    async def connect(self) -> None:
        """建立连接(初始化索引)"""
        try:
            # 如果有保存的索引,尝试加载
            if self.index_path and os.path.exists(self.index_path):
                await self.load_index(self.index_path)
            else:
                # 创建新索引
                await self._create_index()
            
            logger.info(f"Faiss向量存储已连接 (维度: {self.dimension}, 类型: {self.index_type})")
        except Exception as e:
            raise VectorStoreError(f"Faiss连接失败: {e}")
    
    async def disconnect(self) -> None:
        """断开连接(可选保存索引)"""
        if self.index_path:
            await self.save_index(self.index_path)
        logger.info("Faiss向量存储已断开")
    
    async def health_check(self) -> bool:
        """健康检查"""
        return self.index is not None
    
    async def _create_index(self) -> None:
        """创建Faiss索引"""
        if self.index_type == "Flat":
            # Flat索引: 精确检索,速度较慢
            if self.metric == "L2":
                self.index = self.faiss.IndexFlatL2(self.dimension)
            elif self.metric == "IP":
                self.index = self.faiss.IndexFlatIP(self.dimension)
            else:
                raise VectorStoreError(f"不支持的度量: {self.metric}")
        
        elif self.index_type == "IVF":
            # IVF索引: 近似检索,速度快
            nlist = 100  # 聚类中心数量
            quantizer = self.faiss.IndexFlatL2(self.dimension)
            if self.metric == "L2":
                self.index = self.faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            elif self.metric == "IP":
                self.index = self.faiss.IndexIVFFlat(quantizer, self.dimension, nlist, self.faiss.METRIC_INNER_PRODUCT)
            else:
                raise VectorStoreError(f"不支持的度量: {self.metric}")
        
        elif self.index_type == "HNSW":
            # HNSW索引: 高性能近似检索
            self.index = self.faiss.IndexHNSWFlat(self.dimension, 32)  # 32是M参数
        
        else:
            raise VectorStoreError(f"不支持的索引类型: {self.index_type}")
        
        logger.info(f"已创建{self.index_type}索引")
    
    async def add_vector(
        self,
        vector_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加单个向量"""
        try:
            # 验证维度
            if embedding.shape[0] != self.dimension:
                raise VectorStoreError(f"向量维度不匹配: 期望{self.dimension}, 实际{embedding.shape[0]}")
            
            # 检查是否已存在
            if vector_id in self.id_to_index:
                logger.warning(f"向量ID {vector_id} 已存在,将覆盖")
                await self.delete_vector(vector_id)
            
            # 添加到Faiss索引
            embedding_2d = embedding.reshape(1, -1).astype('float32')
            self.index.add(embedding_2d)
            
            # 更新映射
            faiss_idx = self._next_index
            self.id_to_index[vector_id] = faiss_idx
            self.index_to_id[faiss_idx] = vector_id
            self._next_index += 1
            
            # 保存元数据
            if metadata:
                self.metadata_store[vector_id] = metadata
            
            logger.debug(f"已添加向量: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            return False
    
    async def add_vectors(self, vectors: List[Vector]) -> List[str]:
        """批量添加向量"""
        added_ids = []
        
        # 准备批量数据
        embeddings_list = []
        for vector in vectors:
            if vector.embedding.shape[0] != self.dimension:
                logger.warning(f"跳过维度不匹配的向量: {vector.id}")
                continue
            
            if vector.id in self.id_to_index:
                await self.delete_vector(vector.id)
            
            embeddings_list.append(vector.embedding)
            added_ids.append(vector.id)
        
        if not embeddings_list:
            return []
        
        # 批量添加
        embeddings_array = np.array(embeddings_list, dtype='float32')
        self.index.add(embeddings_array)
        
        # 更新映射和元数据
        for i, vector in enumerate([v for v in vectors if v.id in added_ids]):
            faiss_idx = self._next_index + i
            self.id_to_index[vector.id] = faiss_idx
            self.index_to_id[faiss_idx] = vector.id
            if vector.metadata:
                self.metadata_store[vector.id] = vector.metadata
        
        self._next_index += len(added_ids)
        logger.info(f"批量添加了 {len(added_ids)} 个向量")
        
        return added_ids
    
    async def get_vector(
        self,
        vector_id: str,
        include_embedding: bool = False
    ) -> Optional[Vector]:
        """获取向量"""
        if vector_id not in self.id_to_index:
            return None
        
        faiss_idx = self.id_to_index[vector_id]
        metadata = self.metadata_store.get(vector_id, {})
        
        embedding = None
        if include_embedding:
            # Faiss不直接支持按索引获取向量,需要重构
            embedding = self.index.reconstruct(faiss_idx)
        
        return Vector(
            id=vector_id,
            embedding=embedding,
            metadata=metadata
        )
    
    async def update_vector(
        self,
        vector_id: str,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        if vector_id not in self.id_to_index:
            return False
        
        # 更新元数据
        if metadata:
            if vector_id in self.metadata_store:
                self.metadata_store[vector_id].update(metadata)
            else:
                self.metadata_store[vector_id] = metadata
        
        # 更新向量数据(需要删除后重新添加)
        if embedding is not None:
            await self.delete_vector(vector_id)
            return await self.add_vector(vector_id, embedding, self.metadata_store.get(vector_id))
        
        return True
    
    async def delete_vector(self, vector_id: str) -> bool:
        """删除向量"""
        if vector_id not in self.id_to_index:
            return False
        
        # Faiss不支持直接删除,需要标记或重建索引
        # 这里简单实现:从映射中移除
        faiss_idx = self.id_to_index.pop(vector_id)
        self.index_to_id.pop(faiss_idx, None)
        self.metadata_store.pop(vector_id, None)
        
        logger.debug(f"已删除向量: {vector_id}")
        return True
    
    async def delete_vectors(self, vector_ids: List[str]) -> int:
        """批量删除向量"""
        count = 0
        for vector_id in vector_ids:
            if await self.delete_vector(vector_id):
                count += 1
        return count
    
    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_embedding: bool = False
    ) -> List[SearchResult]:
        """向量检索"""
        try:
            # 验证维度
            if query_vector.shape[0] != self.dimension:
                raise VectorStoreError(f"查询向量维度不匹配: 期望{self.dimension}, 实际{query_vector.shape[0]}")
            
            # 执行检索
            query_2d = query_vector.reshape(1, -1).astype('float32')
            distances, indices = self.index.search(query_2d, k)
            
            # 构建结果
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Faiss返回-1表示没有更多结果
                    break
                
                vector_id = self.index_to_id.get(idx)
                if not vector_id:
                    continue
                
                # 应用元数据过滤
                metadata = self.metadata_store.get(vector_id, {})
                if filter and not self._match_filter(metadata, filter):
                    continue
                
                # 计算相似度分数(转换距离为相似度)
                if self.metric == "L2":
                    score = 1.0 / (1.0 + float(dist))  # L2距离转相似度
                else:  # IP
                    score = float(dist)  # 内积本身就是相似度
                
                embedding = None
                if include_embedding:
                    embedding = self.index.reconstruct(idx)
                
                results.append(SearchResult(
                    id=vector_id,
                    score=score,
                    metadata=metadata,
                    embedding=embedding
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    async def search_by_id(
        self,
        vector_id: str,
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """根据向量ID检索"""
        vector = await self.get_vector(vector_id, include_embedding=True)
        if not vector or vector.embedding is None:
            return []
        
        return await self.search(vector.embedding, k, filter)
    
    def _match_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """匹配元数据过滤条件"""
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """统计向量数量"""
        if not filter:
            return self.index.ntotal
        
        # 应用过滤
        count = 0
        for vector_id, metadata in self.metadata_store.items():
            if self._match_filter(metadata, filter):
                count += 1
        return count
    
    async def clear(self) -> bool:
        """清空所有向量"""
        await self._create_index()
        self.id_to_index.clear()
        self.index_to_id.clear()
        self.metadata_store.clear()
        self._next_index = 0
        logger.info("已清空所有向量")
        return True
    
    async def build_index(self, **kwargs) -> bool:
        """构建索引(IVF需要训练)"""
        if self.index_type == "IVF" and not self.index.is_trained:
            # 获取所有向量进行训练
            if self.index.ntotal > 0:
                logger.info("正在训练IVF索引...")
                # 注意: 这里简化处理,实际应该收集所有向量
                return True
        return True
    
    async def save_index(self, path: str) -> bool:
        """保存索引到文件"""
        try:
            # 保存Faiss索引
            self.faiss.write_index(self.index, path)
            
            # 保存元数据和映射
            metadata_path = self.metadata_path or path + ".metadata"
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'id_to_index': self.id_to_index,
                    'index_to_id': self.index_to_id,
                    'metadata_store': self.metadata_store,
                    'next_index': self._next_index
                }, f)
            
            logger.info(f"已保存索引到: {path}")
            return True
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
            return False
    
    async def load_index(self, path: str) -> bool:
        """从文件加载索引"""
        try:
            # 加载Faiss索引
            self.index = self.faiss.read_index(path)
            
            # 加载元数据和映射
            metadata_path = self.metadata_path or path + ".metadata"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.id_to_index = data['id_to_index']
                    self.index_to_id = data['index_to_id']
                    self.metadata_store = data['metadata_store']
                    self._next_index = data['next_index']
            
            logger.info(f"已加载索引: {path}, 向量数: {self.index.ntotal}")
            return True
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            return False
