"""LLM配置测试模块

提供LLM调用器的完整测试功能。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from loguru import logger
import asyncio


from ame.foundation.llm import (
    LLMCallerBase,
    create_user_message,
    CallMode,
)


@dataclass
class TestConfig:
    """测试配置"""
    test_connectivity: bool = True
    test_stream: bool = True
    test_complete: bool = True
    test_token_estimation: bool = True
    test_error_handling: bool = False


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
    
    @property
    def all_passed(self) -> bool:
        """是否所有测试都通过（别名）"""
        return self.success


class LLMTester:
    """LLM测试器"""
    
    def __init__(self, caller: LLMCallerBase):
        """初始化
        
        Args:
            caller: 已实例化配置的LLM调用器
        """
        if not isinstance(caller, LLMCallerBase):
            raise TypeError("caller必须是LLMCallerBase的子类实例")
        self.caller = caller
    
    async def test_connectivity(self) -> TestResult:
        """测试连通性"""
        try:
            if not self.caller.is_configured():
                return TestResult(
                    success=False,
                    message="调用器未正确配置",
                    error="未配置API密钥或其他必要参数"
                )
            
            messages = [create_user_message("Hi")]
            response = await self.caller.generate(messages, max_tokens=10)
            
            return TestResult(
                success=True,
                message="连通性测试通过",
                details={
                    "model": response.model,
                    "response_length": len(response.content),
                    "total_tokens": response.total_tokens
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="连通性测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_stream(self) -> TestResult:
        """测试流式输出"""
        try:
            messages = [create_user_message("用一句话介绍AI")]
            chunks = []
            
            async for chunk in self.caller.generate_stream(messages, max_tokens=50):
                chunks.append(chunk)
            
            full_text = "".join(chunks)
            
            return TestResult(
                success=True,
                message="流式输出测试通过",
                details={
                    "chunks_count": len(chunks),
                    "total_length": len(full_text),
                    "first_chunk": chunks[0] if chunks else "",
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="流式输出测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_complete(self) -> TestResult:
        """测试完整输出"""
        try:
            messages = [create_user_message("1+1等于几?")]
            response = await self.caller.generate(messages, max_tokens=20)
            
            return TestResult(
                success=True,
                message="完整输出测试通过",
                details={
                    "content": response.content[:100],
                    "model": response.model,
                    "finish_reason": response.finish_reason,
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                }
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="完整输出测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    def test_token_estimation(self) -> TestResult:
        """测试Token估算"""
        try:
            test_texts = [
                "Hello",
                "你好，世界",
                "This is a longer text with multiple words.",
                "这是一段包含中英文的测试文本。Mixed content test."
            ]
            
            results = {}
            for text in test_texts:
                tokens = self.caller.estimate_tokens(text)
                results[text[:20]] = tokens
            
            return TestResult(
                success=True,
                message="Token估算测试通过",
                details=results
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="Token估算测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def test_error_handling(self) -> TestResult:
        """测试错误处理"""
        try:
            # 测试超长输入
            long_text = "测试" * 10000
            messages = [create_user_message(long_text)]
            
            try:
                await self.caller.generate(messages, max_tokens=10)
                error_handled = False
            except Exception:
                error_handled = True
            
            return TestResult(
                success=True,
                message="错误处理测试通过",
                details={"handles_errors": error_handled}
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="错误处理测试失败",
                error=f"{type(e).__name__}: {e}"
            )
    
    async def run_tests(self, config: TestConfig) -> TestSummary:
        """运行所有测试
        
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
        
        if config.test_stream:
            logger.info("[2/5] 测试流式输出...")
            results["stream"] = await self.test_stream()
            self._print_result("流式输出", results["stream"])
        
        if config.test_complete:
            logger.info("[3/5] 测试完整输出...")
            results["complete"] = await self.test_complete()
            self._print_result("完整输出", results["complete"])
        
        if config.test_token_estimation:
            logger.info("[4/5] 测试Token估算...")
            results["token_estimation"] = self.test_token_estimation()
            self._print_result("Token估算", results["token_estimation"])
        
        if config.test_error_handling:
            logger.info("[5/5] 测试错误处理...")
            results["error_handling"] = await self.test_error_handling()
            self._print_result("错误处理", results["error_handling"])
        
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


async def test_llm_callers(
    caller: Optional[LLMCallerBase] = None,
    config: Optional[TestConfig] = None,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    base_url: Optional[str] = None,
    **kwargs
) -> TestSummary:
    """测试LLM配置
    
    支持两种使用方式：
    1. 传入已实例化的caller
    2. 传入api_key等参数，自动实例化OpenAICaller
    
    Args:
        caller: 已实例化的LLM调用器（优先使用）
        config: 测试配置，默认执行所有测试
        api_key: OpenAI API密钥（当caller为None时使用）
        model: 模型名称
        base_url: API基础URL
        **kwargs: 其他OpenAI参数
        
    Returns:
        测试汇总结果
        
    Raises:
        ValueError: 既未提供caller也未提供api_key
    """
    # 确定使用的caller
    if caller is None:
        if api_key is None:
            raise ValueError("必须提供caller或api_key参数")
        
        from ame.foundation.llm import OpenAICaller
        logger.info(f"使用默认OpenAICaller实例化，模型: {model}")
        caller = OpenAICaller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs
        )
    else:
        logger.info(f"使用用户提供的caller: {type(caller).__name__}")
    
    if config is None:
        config = TestConfig()
    
    tester = LLMTester(caller)
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
    # 示例用法1: 直接传入已实例化的caller
    from ame.foundation.llm import OpenAICaller
    
    caller = OpenAICaller(
        api_key="your-api-key",
        model="gpt-3.5-turbo",
        base_url="https://api.openai.com/v1"
    )
    
    config = TestConfig(
        test_connectivity=True,
        test_stream=True,
        test_complete=True,
        test_token_estimation=True,
        test_error_handling=False
    )
    
    summary = asyncio.run(test_llm_callers(caller=caller, config=config))
    print(f"\n测试结果: {'成功' if summary.success else '失败'}")
    
    # 示例用法2: 仅传入API配置，自动实例化
    # summary = asyncio.run(test_llm(
    #     api_key="your-api-key",
    #     model="gpt-3.5-turbo",
    #     base_url="https://api.openai.com/v1",
    #     config=config
    # ))