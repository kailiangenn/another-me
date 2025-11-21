# AME模块后续优化规划

## 当前状态分析

### 已完成(P0基础能力)
- ✅ Foundation Layer: LLM/Embedding/Storage/File/NLP基础模块
- ✅ Capability Layer: Life/Work两大场景的核心能力
- ✅ Service Layer: Work场景的3个服务(Project/Todo/Advice)
- ✅ 基础测试覆盖

### 优化方向
1. **Foundation Layer增强**: 更强大的NLP/Embedding能力
2. **Capability Layer完善**: 混合检索、上下文管理优化
3. **Service Layer扩展**: Life场景服务实现
4. **系统集成**: 跨层能力整合、性能优化

---

## 短期优化计划(迭代2.1)

### 1. Foundation Layer增强

#### 1.1 NLP模块 - spaCy中文NER后端

**功能描述**
- 基于spaCy的中文命名实体识别
- 支持人名、地名、机构名、时间、数字等实体类型
- 替代或补充现有的规则提取器

**基类依赖**
```python
from ame.foundation.nlp.entity_extractor import EntityExtractorBase, Entity, EntityType
from typing import List, Optional
```

**实现位置**
`ame/foundation/nlp/spacy_extractor.py`

**类定义**
```python
class SpacyEntityExtractor(EntityExtractorBase):
    """基于spaCy的中文NER后端"""
    
    def __init__(self, model_name: str = "zh_core_web_sm"):
        """初始化spaCy模型"""
        
    def extract(self, text: str, entity_types: Optional[List[EntityType]] = None) -> List[Entity]:
        """提取命名实体
        
        输入:
            text: str - 待提取文本
            entity_types: Optional[List[EntityType]] - 指定实体类型,None则提取所有
        
        输出:
            List[Entity] - 实体列表
                Entity.text: str - 实体文本
                Entity.type: EntityType - 实体类型
                Entity.start: int - 起始位置
                Entity.end: int - 结束位置
                Entity.confidence: float - 置信度
        """
```

**配置管理**
```python
# ame/foundation/nlp/extractor_factory.py
class EntityExtractorFactory:
    @staticmethod
    def create(backend: str = "rule") -> EntityExtractorBase:
        """创建实体提取器
        
        输入:
            backend: str - "rule" | "spacy" | "hybrid"
        
        输出:
            EntityExtractorBase实例
        """
```

---

#### 1.2 Intent模块 - 分层意图识别

**功能描述**
- 支持粗粒度意图(comfort/query_self/analyze/chat)和细粒度子意图
- 返回意图层级结构,便于针对性处理
- 提高复杂场景下的意图识别准确度

**基类依赖**
```python
from ame.foundation.nlp.intent_recognizer import IntentRecognizerBase, IntentResult, IntentType
from typing import Optional
from dataclasses import dataclass
```

**实现位置**
`ame/foundation/nlp/intent_recognizer.py` (增强现有类)

**数据结构**
```python
@dataclass
class HierarchicalIntentResult:
    """分层意图识别结果"""
    primary_intent: IntentType  # 主意图
    sub_intent: Optional[str]   # 子意图
    confidence: float           # 置信度
    context: dict              # 上下文信息
```

**方法增强**
```python
class IntentRecognizerBase:
    def recognize_hierarchical(self, text: str) -> HierarchicalIntentResult:
        """分层意图识别
        
        输入:
            text: str - 用户输入
        
        输出:
            HierarchicalIntentResult
                primary_intent: IntentType - COMFORT/QUERY_SELF/ANALYZE/CHAT等
                sub_intent: Optional[str] - "情绪安慰"/"记忆查询"/"工作分析"等
                confidence: float - 0.0~1.0
                context: dict - {"keywords": [...], "entities": [...]}
        """
```

**子意图定义示例**
```python
COMFORT_SUB_INTENTS = ["情绪安慰", "鼓励支持", "压力缓解"]
QUERY_SELF_SUB_INTENTS = ["记忆查询", "习惯查询", "偏好查询"]
ANALYZE_SUB_INTENTS = ["工作分析", "效率分析", "模式识别"]
```

---

#### 1.3 NLP模块 - 多级别摘要

**功能描述**
- 支持不同详细程度的摘要(极简/简短/标准/详细)
- 保留关键信息的同时适应不同场景需求
- 支持结构化摘要输出

**基类依赖**
```python
from ame.foundation.nlp.summarizer import SummarizerBase
from typing import List, Dict, Any
from enum import Enum
```

**实现位置**
`ame/foundation/nlp/summarizer.py` (增强现有类)

**枚举定义**
```python
class SummaryLevel(Enum):
    """摘要级别"""
    MINIMAL = "minimal"      # 一句话(20-30字)
    BRIEF = "brief"          # 简短(50-100字)
    STANDARD = "standard"    # 标准(150-250字)
    DETAILED = "detailed"    # 详细(300-500字)
```

**数据结构**
```python
@dataclass
class EnhancedSummary:
    """增强摘要结果"""
    level: SummaryLevel          # 摘要级别
    text: str                    # 摘要文本
    key_points: List[str]        # 关键要点
    metadata: Dict[str, Any]     # 元数据(字数/时间等)
```

