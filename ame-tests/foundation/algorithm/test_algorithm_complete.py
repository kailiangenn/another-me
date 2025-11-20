"""
Algorithm模块完整测试 - 测试TodoSorter拓扑排序、循环依赖检测、优先级评分

测试覆盖:
1. TodoSorter - 基础功能（优先级排序、截止日期计算）
2. TodoSorter - 拓扑排序（依赖关系处理）
3. TodoSorter - 循环依赖检测
4. TodoSorter - 权重配置和自定义评分
5. TodoSorter - 边界情况处理
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../ame"))

from foundation.algorithm.todo_sorter import (
    TodoSorter,
    TodoItem,
    Priority,
    TaskStatus,
    SortedTodoList,
)


# ============== 测试函数 ==============

def test_basic_priority_sorting():
    """测试基础优先级排序"""
    print("\n=== 测试 TodoSorter - 基础优先级排序 ===")
    
    sorter = TodoSorter()
    
    # 创建不同优先级的任务
    todos = [
        TodoItem(id="1", title="低优先级任务", priority=Priority.LOW),
        TodoItem(id="2", title="高优先级任务", priority=Priority.HIGH),
        TodoItem(id="3", title="中优先级任务", priority=Priority.MEDIUM),
        TodoItem(id="4", title="另一个高优先级", priority=Priority.HIGH),
    ]
    
    result = sorter.sort(todos, consider_dependencies=False)
    
    print(f"排序后的任务顺序:")
    for i, todo in enumerate(result.sorted_todos, 1):
        print(f"  {i}. {todo.title} ({todo.priority.value})")
    
    # 验证高优先级任务在前
    assert result.sorted_todos[0].priority == Priority.HIGH
    assert result.sorted_todos[1].priority == Priority.HIGH
    assert result.sorted_todos[-1].priority == Priority.LOW
    
    print("✅ 基础优先级排序测试通过")


def test_due_date_urgency():
    """测试截止日期紧急度计算"""
    print("\n=== 测试 TodoSorter - 截止日期紧急度 ===")
    
    sorter = TodoSorter()
    now = datetime.now()
    
    # 创建不同截止日期的任务
    todos = [
        TodoItem(
            id="1",
            title="一周后到期",
            priority=Priority.MEDIUM,
            due_date=now + timedelta(days=7)
        ),
        TodoItem(
            id="2",
            title="今天到期",
            priority=Priority.MEDIUM,
            due_date=now
        ),
        TodoItem(
            id="3",
            title="已过期",
            priority=Priority.MEDIUM,
            due_date=now - timedelta(days=1)
        ),
        TodoItem(
            id="4",
            title="明天到期",
            priority=Priority.MEDIUM,
            due_date=now + timedelta(days=1)
        ),
    ]
    
    result = sorter.sort(todos, consider_dependencies=False, consider_due_date=True)
    
    print(f"按紧急度排序:")
    for i, todo in enumerate(result.sorted_todos, 1):
        days = (todo.due_date - now).days if todo.due_date else None
        print(f"  {i}. {todo.title} (还剩 {days} 天)")
    
    # 验证已过期或今天到期的任务最紧急（由于综合评分，顺序可能有小差异）
    # 验证最紧急的任务在前两位
    assert result.sorted_todos[0].id in ["2", "3"], "今天或已过期任务应该最优先"
    assert result.sorted_todos[1].id in ["2", "3"], "今天或已过期任务应该在前两位"
    # 验证一周后到期的排在最后
    assert result.sorted_todos[-1].id == "1", "一周后到期的任务应该最不紧急"
    
    print("✅ 截止日期紧急度测试通过")


def test_topological_sort_basic():
    """测试基础拓扑排序（依赖关系）"""
    print("\n=== 测试 TodoSorter - 基础拓扑排序 ===")
    
    sorter = TodoSorter()
    
    # 创建有依赖关系的任务
    # Task2 依赖 Task1
    # Task3 依赖 Task2
    # Task4 独立
    todos = [
        TodoItem(id="1", title="基础任务", priority=Priority.MEDIUM),
        TodoItem(id="2", title="依赖任务1", priority=Priority.HIGH, dependencies=["1"]),
        TodoItem(id="3", title="依赖任务2", priority=Priority.HIGH, dependencies=["2"]),
        TodoItem(id="4", title="独立任务", priority=Priority.LOW),
    ]
    
    result = sorter.sort(todos, consider_dependencies=True)
    
    print(f"拓扑排序后的任务顺序:")
    for i, todo in enumerate(result.sorted_todos, 1):
        deps = f"依赖: {todo.dependencies}" if todo.dependencies else "无依赖"
        print(f"  {i}. {todo.title} ({deps})")
    
    # 验证依赖顺序正确
    # Task1 必须在 Task2 之前
    # Task2 必须在 Task3 之前
    ids = [t.id for t in result.sorted_todos]
    assert ids.index("1") < ids.index("2"), "Task1应该在Task2之前"
    assert ids.index("2") < ids.index("3"), "Task2应该在Task3之前"
    
    # 验证没有被阻塞的任务
    assert len(result.blocked_todos) == 0, "不应该有被阻塞的任务"
    
    print("✅ 基础拓扑排序测试通过")


def test_circular_dependency_detection():
    """测试循环依赖检测"""
    print("\n=== 测试 TodoSorter - 循环依赖检测 ===")
    
    sorter = TodoSorter()
    
    # 创建循环依赖: Task1 -> Task2 -> Task3 -> Task1
    todos = [
        TodoItem(id="1", title="任务1", priority=Priority.HIGH, dependencies=["3"]),
        TodoItem(id="2", title="任务2", priority=Priority.HIGH, dependencies=["1"]),
        TodoItem(id="3", title="任务3", priority=Priority.HIGH, dependencies=["2"]),
        TodoItem(id="4", title="独立任务", priority=Priority.MEDIUM),
    ]
    
    result = sorter.sort(todos, consider_dependencies=True)
    
    print(f"排序结果:")
    print(f"  成功排序的任务数: {len(result.sorted_todos)}")
    print(f"  被阻塞的任务数: {len(result.blocked_todos)}")
    
    if result.blocked_todos:
        print(f"  被阻塞的任务:")
        for todo in result.blocked_todos:
            print(f"    - {todo.title} (依赖: {todo.dependencies})")
    
    # 验证循环依赖被检测到
    assert len(result.blocked_todos) == 3, "应该检测到3个循环依赖的任务"
    assert len(result.sorted_todos) == 1, "只有独立任务应该被成功排序"
    assert result.sorted_todos[0].id == "4", "独立任务应该被排序"
    
    print("✅ 循环依赖检测测试通过")


def test_partial_dependency_cycle():
    """测试部分循环依赖"""
    print("\n=== 测试 TodoSorter - 部分循环依赖 ===")
    
    sorter = TodoSorter()
    
    # 部分循环: Task1 -> Task2 -> Task1, Task3独立, Task4依赖Task3
    todos = [
        TodoItem(id="1", title="任务1", priority=Priority.HIGH, dependencies=["2"]),
        TodoItem(id="2", title="任务2", priority=Priority.HIGH, dependencies=["1"]),
        TodoItem(id="3", title="任务3", priority=Priority.MEDIUM),
        TodoItem(id="4", title="任务4", priority=Priority.LOW, dependencies=["3"]),
    ]
    
    result = sorter.sort(todos, consider_dependencies=True)
    
    print(f"排序结果:")
    for todo in result.sorted_todos:
        print(f"  ✓ {todo.title}")
    
    print(f"被阻塞的任务:")
    for todo in result.blocked_todos:
        print(f"  ✗ {todo.title}")
    
    # 验证结果
    assert len(result.blocked_todos) == 2, "Task1和Task2应该被阻塞"
    assert len(result.sorted_todos) == 2, "Task3和Task4应该被成功排序"
    
    # 验证Task3在Task4之前
    ids = [t.id for t in result.sorted_todos]
    assert ids.index("3") < ids.index("4"), "Task3应该在Task4之前"
    
    print("✅ 部分循环依赖测试通过")


def test_weight_configuration():
    """测试权重配置"""
    print("\n=== 测试 TodoSorter - 权重配置 ===")
    
    now = datetime.now()
    
    # 创建测试任务
    todos = [
        TodoItem(
            id="1",
            title="高优先级但不紧急",
            priority=Priority.HIGH,
            due_date=now + timedelta(days=30)
        ),
        TodoItem(
            id="2",
            title="低优先级但很紧急",
            priority=Priority.LOW,
            due_date=now
        ),
    ]
    
    # 测试默认权重（紧急度40%, 重要性40%, 依赖20%）
    print("\n--- 默认权重 (紧急度40%, 重要性40%) ---")
    sorter1 = TodoSorter()
    result1 = sorter1.sort(todos.copy(), consider_dependencies=False)
    print(f"  第一位: {result1.sorted_todos[0].title}")
    
    # 测试高紧急度权重（紧急度80%, 重要性10%, 依赖10%）
    print("\n--- 高紧急度权重 (紧急度80%, 重要性10%) ---")
    sorter2 = TodoSorter(urgency_weight=0.8, importance_weight=0.1, dependency_weight=0.1)
    result2 = sorter2.sort(todos.copy(), consider_dependencies=False)
    print(f"  第一位: {result2.sorted_todos[0].title}")
    
    # 测试高重要性权重（重要性80%, 紧急度10%, 依赖10%）
    print("\n--- 高重要性权重 (重要性80%, 紧急度10%) ---")
    sorter3 = TodoSorter(urgency_weight=0.1, importance_weight=0.8, dependency_weight=0.1)
    result3 = sorter3.sort(todos.copy(), consider_dependencies=False)
    print(f"  第一位: {result3.sorted_todos[0].title}")
    
    # 验证不同权重产生不同结果
    assert result2.sorted_todos[0].id == "2", "高紧急度权重应该优先紧急任务"
    assert result3.sorted_todos[0].id == "1", "高重要性权重应该优先重要任务"
    
    print("✅ 权重配置测试通过")


def test_custom_scorer():
    """测试自定义评分函数"""
    print("\n=== 测试 TodoSorter - 自定义评分函数 ===")
    
    # 定义自定义评分函数：标题长度越短分数越高
    def custom_scorer(todo: TodoItem) -> float:
        return 100 - len(todo.title)
    
    sorter = TodoSorter()
    sorter.set_custom_scorer(custom_scorer)
    
    todos = [
        TodoItem(id="1", title="非常非常非常长的任务标题", priority=Priority.HIGH),
        TodoItem(id="2", title="短标题", priority=Priority.LOW),
        TodoItem(id="3", title="中等长度的标题", priority=Priority.MEDIUM),
    ]
    
    result = sorter.sort(todos, consider_dependencies=False)
    
    print(f"自定义评分排序结果:")
    for i, todo in enumerate(result.sorted_todos, 1):
        print(f"  {i}. {todo.title} (长度: {len(todo.title)})")
    
    # 验证按标题长度排序
    assert result.sorted_todos[0].id == "2", "最短标题应该排第一"
    assert result.sorted_todos[-1].id == "1", "最长标题应该排最后"
    
    print("✅ 自定义评分函数测试通过")


def test_priority_grouping():
    """测试优先级分组"""
    print("\n=== 测试 TodoSorter - 优先级分组 ===")
    
    sorter = TodoSorter()
    
    todos = [
        TodoItem(id="1", title="高1", priority=Priority.HIGH),
        TodoItem(id="2", title="低1", priority=Priority.LOW),
        TodoItem(id="3", title="中1", priority=Priority.MEDIUM),
        TodoItem(id="4", title="高2", priority=Priority.HIGH),
        TodoItem(id="5", title="中2", priority=Priority.MEDIUM),
    ]
    
    result = sorter.sort(todos, consider_dependencies=False)
    
    print(f"优先级分组:")
    for priority, tasks in result.groups.items():
        print(f"  {priority}: {len(tasks)} 个任务")
        for task in tasks:
            print(f"    - {task.title}")
    
    # 验证分组正确
    assert len(result.groups["high"]) == 2, "应该有2个高优先级任务"
    assert len(result.groups["medium"]) == 2, "应该有2个中优先级任务"
    assert len(result.groups["low"]) == 1, "应该有1个低优先级任务"
    
    print("✅ 优先级分组测试通过")


def test_completed_tasks_filtering():
    """测试已完成任务过滤"""
    print("\n=== 测试 TodoSorter - 已完成任务过滤 ===")
    
    sorter = TodoSorter()
    
    todos = [
        TodoItem(id="1", title="待办任务1", priority=Priority.HIGH, status=TaskStatus.PENDING),
        TodoItem(id="2", title="已完成任务", priority=Priority.HIGH, status=TaskStatus.COMPLETED),
        TodoItem(id="3", title="待办任务2", priority=Priority.MEDIUM, status=TaskStatus.PENDING),
        TodoItem(id="4", title="进行中任务", priority=Priority.LOW, status=TaskStatus.IN_PROGRESS),
    ]
    
    result = sorter.sort(todos, consider_dependencies=False)
    
    print(f"排序结果 (已完成任务已过滤):")
    for todo in result.sorted_todos:
        print(f"  - {todo.title} ({todo.status.value})")
    
    # 验证已完成任务被过滤
    assert len(result.sorted_todos) == 3, "应该只有3个未完成任务"
    assert all(t.status != TaskStatus.COMPLETED for t in result.sorted_todos), "不应包含已完成任务"
    
    print("✅ 已完成任务过滤测试通过")


def test_complex_dependency_chain():
    """测试复杂依赖链"""
    print("\n=== 测试 TodoSorter - 复杂依赖链 ===")
    
    sorter = TodoSorter()
    
    # 创建复杂依赖结构:
    #     Task1
    #    /     \
    # Task2   Task3
    #    \     /
    #    Task4
    todos = [
        TodoItem(id="1", title="根任务", priority=Priority.HIGH),
        TodoItem(id="2", title="分支任务A", priority=Priority.HIGH, dependencies=["1"]),
        TodoItem(id="3", title="分支任务B", priority=Priority.HIGH, dependencies=["1"]),
        TodoItem(id="4", title="汇聚任务", priority=Priority.MEDIUM, dependencies=["2", "3"]),
    ]
    
    result = sorter.sort(todos, consider_dependencies=True)
    
    print(f"复杂依赖链排序结果:")
    for i, todo in enumerate(result.sorted_todos, 1):
        print(f"  {i}. {todo.title}")
    
    ids = [t.id for t in result.sorted_todos]
    
    # 验证依赖关系
    assert ids.index("1") < ids.index("2"), "Task1应该在Task2之前"
    assert ids.index("1") < ids.index("3"), "Task1应该在Task3之前"
    assert ids.index("2") < ids.index("4"), "Task2应该在Task4之前"
    assert ids.index("3") < ids.index("4"), "Task3应该在Task4之前"
    assert len(result.blocked_todos) == 0, "不应有被阻塞的任务"
    
    print("✅ 复杂依赖链测试通过")


def test_empty_todo_list():
    """测试空任务列表"""
    print("\n=== 测试 TodoSorter - 空任务列表 ===")
    
    sorter = TodoSorter()
    result = sorter.sort([], consider_dependencies=True)
    
    print(f"空列表排序结果:")
    print(f"  任务数: {len(result.sorted_todos)}")
    print(f"  被阻塞数: {len(result.blocked_todos)}")
    
    assert len(result.sorted_todos) == 0
    assert len(result.blocked_todos) == 0
    assert result.metadata["total"] == 0
    
    print("✅ 空任务列表测试通过")


def test_nonexistent_dependencies():
    """测试不存在的依赖"""
    print("\n=== 测试 TodoSorter - 不存在的依赖 ===")
    
    sorter = TodoSorter()
    
    # Task2依赖不存在的Task999
    todos = [
        TodoItem(id="1", title="正常任务", priority=Priority.HIGH),
        TodoItem(id="2", title="有无效依赖的任务", priority=Priority.HIGH, dependencies=["999"]),
    ]
    
    result = sorter.sort(todos, consider_dependencies=True)
    
    print(f"排序结果:")
    for todo in result.sorted_todos:
        print(f"  - {todo.title}")
    
    # 验证不存在的依赖被忽略，任务正常排序
    assert len(result.sorted_todos) == 2, "两个任务都应该被排序"
    assert len(result.blocked_todos) == 0, "不应有被阻塞的任务"
    
    print("✅ 不存在的依赖测试通过")


def test_weight_update():
    """测试动态更新权重"""
    print("\n=== 测试 TodoSorter - 动态更新权重 ===")
    
    sorter = TodoSorter(urgency_weight=0.5, importance_weight=0.3, dependency_weight=0.2)
    
    print(f"初始权重:")
    print(f"  紧急度: {sorter.urgency_weight:.2f}")
    print(f"  重要性: {sorter.importance_weight:.2f}")
    print(f"  依赖关系: {sorter.dependency_weight:.2f}")
    
    # 更新权重
    sorter.set_weights(urgency_weight=0.1, importance_weight=0.7, dependency_weight=0.2)
    
    print(f"\n更新后权重:")
    print(f"  紧急度: {sorter.urgency_weight:.2f}")
    print(f"  重要性: {sorter.importance_weight:.2f}")
    print(f"  依赖关系: {sorter.dependency_weight:.2f}")
    
    # 验证权重更新成功
    assert abs(sorter.urgency_weight - 0.1) < 0.01
    assert abs(sorter.importance_weight - 0.7) < 0.01
    assert abs(sorter.dependency_weight - 0.2) < 0.01
    
    # 验证权重和为1
    total = sorter.urgency_weight + sorter.importance_weight + sorter.dependency_weight
    assert abs(total - 1.0) < 0.001, "权重之和应该为1"
    
    print("✅ 动态更新权重测试通过")


# ============== 主测试函数 ==============

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Algorithm模块完整测试套件")
    print("=" * 60)
    
    test_basic_priority_sorting()
    test_due_date_urgency()
    test_topological_sort_basic()
    test_circular_dependency_detection()
    test_partial_dependency_cycle()
    test_weight_configuration()
    test_custom_scorer()
    test_priority_grouping()
    test_completed_tasks_filtering()
    test_complex_dependency_chain()
    test_empty_todo_list()
    test_nonexistent_dependencies()
    test_weight_update()
    
    print("\n" + "=" * 60)
    print("✅ 所有Algorithm测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
