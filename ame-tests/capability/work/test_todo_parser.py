"""
Work场景TodoParser测试

测试TodoParser的待办解析功能
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ame.capability.work.todo_parser import TodoParser
from ame.foundation.algorithm import Priority, TaskStatus


def test_checkbox_format():
    """测试checkbox格式解析"""
    print("测试1: Checkbox格式 - [ ] 任务")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    - [ ] 实现登录功能
    - [ ] 编写单元测试
    - [ ] 更新文档
    """
    
    todos = parser._parse_by_rules(text)
    
    assert len(todos) == 3, f"Expected 3 todos, got {len(todos)}"
    assert todos[0].title == "实现登录功能"
    assert todos[1].title == "编写单元测试"
    assert todos[2].title == "更新文档"
    
    for todo in todos:
        assert todo.status == TaskStatus.PENDING
        assert todo.id.startswith("task_")
        print(f"  ✓ {todo.title}")
    
    print("✅ 测试1通过\n")


def test_todo_format():
    """测试TODO格式解析"""
    print("测试2: TODO格式")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    TODO: 修复bug
    TODO: 优化性能
    """
    
    todos = parser._parse_by_rules(text)
    
    assert len(todos) == 2
    assert "修复bug" in todos[0].title
    assert "优化性能" in todos[1].title
    print(f"  ✓ 解析到 {len(todos)} 个TODO任务")
    
    print("✅ 测试2通过\n")


def test_numbered_format():
    """测试数字列表格式"""
    print("测试3: 数字列表格式")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    1. 设计数据库Schema
    2. 实现API接口
    3. 前端对接
    """
    
    todos = parser._parse_by_rules(text)
    
    assert len(todos) == 3
    assert todos[0].title == "设计数据库Schema"
    assert todos[1].title == "实现API接口"
    assert todos[2].title == "前端对接"
    print(f"  ✓ 解析到 {len(todos)} 个数字列表任务")
    
    print("✅ 测试3通过\n")


def test_priority_extraction():
    """测试优先级提取"""
    print("测试4: 优先级提取")
    
    parser = TodoParser(llm_caller=None)
    
    test_cases = [
        ("紧急修复登录bug", Priority.HIGH),
        ("重要功能开发", Priority.HIGH),
        ("低优先级的文档更新", Priority.LOW),
        ("普通任务", Priority.MEDIUM),
    ]
    
    for text, expected_priority in test_cases:
        priority = parser._extract_priority(text)
        assert priority == expected_priority, \
            f"Text: '{text}', Expected: {expected_priority}, Got: {priority}"
        print(f"  ✓ '{text}' -> {priority.value}")
    
    print("✅ 测试4通过\n")


def test_due_date_extraction():
    """测试截止日期提取"""
    print("测试5: 截止日期提取")
    
    parser = TodoParser(llm_caller=None)
    
    # 测试相对时间
    test_cases = [
        ("今天完成任务", 0),  # 今天
        ("明天提交代码", 1),  # 明天
    ]
    
    for text, days_offset in test_cases:
        due_date = parser._extract_due_date(text)
        if due_date:
            expected_date = datetime.now() + timedelta(days=days_offset)
            # 只比较日期部分
            assert due_date.date() == expected_date.date(), \
                f"Text: '{text}', Expected: {expected_date.date()}, Got: {due_date.date()}"
            print(f"  ✓ '{text}' -> {due_date.date()}")
        else:
            print(f"  ⚠ '{text}' -> 无法识别日期")
    
    # 测试具体日期
    text_with_date = "2024-12-31之前完成"
    due_date = parser._extract_due_date(text_with_date)
    if due_date:
        assert due_date.year == 2024
        assert due_date.month == 12
        assert due_date.day == 31
        print(f"  ✓ 具体日期: {due_date.date()}")
    
    print("✅ 测试5通过\n")


