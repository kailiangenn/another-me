"""
文本处理工具函数
"""
import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    清理文本
    - 去除多余空白
    - 统一换行符
    """
    if not text:
        return ""
    
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 去除首尾空白
    text = text.strip()
    
    # 压缩多余空格（保留单个换行）
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后缀
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    估算 token 数量（简化版）
    
    规则：
    - 英文：~4 字符/token
    - 中文：~2 字符/token
    """
    if not text:
        return 0
    
    # 统计中英文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars
    
    # 估算 token
    tokens = chinese_chars // 2 + other_chars // 4
    
    return max(1, tokens)


def split_text(
    text: str,
    max_tokens: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    分割长文本
    
    Args:
        text: 输入文本
        max_tokens: 每段最大 token 数
        overlap: 段落重叠 token 数
    """
    if not text:
        return []
    
    if count_tokens(text) <= max_tokens:
        return [text]
    
    # 按句子分割
    sentences = re.split(r'([。！？.!?])', text)
    sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2] + [''])]
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        
        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            # 保存当前段落
            chunks.append(''.join(current_chunk))
            
            # 计算重叠部分
            overlap_text = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                s_tokens = count_tokens(s)
                if overlap_tokens + s_tokens > overlap:
                    break
                overlap_text.insert(0, s)
                overlap_tokens += s_tokens
            
            current_chunk = overlap_text
            current_tokens = overlap_tokens
        
        current_chunk.append(sentence)
        current_tokens += sentence_tokens
    
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    return chunks


def extract_keywords(text: str, top_k: int = 5) -> List[str]:
    """
    提取关键词（简化版 - 基于词频）
    
    Args:
        text: 输入文本
        top_k: 返回前 K 个关键词
    """
    if not text:
        return []
    
    # 分词（简化：按空格和标点分割）
    words = re.findall(r'[\w]+', text.lower())
    
    # 过滤停用词（简化版）
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一'}
    words = [w for w in words if w not in stopwords and len(w) > 1]
    
    # 统计词频
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 排序并返回
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_k]]


def normalize_text(text: str) -> str:
    """
    标准化文本
    - 转小写
    - 去除特殊字符
    - 压缩空格
    """
    if not text:
        return ""
    
    # 转小写
    text = text.lower()
    
    # 保留字母、数字、中文、空格
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    
    # 压缩空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
