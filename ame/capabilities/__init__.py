"""
Capabilities Layer - 能力模块层

组合 Foundation Layer 的基础能力，提供面向场景的高级能力。

推荐使用 CapabilityFactory 来构建和组合能力，而非直接实例化。
"""

__version__ = "0.4.0"

# Memory
from .memory import MemoryBase, MemoryItem, MemoryManager, ConversationFilter

# Retrieval
from .retrieval import RetrieverBase, RetrievalResult, HybridRetriever

# Intent
from .intent import IntentRecognizerBase, IntentResult, UserIntent, IntentRecognizer

# Analysis
from .analysis import DataAnalyzer, InsightGenerator

# Generation
from .generation import RAGGenerator, StyleGenerator

# Factory
from .factory import CapabilityFactory, CapabilityType

__all__ = [
    # Factory (推荐使用)
    "CapabilityFactory",
    "CapabilityType",
    
    # Memory
    "MemoryBase",
    "MemoryItem",
    "MemoryManager",
    "ConversationFilter",
    
    # Retrieval
    "RetrieverBase",
    "RetrievalResult",
    "HybridRetriever",
    
    # Intent
    "IntentRecognizerBase",
    "IntentResult",
    "UserIntent",
    "IntentRecognizer",
    
    # Analysis
    "DataAnalyzer",
    "InsightGenerator",
    
    # Generation
    "RAGGenerator",
    "StyleGenerator",
]
