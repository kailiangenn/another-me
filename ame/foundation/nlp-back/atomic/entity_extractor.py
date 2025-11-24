"""
实体提取器 - 基于jieba分词和LLM的实体提取
"""

from typing import List, Dict, Optional
from loguru import logger

from ..core import (
    Entity,
    EntityType,
    EntityExtractionError,
    DependencyMissingError,
)


class EntityExtractor:
    """实体提取器（基于jieba分词 + LLM增强）
    
    Enhancements:
    - 支持自定义jieba词典
    - 支持NER模型切换
    - 支持自定义实体类型映射
    """
    
    def __init__(
        self,
        llm_caller=None,
        enable_jieba: bool = True,
        custom_dict_path: Optional[str] = None,
        ner_backend: str = "jieba"
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器（可选）
            enable_jieba: 是否启用jieba分词
            custom_dict_path: 自定义jieba词典路径
            ner_backend: NER后端 ("jieba", "spacy", "hanlp", "custom")
        """
        self.llm = llm_caller
        self.enable_jieba = enable_jieba
        self.jieba = None
        self.pseg = None
        self.ner_backend = ner_backend
        self.custom_ner_func = None
        self.custom_type_mapping = {}
        
        # 初始化NER后端
        if ner_backend == "jieba" and enable_jieba:
            self._init_jieba(custom_dict_path)
        elif ner_backend == "spacy":
            self._init_spacy()
        elif ner_backend == "hanlp":
            self._init_hanlp()
        elif ner_backend != "custom":
            logger.warning(f"不支持的NER后端: {ner_backend}, 默认使用jieba")
            self.ner_backend = "jieba"
            self._init_jieba(custom_dict_path)
    
    def _init_jieba(self, custom_dict_path: Optional[str] = None) -> None:
        """初始化jieba
        
        Args:
            custom_dict_path: 自定义词典路径
        """
        try:
            import jieba
            import jieba.posseg as pseg
            self.jieba = jieba
            self.pseg = pseg
            logger.debug("jieba分词已加载")
            
            # 加载自定义词典
            if custom_dict_path:
                self.load_custom_dict(custom_dict_path)
        except ImportError:
            logger.warning("jieba未安装，实体提取功能受限")
            self.enable_jieba = False
    
    def _init_spacy(self) -> None:
        """初始化spacy (占位实现)"""
        logger.warning("spacy后端暂未实现，请安装spacy并自定义实现")
        # TODO: Implement spacy NER
        # import spacy
        # self.spacy_nlp = spacy.load("zh_core_web_sm")
    
    def _init_hanlp(self) -> None:
        """初始化HanLP (占位实现)"""
        logger.warning("HanLP后端暂未实现，请安装hanlp并自定义实现")
        # TODO: Implement HanLP NER
        # import hanlp
        # self.hanlp_ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_BERT_BASE_ZH)
    
    def load_custom_dict(self, dict_path: str) -> None:
        """加载自定义jieba词典
        
        Args:
            dict_path: 词典文件路径 (格式: 词语 词频 词性)
        """
        if not self.jieba:
            logger.warning("未启用jieba，无法加载自定义词典")
            return
        
        try:
            self.jieba.load_userdict(dict_path)
            logger.info(f"已加载自定义词典: {dict_path}")
        except Exception as e:
            logger.error(f"加载自定义词典失败: {e}")
    
    def set_ner_backend(self, backend: str) -> None:
        """切换NER后端
        
        Args:
            backend: NER后端 ("jieba", "spacy", "hanlp", "custom")
        """
        if backend == self.ner_backend:
            logger.info(f"当前NER后端已是 {backend}")
            return
        
        logger.info(f"切换NER后端: {self.ner_backend} -> {backend}")
        self.ner_backend = backend
        
        if backend == "jieba":
            self._init_jieba()
        elif backend == "spacy":
            self._init_spacy()
        elif backend == "hanlp":
            self._init_hanlp()
    
    def set_custom_ner_function(self, ner_func) -> None:
        """设置自定义NER函数
        
        Args:
            ner_func: 自定义NER函数 (text: str) -> List[Entity]
        """
        self.ner_backend = "custom"
        self.custom_ner_func = ner_func
        logger.info("已设置自定义NER函数")
    
    def register_entity_type_mapping(self, flag: str, entity_type: EntityType) -> None:
        """注册自定义实体类型映射
        
        Args:
            flag: 词性标注
            entity_type: 实体类型
        """
        self.custom_type_mapping[flag] = entity_type
        logger.info(f"注册实体类型映射: {flag} -> {entity_type.value}")
    
    def _map_flag_to_type(self, flag: str) -> EntityType:
        """映射jieba词性标注到实体类型
        
        Args:
            flag: jieba词性标注
            
        Returns:
            实体类型
        """
        # 优先使用自定义映射
        if flag in self.custom_type_mapping:
            return self.custom_type_mapping[flag]
        
        # 默认映射
        flag_map = {
            'nr': EntityType.PERSON,      # 人名
            'ns': EntityType.LOCATION,    # 地名
            'nt': EntityType.ORGANIZATION,  # 机构名
            'nz': EntityType.OTHER,       # 其他专名
            't': EntityType.TIME,         # 时间词
        }
        return flag_map.get(flag, EntityType.OTHER)
    
    def _extract_by_jieba(self, text: str) -> List[Entity]:
        """使用jieba提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        if not self.enable_jieba or not self.pseg:
            return []
        
        entities = []
        offset = 0
        
        # 词性标注
        words = self.pseg.cut(text)
        for word, flag in words:
            # 只保留命名实体
            if flag in ['nr', 'ns', 'nt', 'nz', 't']:
                entity_type = self._map_flag_to_type(flag)
                
                # 计算位置
                start = text.find(word, offset)
                end = start + len(word) if start >= 0 else 0
                offset = end
                
                entities.append(Entity(
                    text=word,
                    type=entity_type,
                    start=start,
                    end=end,
                    confidence=0.7,
                    metadata={"flag": flag, "method": "jieba"}
                ))
        
        return entities
    
    async def _extract_by_llm(self, text: str) -> List[Entity]:
        """使用LLM提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        if not self.llm:
            return []
        
        try:
            prompt = f"""请从以下文本中提取命名实体，包括：人名、地点、组织、技术概念、时间、事件等。

文本: {text}

请以JSON格式返回，例如:
[
  {{"text": "张三", "type": "person"}},
  {{"text": "北京", "type": "location"}}
]

类型可选: person, location, organization, concept, time, event, other
只返回JSON，不要其他内容。"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages, max_tokens=500, temperature=0)
            
            # 解析JSON响应
            import json
            try:
                raw_content = response.content.strip()
                # 尝试提取JSON部分
                if "```json" in raw_content:
                    raw_content = raw_content.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_content:
                    raw_content = raw_content.split("```")[1].split("```")[0].strip()
                
                entities_data = json.loads(raw_content)
                
                entities = []
                for entity_dict in entities_data:
                    entity_type_str = entity_dict.get("type", "other")
                    
                    # 映射类型
                    type_map = {
                        "person": EntityType.PERSON,
                        "location": EntityType.LOCATION,
                        "organization": EntityType.ORGANIZATION,
                        "concept": EntityType.CONCEPT,
                        "time": EntityType.TIME,
                        "event": EntityType.EVENT,
                        "other": EntityType.OTHER,
                    }
                    entity_type = type_map.get(entity_type_str, EntityType.OTHER)
                    
                    # 查找位置
                    entity_text = entity_dict.get("text", "")
                    start = text.find(entity_text)
                    end = start + len(entity_text) if start >= 0 else 0
                    
                    entities.append(Entity(
                        text=entity_text,
                        type=entity_type,
                        start=start,
                        end=end,
                        confidence=0.85,
                        metadata={"method": "llm"}
                    ))
                
                return entities
                
            except json.JSONDecodeError as e:
                logger.error(f"LLM返回的JSON格式错误: {e}, 原始内容: {response.content}")
                return []
                
        except Exception as e:
            logger.error(f"LLM实体提取失败: {e}")
            return []
    
    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        """去重实体
        
        Args:
            entities: 实体列表
            
        Returns:
            去重后的实体列表
        """
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # 使用文本和类型作为唯一标识
            key = (entity.text.lower(), entity.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    async def extract(
        self, 
        text: str, 
        use_llm: bool = False,
        use_backend: bool = True
    ) -> List[Entity]:
        """提取实体
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM增强
            use_backend: 是否使用NER后端
            
        Returns:
            实体列表
        """
        if not text or not text.strip():
            raise EntityExtractionError("输入文本不能为空")
        
        entities = []
        
        # 1. 使用NER后端提取
        if use_backend:
            if self.ner_backend == "jieba" and self.enable_jieba:
                backend_entities = self._extract_by_jieba(text)
            elif self.ner_backend == "custom" and self.custom_ner_func:
                backend_entities = self.custom_ner_func(text)
            else:
                logger.warning(f"NER后端 '{self.ner_backend}' 不可用")
                backend_entities = []
            
            entities.extend(backend_entities)
            logger.debug(f"{self.ner_backend}提取到 {len(backend_entities)} 个实体")
        
        # 2. LLM增强（可选）
        if use_llm and self.llm:
            llm_entities = await self._extract_by_llm(text)
            entities.extend(llm_entities)
            logger.debug(f"LLM提取到 {len(llm_entities)} 个实体")
        
        # 3. 去重
        entities = self._deduplicate(entities)
        
        return entities
    
    def extract_sync(self, text: str) -> List[Entity]:
        """同步提取（仅使用jieba）
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        if not text or not text.strip():
            raise EntityExtractionError("输入文本不能为空")
        
        if not self.enable_jieba:
            logger.warning("jieba未启用，无法同步提取实体")
            return []
        
        return self._extract_by_jieba(text)
