"""
ConnectService - 配置测试服务

提供LLM和Storage配置测试能力，帮助用户验证配置是否正确。

服务特性：
- 无对话：单次调用，返回测试结果
- 无持久化：不存储任何数据
- 核心能力：复用test_llm.py和test_storage.py的测试逻辑
"""

from typing import Optional
from loguru import logger

from ame.capability.factory import CapabilityFactory
from .test_llm import TestConfig as LLMTestConfig, TestSummary, test_llm_callers
from .test_storage import TestConfig as StorageTestConfig, test_storage_graph


class ConnectService:
    """配置测试服务
    
    遵循架构规范：
    - 通过CapabilityFactory获取能力
    - 不直接创建Foundation层组件
    """
    
    def __init__(self, capability_factory: CapabilityFactory):
        """初始化
        
        Args:
            capability_factory: 能力工厂实例
        """
        self.factory = capability_factory
        logger.debug("ConnectService初始化完成")
    
    async def test_llm_config(
        self, 
        api_key: str, 
        model: str = "gpt-3.5-turbo", 
        base_url: Optional[str] = None,
        test_connectivity: bool = True,
        test_stream: bool = True,
        test_complete: bool = True,
        test_token_estimation: bool = True,
        test_error_handling: bool = False,
        **kwargs
    ) -> TestSummary:
        """测试LLM配置
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            base_url: API基础URL
            test_connectivity: 是否测试连通性
            test_stream: 是否测试流式输出
            test_complete: 是否测试完整输出
            test_token_estimation: 是否测试Token估算
            test_error_handling: 是否测试错误处理
            **kwargs: 其他OpenAI参数
            
        Returns:
            测试汇总结果
        """
        logger.info(f"开始测试LLM配置: model={model}, base_url={base_url}")
        
        # 通过工厂创建LLM调用器
        llm_caller = self.factory.create_llm_caller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs
        )
        
        # 配置测试选项
        config = LLMTestConfig(
            test_connectivity=test_connectivity,
            test_stream=test_stream,
            test_complete=test_complete,
            test_token_estimation=test_token_estimation,
            test_error_handling=test_error_handling
        )
        
        # 执行测试
        summary = await test_llm_callers(caller=llm_caller, config=config)
        
        logger.info(f"LLM配置测试完成: {summary.passed}/{summary.total} 通过")
        return summary
    
    async def test_storage_config(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        graph_name: str = "ame_graph",
        password: Optional[str] = None,
        test_connectivity: bool = True,
        test_node_operations: bool = True,
        test_edge_operations: bool = True,
        test_query_operations: bool = True,
        test_time_query: bool = True,
        **kwargs
    ) -> TestSummary:
        """测试Storage配置
        
        Args:
            host: FalkorDB主机地址
            port: FalkorDB端口
            graph_name: 图名称
            password: 密码
            test_connectivity: 是否测试连通性
            test_node_operations: 是否测试节点操作
            test_edge_operations: 是否测试边操作
            test_query_operations: 是否测试查询操作
            test_time_query: 是否测试时间查询
            **kwargs: 其他FalkorDB参数
            
        Returns:
            测试汇总结果
        """
        logger.info(f"开始测试Storage配置: host={host}, port={port}, graph={graph_name}")
        
        # 通过工厂创建图存储
        graph_store = self.factory.create_graph_store(
            host=host,
            port=port,
            graph_name=graph_name,
            password=password,
            **kwargs
        )
        
        # 配置测试选项
        config = StorageTestConfig(
            test_connectivity=test_connectivity,
            test_node_operations=test_node_operations,
            test_edge_operations=test_edge_operations,
            test_query_operations=test_query_operations,
            test_time_query=test_time_query
        )
        
        # 执行测试
        summary = await test_storage_graph(store=graph_store, config=config)
        
        logger.info(f"Storage配置测试完成: {summary.passed}/{summary.total} 通过")
        return summary
    
    async def test_all_configs(
        self,
        # LLM配置
        llm_api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_base_url: Optional[str] = None,
        # Storage配置
        storage_host: str = "localhost",
        storage_port: int = 6379,
        storage_graph_name: str = "ame_graph",
        storage_password: Optional[str] = None,
        **kwargs
    ) -> dict:
        """测试所有配置（LLM + Storage）
        
        Args:
            llm_api_key: LLM API密钥
            llm_model: LLM模型名称
            llm_base_url: LLM API基础URL
            storage_host: Storage主机
            storage_port: Storage端口
            storage_graph_name: 图名称
            storage_password: Storage密码
            **kwargs: 其他参数
            
        Returns:
            包含所有测试结果的字典
        """
        logger.info("开始测试所有配置（LLM + Storage）")
        
        results = {}
        
        # 测试LLM
        try:
            llm_summary = await self.test_llm_config(
                api_key=llm_api_key,
                model=llm_model,
                base_url=llm_base_url
            )
            results["llm"] = {
                "success": llm_summary.success,
                "summary": llm_summary
            }
        except Exception as e:
            logger.error(f"LLM配置测试失败: {e}")
            results["llm"] = {
                "success": False,
                "error": str(e)
            }
        
        # 测试Storage
        try:
            storage_summary = await self.test_storage_config(
                host=storage_host,
                port=storage_port,
                graph_name=storage_graph_name,
                password=storage_password
            )
            results["storage"] = {
                "success": storage_summary.success,
                "summary": storage_summary
            }
        except Exception as e:
            logger.error(f"Storage配置测试失败: {e}")
            results["storage"] = {
                "success": False,
                "error": str(e)
            }
        
        # 汇总
        all_success = all(r.get("success", False) for r in results.values())
        results["all_passed"] = all_success
        
        logger.info(f"所有配置测试完成: {'全部通过' if all_success else '存在失败'}")
        return results
