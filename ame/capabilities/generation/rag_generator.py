"""
RAG (Retrieval-Augmented Generation) 生成器
整合自：
- rag/knowledge_base.py
- rag_generator/generator.py

依赖：
- HybridRetriever (Capabilities Layer): 检索相关文档
- OpenAICaller (Foundation Layer): LLM 生成
"""
from typing import List, Dict, Any, Optional

from ame.foundation.llm import OpenAICaller
from ame.capabilities.retrieval import HybridRetriever
from ame.models.domain import Document


class RAGGenerator:
    """
    RAG (Retrieval-Augmented Generation) 生成器
    
    基于检索增强的生成，提供：
    - 知识库问答
    - 带引用的回答生成
    - 上下文感知生成
    """
    
    def __init__(
        self,
        retriever: HybridRetriever,
        llm_caller: OpenAICaller
    ):
        """
        初始化 RAG 生成器
        
        Args:
            retriever: 混合检索器
            llm_caller: LLM 调用器
        """
        self.retriever = retriever
        self.llm = llm_caller
    
    async def generate(
        self,
        query: str,
        context: Optional[Dict] = None,
        max_tokens: int = 1000,
        top_k: int = 5
    ) -> str:
        """
        基于检索的生成
        
        流程：
        1. 使用 retriever 检索相关文档
        2. 构建包含检索结果的 Prompt
        3. 使用 LLM 生成回答
        
        Args:
            query: 用户查询
            context: 上下文信息（可选）
            max_tokens: 最大生成长度
            top_k: 检索文档数量
        
        Returns:
            生成的回答
        """
        # Step 1: 检索相关文档
        retrieval_result = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=context.get("filters") if context else None
        )
        
        # Step 2: 构建 Prompt
        prompt = self._build_rag_prompt(
            query=query,
            documents=retrieval_result.documents,
            context=context
        )
        
        # Step 3: LLM 生成
        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        return response.strip()
    
    async def generate_with_citations(
        self,
        query: str,
        context: Optional[Dict] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        带引用的生成
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 检索文档数量
        
        Returns:
            {
                "answer": "回答内容",
                "citations": [{"doc_id": "...", "content": "...", "score": 0.95}],
                "source_count": 3
            }
        """
        # 检索
        retrieval_result = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=context.get("filters") if context else None
        )
        
        # 生成回答
        answer = await self.generate(
            query=query,
            context=context,
            top_k=top_k
        )
        
        # 构建引用
        citations = [
            {
                "doc_id": doc.doc_id,
                "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "score": getattr(doc, 'score', 1.0),
                "source": doc.source
            }
            for doc in retrieval_result.documents
        ]
        
        return {
            "answer": answer,
            "citations": citations,
            "source_count": len(citations)
        }
    
    async def generate_stream(
        self,
        query: str,
        context: Optional[Dict] = None,
        top_k: int = 5
    ):
        """
        流式生成（如果 LLM 支持）
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 检索文档数量
        
        Yields:
            生成的文本片段
        """
        # 检索
        retrieval_result = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=context.get("filters") if context else None
        )
        
        # 构建 Prompt
        prompt = self._build_rag_prompt(
            query=query,
            documents=retrieval_result.documents,
            context=context
        )
        
        # 流式生成（如果支持）
        if hasattr(self.llm, 'generate_stream'):
            async for chunk in self.llm.generate_stream(prompt):
                yield chunk
        else:
            # 降级：一次性生成
            response = await self.llm.generate(prompt)
            yield response
    
    def _build_rag_prompt(
        self,
        query: str,
        documents: List[Document],
        context: Optional[Dict]
    ) -> str:
        """
        构建 RAG Prompt
        
        格式：
        [相关文档]
        文档1...
        文档2...
        
        [用户问题]
        {query}
        
        [回答要求]
        请基于以上文档回答问题...
        """
        # 构建文档部分
        doc_texts = []
        for i, doc in enumerate(documents[:5], 1):
            # 限制每个文档长度
            content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
            doc_texts.append(f"[文档{i}]\n{content}")
        
        docs_section = "\n\n".join(doc_texts) if doc_texts else "[暂无相关文档]"
        
        # 构建完整 Prompt
        prompt = f"""[相关文档]
{docs_section}

[用户问题]
{query}

[回答要求]
请基于以上文档回答用户的问题。
1. 如果文档中有相关信息，请综合文档内容进行回答
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要准确、简洁、有条理
"""
        
        # 如果有上下文约束，添加到 Prompt
        if context:
            if "style" in context:
                prompt += f"\n\n[语气风格]: {context['style']}"
            if "max_length" in context:
                prompt += f"\n[长度要求]: 回答控制在{context['max_length']}字以内"
        
        return prompt
    
    def _format_citations(self, documents: List[Document]) -> str:
        """格式化引用信息"""
        if not documents:
            return ""
        
        citations = []
        for i, doc in enumerate(documents, 1):
            citations.append(
                f"[{i}] {doc.source} - {doc.timestamp.strftime('%Y-%m-%d') if doc.timestamp else '未知时间'}"
            )
        
        return "\n参考来源：\n" + "\n".join(citations)