**方法增强**
```python
class SummarizerBase:
    def summarize_multilevel(
        self, 
        text: str,
        levels: List[SummaryLevel] = None
    ) -> Dict[SummaryLevel, EnhancedSummary]:
        """多级别摘要生成
        
        输入:
            text: str - 原文
            levels: List[SummaryLevel] - 需要的摘要级别,None则生成所有级别
        
        输出:
            Dict[SummaryLevel, EnhancedSummary]
                key: SummaryLevel枚举
                value: EnhancedSummary对象
        """
```

---

#### 1.4 Embedding模块 - Transformer后端

**功能描述**
- 基于HuggingFace Transformers的高质量向量化
- 支持多种中文预训练模型(text2vec-base-chinese等)
- 提供批量编码和缓存机制

**基类依赖**
```python
from ame.foundation.embedding.base import EmbeddingBase
from typing import List, Optional
import numpy as np
```

**实现位置**
`ame/foundation/embedding/transformer_embedding.py`

**类定义**
```python
class TransformerEmbedding(EmbeddingBase):
    """基于Transformer的向量化"""
    
    def __init__(
        self, 
        model_name: str = "shibing624/text2vec-base-chinese",
        device: str = "cpu",
        batch_size: int = 32
    ):
        """初始化Transformer模型"""
    
    def embed_single(self, text: str) -> np.ndarray:
        """单文本向量化
        
        输入:
            text: str - 待编码文本
        
        输出:
            np.ndarray - shape (embedding_dim,), 默认768维
        """
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """批量向量化
        
        输入:
            texts: List[str] - 文本列表
        
        输出:
            List[np.ndarray] - 向量列表,每个shape (embedding_dim,)
        """
    
    def get_dimension(self) -> int:
        """获取向量维度,返回768"""
```

**配置管理**
```python
# ame/foundation/embedding/factory.py
class EmbeddingFactory:
    @staticmethod
    def create(backend: str = "simple") -> EmbeddingBase:
        """创建Embedding实例
        
        输入:
            backend: str - "simple" | "transformer" | "openai"
        
        输出:
            EmbeddingBase实例
        """
```

---

### 2. Capability Layer完善

#### 2.1 ContextRetriever - 混合检索优化

**功能描述**
- 融合向量检索(语义相似)和关键词检索(精确匹配)
- 支持时间衰减、重要性加权
- 多路召回+重排序策略

**基类依赖**
```python
from ame.foundation.storage.vector_store import VectorStore
from ame.foundation.embedding.base import EmbeddingBase
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
```

**实现位置**
`ame/capability/life/context_retriever.py` (增强现有类)

**数据结构**
```python
@dataclass
class RetrievalConfig:
    """检索配置"""
    vector_weight: float = 0.6      # 向量检索权重
    keyword_weight: float = 0.3     # 关键词权重
    time_decay_weight: float = 0.1  # 时间衰减权重
    top_k: int = 5                  # 返回数量
    time_decay_days: int = 30       # 时间衰减周期
```

**方法增强**
```python
class ContextRetriever:
    def hybrid_retrieve(
        self,
        query: str,
        config: RetrievalConfig = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """混合检索
        
        输入:
            query: str - 查询文本
            config: RetrievalConfig - 检索配置
            filters: Optional[Dict] - 过滤条件 {"user_id": "xxx", "tags": ["work"]}
        
        输出:
            List[Dict] - 检索结果列表
                [{
                    "content": str,           # 内容
                    "score": float,           # 综合得分
                    "vector_score": float,    # 向量得分
                    "keyword_score": float,   # 关键词得分
                    "time_score": float,      # 时间得分
                    "timestamp": str,         # 时间戳
                    "metadata": dict          # 元数据
                }]
        """
```

---

### 3. Service Layer扩展

#### 3.1 LifeDialogueService - 对话服务

**功能描述**
- Life场景的完整对话流程服务
- 集成意图识别、上下文检索、对话生成
- 支持多轮对话状态管理

**依赖模块**
```python
from ame.capability.life.life_intent_recognizer import LifeIntentRecognizer
from ame.capability.life.context_retriever import ContextRetriever
from ame.capability.life.dialogue_generator import DialogueGenerator
from typing import Dict, Any, Optional
```

**实现位置**
`ame/service/life/dialogue_service.py`

**类定义**
```python
class LifeDialogueService:
    """Life场景对话服务"""
    
    def __init__(
        self,
        intent_recognizer: LifeIntentRecognizer,
        context_retriever: ContextRetriever,
        dialogue_generator: DialogueGenerator
    ):
        """初始化服务"""
    
    def process_dialogue(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理对话请求
        
        输入:
            user_input: str - 用户输入
            user_id: str - 用户ID
            session_id: Optional[str] - 会话ID
        
        输出:
            {
                "response": str,              # 回复内容
                "intent": str,                # 识别的意图
                "confidence": float,          # 置信度
                "context_used": List[Dict],   # 使用的上下文
                "session_id": str             # 会话ID
            }
        """
```

