"""
存储异常定义
"""


class StorageError(Exception):
    """存储基础异常"""
    pass


class ConnectionError(StorageError):
    """连接异常"""
    
    def __init__(self, message: str, host: str = None, port: int = None):
        self.host = host
        self.port = port
        super().__init__(message)


class ValidationError(StorageError):
    """数据验证异常"""
    
    def __init__(self, message: str, data: any = None):
        self.data = data
        super().__init__(message)


class QueryError(StorageError):
    """查询异常"""
    
    def __init__(self, message: str, query: str = None):
        self.query = query
        super().__init__(message)


class VectorStoreError(StorageError):
    """向量存储异常"""
    pass


class GraphStoreError(StorageError):
    """图存储异常"""
    pass
