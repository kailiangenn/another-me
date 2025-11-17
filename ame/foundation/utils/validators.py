"""
验证工具函数
"""
from typing import Any, Optional
import re


def validate_doc_id(doc_id: str) -> bool:
    """
    验证文档 ID
    - 非空
    - 长度合理（1-256）
    """
    if not doc_id or not isinstance(doc_id, str):
        return False
    
    return 1 <= len(doc_id) <= 256


def validate_text(text: str, min_length: int = 1, max_length: int = 100000) -> bool:
    """
    验证文本
    
    Args:
        text: 文本内容
        min_length: 最小长度
        max_length: 最大长度
    """
    if not text or not isinstance(text, str):
        return False
    
    return min_length <= len(text.strip()) <= max_length


def validate_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> bool:
    """
    验证分数
    
    Args:
        score: 分数值
        min_val: 最小值
        max_val: 最大值
    """
    if not isinstance(score, (int, float)):
        return False
    
    return min_val <= score <= max_val


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """验证 URL 格式"""
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_timestamp(timestamp: Any) -> bool:
    """验证时间戳（支持多种格式）"""
    from datetime import datetime
    
    if isinstance(timestamp, datetime):
        return True
    
    if isinstance(timestamp, str):
        try:
            datetime.fromisoformat(timestamp)
            return True
        except ValueError:
            return False
    
    if isinstance(timestamp, (int, float)):
        return timestamp > 0
    
    return False


def validate_dict(data: Any, required_keys: Optional[list] = None) -> bool:
    """
    验证字典结构
    
    Args:
        data: 待验证数据
        required_keys: 必需的键列表
    """
    if not isinstance(data, dict):
        return False
    
    if required_keys:
        return all(key in data for key in required_keys)
    
    return True


def validate_list(data: Any, min_length: int = 0, max_length: Optional[int] = None) -> bool:
    """
    验证列表
    
    Args:
        data: 待验证数据
        min_length: 最小长度
        max_length: 最大长度
    """
    if not isinstance(data, list):
        return False
    
    if len(data) < min_length:
        return False
    
    if max_length is not None and len(data) > max_length:
        return False
    
    return True