def test_mixed_formats():
    """测试混合格式"""
    print("测试6: 混合格式")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    待办事项:
    - [ ] 紧急: 修复登录bug (今天)
    1. 实现新功能
    TODO: 更新文档
    - 优化性能
    """
    
    todos = parser._parse_by_rules(text)
    
    assert len(todos) >= 3, f"Expected at least 3 todos, got {len(todos)}"
    
    # 检查是否正确提取了优先级和日期
    has_high_priority = any(t.priority == Priority.HIGH for t in todos)
    has_due_date = any(t.due_date is not None for t in todos)
    
    print(f"  ✓ 解析到 {len(todos)} 个任务")
    print(f"  ✓ 包含高优先级任务: {has_high_priority}")
    print(f"  ✓ 包含截止日期: {has_due_date}")
    
    print("✅ 测试6通过\n")


def test_empty_input():
    """测试空输入"""
    print("测试7: 空输入处理")
    
    parser = TodoParser(llm_caller=None)
    
    # 空字符串
    todos = parser._parse_by_rules("")
    assert len(todos) == 0, "空字符串应返回空列表"
    print("  ✓ 空字符串返回空列表")
    
    # 只有空格和换行
    todos = parser._parse_by_rules("\n\n   \n  ")
    assert len(todos) == 0
    print("  ✓ 纯空白返回空列表")
    
    # 无效格式
    todos = parser._parse_by_rules("这是一段普通文本，没有待办格式")
    assert len(todos) == 0
    print("  ✓ 无效格式返回空列表")
    
    print("✅ 测试7通过\n")


def test_complex_tasks():
    """测试复杂任务描述"""
    print("测试8: 复杂任务描述")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    - [ ] 实现用户认证模块（包括登录、注册、密码重置）
    - [ ] 编写API文档（Swagger格式）并部署到服务器
    """
    
    todos = parser._parse_by_rules(text)
    
    assert len(todos) == 2
    assert "用户认证" in todos[0].title
    assert "API文档" in todos[1].title
    
    # 标题应该包含完整描述（包括括号内容）
    assert "登录" in todos[0].title or "注册" in todos[0].title
    print(f"  ✓ 任务1: {todos[0].title}")
    print(f"  ✓ 任务2: {todos[1].title}")
    
    print("✅ 测试8通过\n")


def test_task_id_generation():
    """测试任务ID生成"""
    print("测试9: 任务ID生成")
    
    parser = TodoParser(llm_caller=None)
    
    text = """
    - [ ] 任务1
    - [ ] 任务2
    - [ ] 任务3
    """
    
    todos = parser._parse_by_rules(text)
    
    # 检查ID唯一性
    ids = [todo.id for todo in todos]
    assert len(ids) == len(set(ids)), "任务ID应该唯一"
    
    # 检查ID格式
    for todo in todos:
        assert todo.id.startswith("task_"), f"ID格式错误: {todo.id}"
        assert len(todo.id) > 10, f"ID长度不足: {todo.id}"
    
    print(f"  ✓ 生成了 {len(ids)} 个唯一ID")
    print(f"  ✓ ID示例: {ids[0]}")
    
    print("✅ 测试9通过\n")


def test_default_values():
    """测试默认值设置"""
    print("测试10: 默认值设置")
    
    parser = TodoParser(llm_caller=None)
    
    text = "- [ ] 简单任务"
    
    todos = parser._parse_by_rules(text)
    assert len(todos) == 1
    
    todo = todos[0]
    
    # 检查默认值
    assert todo.status == TaskStatus.PENDING, f"默认状态应为PENDING"
    assert todo.priority == Priority.MEDIUM, f"默认优先级应为MEDIUM"
    assert todo.description == "", f"默认描述应为空"
    assert len(todo.dependencies) == 0, f"默认依赖应为空列表"
    assert todo.created_at is not None, f"应有创建时间"
    
    print("  ✓ 状态: PENDING")
    print("  ✓ 优先级: MEDIUM")
    print("  ✓ 描述: 空")
    print("  ✓ 依赖: []")
    print(f"  ✓ 创建时间: {todo.created_at}")
    
    print("✅ 测试10通过\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("TodoParser测试")
    print("=" * 60)
    print()
    
    try:
        test_checkbox_format()
        test_todo_format()
        test_numbered_format()
        test_priority_extraction()
        test_due_date_extraction()
        test_mixed_formats()
        test_empty_input()
        test_complex_tasks()
        test_task_id_generation()
        test_default_values()
        
        print("=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
