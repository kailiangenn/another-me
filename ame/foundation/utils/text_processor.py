"""
文本处理工具 - Foundation Layer
负责: 文件解析、文本清洗、格式标准化
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import re
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本处理器（支持同步和异步）"""
    
    def __init__(self, max_workers: int = 4):
        self.supported_formats = ['.txt', '.json', '.md']
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_file(self, file_path: str) -> List[Dict]:
        """处理文件"""
        extension = file_path.split('.')[-1].lower()
        
        if extension in ['txt', 'md']:
            return await self._process_text_file(file_path)
        elif extension == 'json':
            return await self._process_json_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    async def process_text(
        self, 
        text: str, 
        source: str, 
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理文本内容"""
        cleaned_text = self.clean_text(text)
        
        return {
            "content": cleaned_text,
            "source": source,
            "timestamp": timestamp or datetime.now().isoformat(),
            "metadata": {
                "length": len(cleaned_text),
                "processed_at": datetime.now().isoformat()
            }
        }
    
    async def _process_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decoding failed for {file_path}, trying GBK")
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        paragraphs = self.split_into_paragraphs(content)
        
        documents = []
        for para in paragraphs:
            if len(para.strip()) > 10:
                doc = await self.process_text(text=para, source=file_path)
                documents.append(doc)
        
        logger.info(f"Processed {len(documents)} paragraphs from {Path(file_path).name}")
        return documents
    
    async def _process_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """处理 JSON 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("content"):
                    doc = await self.process_text(
                        text=item.get("content", ""),
                        source=f"{file_path}:{item.get('sender', 'unknown')}",
                        timestamp=item.get("timestamp")
                    )
                    documents.append(doc)
        
        logger.info(f"Processed {len(documents)} messages from {Path(file_path).name}")
        return documents
    
    def clean_text(self, text: str) -> str:
        """文本清洗"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:，。！？；：""''、]', '', text)
        return text.strip()
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    async def process_files_concurrent(self, file_paths: List[str]) -> List[Dict]:
        """并发处理多个文件"""
        logger.info(f"Starting concurrent processing of {len(file_paths)} files")
        
        tasks = [self._process_file_async(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing file {file_paths[i]}: {str(result)}")
            else:
                valid_results.extend(result)
        
        logger.info(f"Completed processing: {len(valid_results)} documents")
        return valid_results
    
    async def _process_file_async(self, file_path: str) -> List[Dict]:
        """异步处理单个文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._process_file_sync,
            file_path
        )
    
    def _process_file_sync(self, file_path: str) -> List[Dict]:
        """同步处理文件"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_file(file_path))
        finally:
            loop.close()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
