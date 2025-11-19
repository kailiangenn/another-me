"""Storage配置测试模块

提供图数据库存储的完整测试功能。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from loguru import logger
import asyncio
from datetime import datetime

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ame.foundation.storage import (
    GraphStoreBase,
    FalkorDBStore,
    GraphNode,
    GraphEdge,
    NodeLabel,
    RelationType,
)


@dataclass
class TestConfig:
    """测试配置"""
    test_connectivity: bool = True
    test_node_operations: bool = True
    test_edge_operations: bool = True
    test_query_operations: bool = True
    test_time_query: bool = True


@dataclass
class TestResult:
    """单项测试结果"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class TestSummary:
    """测试汇总结果"""
    total: int
    passed: int
    failed: int
    results: Dict[str, TestResult]
    
    @property
    def pass_rate(self) -> float:
        """通过率"""
        return self.passed / self.total if self.total > 0 else 0.0
    
    @property
    def success(self) -> bool:
        """是否全部通过"""
        return self.passed == self.total


class StorageTester:
    """Storage测试器"""
    
    def __init__(self, store: GraphStoreBase):
        """
        初始化
        
        Args:
            store: 已实例化配置的图数据库存储
        """
        if not isinstance(store, GraphStoreBase):
            raise TypeError("store必须是GraphStoreBase的子类实例")
        self.store = store
        self._test_node_ids = []
        self._test_edge_ids = []
    
    async def test_connectivity(self) -> TestResult:
        """测试连通性"""
        try:
            await self.store.connect()
            
            is_healthy = await self.store.health_check()
            
            if not is_healthy:
                return TestResult(
                    success=False,
                    message="健康检查失败",
                    error="数据库连接不健康"
                )
            
            return TestResult(
                success=True,
                message="连通性测试通过",
                details={
                    "store_type": type(self.store).__name__,
                    "health_status": "healthy"
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="连通性测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_node_operations(self) -> TestResult:
        """测试节点操作（CRUD）"""
        try:
            # 1. 创建节点
            test_node = GraphNode(
                label=NodeLabel.PERSON,
                properties={
                    "name": "测试用户",
                    "user_id": "test_001",
                    "source": "test"
                }
            )
            
            node_id = await self.store.create_node(test_node)
            self._test_node_ids.append(node_id)
            
            # 2. 获取节点
            retrieved_node = await self.store.get_node(node_id)
            if not retrieved_node:
                raise Exception("创建的节点无法获取")
            
            # 3. 更新节点
            update_success = await self.store.update_node(
                node_id,
                {"name": "更新后的用户"}
            )
            
            if not update_success:
                raise Exception("节点更新失败")
            
            # 4. 查找节点
            found_nodes = await self.store.find_nodes(
                label=NodeLabel.PERSON,
                properties={"user_id": "test_001"},
                limit=10
            )
            
            return TestResult(
                success=True,
                message="节点操作测试通过",
                details={
                    "created_node_id": node_id,
                    "retrieved": retrieved_node is not None,
                    "updated": update_success,
                    "found_count": len(found_nodes)
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="节点操作测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_edge_operations(self) -> TestResult:
        """测试边操作（CRUD）"""
        try:
            # 先创建两个节点
            node1 = GraphNode(
                label=NodeLabel.PERSON,
                properties={"name": "用户A", "user_id": "test_002"}
            )
            node2 = GraphNode(
                label=NodeLabel.INTEREST,
                properties={"name": "编程"}
            )
            
            node1_id = await self.store.create_node(node1)
            node2_id = await self.store.create_node(node2)
            self._test_node_ids.extend([node1_id, node2_id])
            
            # 1. 创建边
            test_edge = GraphEdge(
                source_id=node1_id,
                target_id=node2_id,
                relation=RelationType.INTERESTED_IN,
                properties={"level": "高"},
                weight=0.9,
                valid_from=datetime.now()
            )
            
            edge_id = await self.store.create_edge(test_edge)
            self._test_edge_ids.append(edge_id)
            
            # 2. 获取边
            retrieved_edge = await self.store.get_edge(edge_id)
            if not retrieved_edge:
                raise Exception("创建的边无法获取")
            
            # 3. 更新边
            update_success = await self.store.update_edge(
                edge_id,
                {"weight": 0.95}
            )
            
            # 4. 查找边
            found_edges = await self.store.find_edges(
                source_id=node1_id,
                relation=RelationType.INTERESTED_IN
            )
            
            return TestResult(
                success=True,
                message="边操作测试通过",
                details={
                    "created_edge_id": edge_id,
                    "retrieved": retrieved_edge is not None,
                    "updated": update_success,
                    "found_count": len(found_edges)
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="边操作测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_query_operations(self) -> TestResult:
        """测试图查询操作"""
        try:
            if len(self._test_node_ids) < 2:
                raise Exception("需要先执行节点和边操作测试")
            
            node_id = self._test_node_ids[0]
            
            # 1. 获取邻居节点
            neighbors = await self.store.get_neighbors(
                node_id=node_id,
                direction="outgoing"
            )
            
            # 2. 查询两个节点之间的边
            if len(self._test_node_ids) >= 2:
                edges_between = await self.store.get_edges_between(
                    source_id=self._test_node_ids[0],
                    target_id=self._test_node_ids[1]
                )
            else:
                edges_between = []
            
            return TestResult(
                success=True,
                message="查询操作测试通过",
                details={
                    "neighbors_count": len(neighbors),
                    "edges_between_count": len(edges_between)
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="查询操作测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_time_query(self) -> TestResult:
        """测试时间范围查询"""
        try:
            # 查询当前时间点有效的边
            valid_edges = await self.store.find_valid_edges_at(
                timestamp=datetime.now()
            )
            
            # 测试过滤功能
            if self._test_node_ids:
                node_valid_edges = await self.store.find_valid_edges_at(
                    timestamp=datetime.now(),
                    source_id=self._test_node_ids[0]
                )
            else:
                node_valid_edges = []
            
            return TestResult(
                success=True,
                message="时间查询测试通过",
                details={
                    "total_valid_edges": len(valid_edges),
                    "node_valid_edges": len(node_valid_edges)
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="时间查询测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def cleanup(self):
        """清理测试数据"""
        try:
            # 删除测试边
            for edge_id in self._test_edge_ids:
                await self.store.delete_edge(edge_id)
            
            # 删除测试节点
            for node_id in self._test_node_ids:
                await self.store.delete_node(node_id)
            
            logger.debug("测试数据已清理")
        except Exception as e:
            logger.warning(f"清理测试数据失败: {e}")
    
    async def run_tests(self, config: TestConfig) -> TestSummary:
        """
        运行所有测试
        
        Args:
            config: 测试配置
            
        Returns:
            测试汇总结果
        """
        results = {}
        
        if config.test_connectivity:
            logger.info("[1/5] 测试连通性...")
            results["connectivity"] = await self.test_connectivity()
            self._print_result("连通性", results["connectivity"])
            
            if not results["connectivity"].success:
                logger.error("连通性测试失败，跳过后续测试")
                return TestSummary(
                    total=1,
                    passed=0,
                    failed=1,
                    results=results
                )
        
        if config.test_node_operations:
            logger.info("[2/5] 测试节点操作...")
            results["node_operations"] = await self.test_node_operations()
            self._print_result("节点操作", results["node_operations"])
        
        if config.test_edge_operations:
            logger.info("[3/5] 测试边操作...")
            results["edge_operations"] = await self.test_edge_operations()
            self._print_result("边操作", results["edge_operations"])
        
        if config.test_query_operations:
            logger.info("[4/5] 测试查询操作...")
            results["query_operations"] = await self.test_query_operations()
            self._print_result("查询操作", results["query_operations"])
        
        if config.test_time_query:
            logger.info("[5/5] 测试时间查询...")
            results["time_query"] = await self.test_time_query()
            self._print_result("时间查询", results["time_query"])
        
        # 清理测试数据
        await self.cleanup()
        
        # 断开连接
        await self.store.disconnect()
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results.values() if r.success)
        failed = total - passed
        
        return TestSummary(
            total=total,
            passed=passed,
            failed=failed,
            results=results
        )
    
    def _print_result(self, name: str, result: TestResult):
        """打印测试结果"""
        status = "✓" if result.success else "✗"
        logger.info(f"{status} {name}: {result.message}")
        
        if result.details:
            for key, value in result.details.items():
                logger.info(f"  - {key}: {value}")
        
        if result.error:
            logger.error(f"  错误: {result.error}")


async def test_storage_graph(
    store: Optional[GraphStoreBase] = None,
    config: Optional[TestConfig] = None,
    host: str = "localhost",
    port: int = 6379,
    graph_name: str = "test_graph",
    password: Optional[str] = None,
    **kwargs
) -> TestSummary:
    """
    测试Storage配置
    
    支持两种使用方式：
    1. 传入已实例化的store
    2. 传入host/port等参数，自动实例化FalkorDBStore
    
    Args:
        store: 已实例化的图存储（优先使用）
        config: 测试配置，默认执行所有测试
        host: FalkorDB主机地址（当store为None时使用）
        port: FalkorDB端口
        graph_name: 图名称
        password: 密码
        **kwargs: 其他FalkorDB参数
        
    Returns:
        测试汇总结果
    """
    # 确定使用的store
    if store is None:
        logger.info(f"使用默认FalkorDBStore实例化，Graph: {graph_name}")
        store = FalkorDBStore(
            host=host,
            port=port,
            graph_name=graph_name,
            password=password,
            **kwargs
        )
    else:
        logger.info(f"使用用户提供的store: {type(store).__name__}")
    
    if config is None:
        config = TestConfig()
    
    tester = StorageTester(store)
    summary = await tester.run_tests(config)
    
    # 打印汇总
    logger.info(f"\n{'='*50}")
    logger.info(f"测试完成: {summary.passed}/{summary.total} 通过")
    logger.info(f"通过率: {summary.pass_rate:.1%}")
    if summary.success:
        logger.info("✓ 所有测试通过")
    else:
        logger.warning(f"✗ {summary.failed} 项测试失败")
    logger.info(f"{'='*50}")
    
    return summary


if __name__ == "__main__":
    # 示例用法1: 直接传入已实例化的store
    store = FalkorDBStore(
        host="localhost",
        port=6379,
        graph_name="test_graph",
        password=None
    )
    
    config = TestConfig(
        test_connectivity=True,
        test_node_operations=True,
        test_edge_operations=True,
        test_query_operations=True,
        test_time_query=True
    )
    
    summary = asyncio.run(test_storage_graph(store=store, config=config))
    print(f"\n测试结果: {'成功' if summary.success else '失败'}")
    
    # 示例用法2: 仅传入连接配置，自动实例化
    # summary = asyncio.run(test_storage(
    #     host="localhost",
    #     port=6379,
    #     graph_name="test_graph",
    #     config=config
    # ))