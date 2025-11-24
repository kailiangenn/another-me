"""
文件解析器基类

定义统一的解析器接口
"""

from abc import ABC, abstractmethod
from pathlib import Path
from ..core.models import ParsedDocument


class FileParserBase(ABC):
    """
    文件解析器基类
    
    所有具体解析器需要实现:
    - can_parse(): 判断是否支持该文件
    - parse(): 执行解析
    """
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        判断是否可以解析该文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            can_parse: 是否可以解析
        """
        pass
    
    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析文档
        
        Args:
            file_path: 文件路径
        
        Returns:
            parsed_doc: 解析后的文档对象
        
        Raises:
            FileNotFoundError: 文件不存在
            UnsupportedFormatError: 不支持的文件格式
            ParseError: 解析错误
        """
        pass
    
    @staticmethod
    def _validate_file_exists(file_path: str) -> Path:
        """
        验证文件是否存在
        
        Args:
            file_path: 文件路径
        
        Returns:
            path: Path对象
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"不是文件: {file_path}")
        
        return path
    
    @staticmethod
    def _get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名（小写，不含点）
        
        Args:
            file_path: 文件路径
        
        Returns:
            extension: 扩展名
        """
        return Path(file_path).suffix.lower().lstrip(".")
