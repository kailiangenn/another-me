"""
文档解析异常定义
"""


class FileParserError(Exception):
    """文件解析基础异常"""
    pass


class UnsupportedFormatError(FileParserError):
    """不支持的文件格式异常"""
    
    def __init__(self, format: str, message: str = None):
        self.format = format
        default_message = f"不支持的文件格式: {format}"
        super().__init__(message or default_message)


class ParseError(FileParserError):
    """文档解析错误异常"""
    
    def __init__(self, file_path: str, reason: str = None):
        self.file_path = file_path
        self.reason = reason
        message = f"解析文档失败: {file_path}"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


class DependencyMissingError(FileParserError):
    """依赖缺失异常"""
    
    def __init__(self, dependency: str, install_command: str = None):
        self.dependency = dependency
        self.install_command = install_command
        message = f"缺少依赖: {dependency}"
        if install_command:
            message += f"\n请安装: {install_command}"
        super().__init__(message)