---

#### 3.2 LifeMemoryService - 记忆服务

**功能描述**
- Life场景的个人记忆存储与查询
- 支持自动记忆提取、手动记忆添加
- 提供记忆统计和分析

**依赖模块**
```python
from ame.foundation.storage.vector_store import VectorStore
from ame.foundation.embedding.base import EmbeddingBase
from ame.foundation.nlp.entity_extractor import EntityExtractorBase
from typing import List, Dict, Any
```

**实现位置**
`ame/service/life/memory_service.py`

**类定义**
```python
class LifeMemoryService:
    """Life场景记忆服务"""
    
    def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """添加记忆
        
        输入:
            user_id: str - 用户ID
            content: str - 记忆内容
            memory_type: str - "event"/"preference"/"habit"/"relation"
            metadata: Dict - 元数据 {"importance": 0.8, "tags": ["family"]}
        
        输出:
            str - 记忆ID
        """
    
    def query_memory(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """查询记忆
        
        输入:
            user_id: str - 用户ID
            query: str - 查询内容
            memory_type: Optional[str] - 限定记忆类型
            top_k: int - 返回数量
        
        输出:
            List[Dict] - 记忆列表
                [{
                    "memory_id": str,
                    "content": str,
                    "type": str,
                    "score": float,
                    "timestamp": str,
                    "metadata": dict
                }]
        """
```

---

## 中期增强计划(迭代2.2)

### 1. Foundation Layer深化

#### 1.1 GraphStore - 知识图谱存储
- 基于Neo4j的图存储实现
- 支持实体-关系-属性模型
- 提供Cypher查询接口

#### 1.2 MultiModalParser - 多模态解析
- 支持图片OCR提取
- 音频转文字
- 表格结构化解析

### 2. Capability Layer进阶

#### 2.1 ReasoningEngine - 推理引擎
- 基于规则的逻辑推理
- 结合LLM的常识推理
- 支持多步推理链

#### 2.2 PersonalityAdapter - 个性化适配
- 根据用户画像调整回复风格
- 学习用户偏好
- 动态调整交互策略

### 3. Service Layer全面覆盖

#### 3.1 HealthService - 健康管理服务
- 睡眠/运动/饮食记录
- 健康趋势分析
- 个性化建议

#### 3.2 LearningService - 学习管理服务
- 知识点管理
- 学习进度跟踪
- 复习提醒

---

## 长期演进计划(迭代3.0)

### 1. 智能化升级
- **主动感知**: 基于时间/事件触发主动提醒
- **预测建议**: 预测用户需求并提前准备
- **自适应学习**: 持续优化个人模型

### 2. 生态集成
- **第三方集成**: 日历/邮件/IM等
- **插件系统**: 支持自定义能力扩展
- **API开放**: 提供RESTful API

### 3. 性能与稳定性
- **缓存优化**: 多级缓存策略
- **异步处理**: 长耗时任务异步化
- **监控告警**: 完善的监控体系

---

## 优化实施路线图

### 第1周: Foundation增强
- ✅ Day 1-2: SpacyEntityExtractor实现与测试
- ✅ Day 3-4: TransformerEmbedding实现与测试
- ✅ Day 5: 分层意图识别与多级别摘要

### 第2周: Capability完善
- ✅ Day 1-2: ContextRetriever混合检索
- ✅ Day 3-5: Life场景其他能力优化

### 第3周: Service扩展
- ✅ Day 1-3: LifeDialogueService实现
- ✅ Day 4-5: LifeMemoryService实现

### 第4周: 集成测试与优化
- ✅ Day 1-2: 端到端集成测试
- ✅ Day 3-4: 性能优化
- ✅ Day 5: 文档完善

---

## 技术选型建议

### NLP工具
- **spaCy**: 中文NER (模型: zh_core_web_sm)
- **HuggingFace Transformers**: 向量化 (模型: text2vec-base-chinese)

### 存储方案
- **向量数据库**: Faiss(本地) / Qdrant(生产)
- **图数据库**: Neo4j
- **缓存**: Redis

### 测试框架
- **单元测试**: 独立Python脚本 + assert
- **集成测试**: pytest
- **性能测试**: locust

---

## 依赖安装清单

```bash
# NLP增强
pip install spacy
python -m spacy download zh_core_web_sm

# Embedding增强
pip install transformers torch sentence-transformers

# 存储增强
pip install faiss-cpu neo4j qdrant-client redis

# 测试工具
pip install pytest pytest-cov locust

# 工具库
pip install pydantic python-dotenv loguru
```

---

## 注意事项

1. **向后兼容**: 所有增强功能通过工厂模式提供,不破坏现有API
2. **配置化**: 新功能通过配置文件启用,支持降级
3. **测试先行**: 每个新功能必须有单元测试和集成测试
4. **文档同步**: 代码和文档同步更新
5. **性能监控**: 关键路径添加性能日志

---

**文档版本**: v1.0  
**创建日期**: 2025-11-21  
**维护者**: AME Development Team
