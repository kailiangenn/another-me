"""
FaissStore删除操作优化测试

验证优化后的删除功能：
1. 自动重建索引机制
2. 手动重建索引
3. 删除后的向量数一致性
"""

import os
import sys
import asyncio
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../ame"))

from foundation.storage.atomic.faiss_store import FaissVectorStore
from foundation.storage.atomic.vector_store import Vector


async def test_auto_rebuild_on_delete():
    """测试自动重建索引机制"""
    print("\n=== 测试 FaissStore - 自动重建索引 ===")
    
    store = FaissVectorStore(dimension=128, index_type="Flat")
    await store.connect()
    
    # 添加10个向量
    vectors = []
    for i in range(10):
        vectors.append(Vector(
            id=f"vec_{i}",
            embedding=np.random.rand(128).astype('float32'),
            metadata={"index": i}
        ))
    
    await store.add_vectors(vectors)
    initial_ntotal = store.index.ntotal
    print(f"✓ 初始向量数: {initial_ntotal}")
    
    # 删除4个向量（超过30%阈值，应触发重建）
    for i in range(4):
        await store.delete_vector(f"vec_{i}")
    
    # 检查是否自动重建
    final_ntotal = store.index.ntotal
    final_count = await store.count()
    
    print(f"✓ 删除后Faiss索引数: {final_ntotal}")
    print(f"✓ 删除后映射数: {final_count}")
    
    # 验证：删除超过30%应该触发重建，索引数应该等于映射数
    assert final_count == 6, f"映射数应该为6，实际{final_count}"
    assert final_ntotal == final_count, f"重建后索引数应该等于映射数: {final_ntotal} vs {final_count}"
    
    # 验证被删除的向量确实不存在
    for i in range(4):
        vec = await store.get_vector(f"vec_{i}")
        assert vec is None, f"vec_{i}应该已被删除"
    
    # 验证未删除的向量仍然存在
    for i in range(4, 10):
        vec = await store.get_vector(f"vec_{i}")
        assert vec is not None, f"vec_{i}应该仍然存在"
    
    await store.disconnect()
    print("✅ 自动重建索引测试通过")


async def test_manual_rebuild():
    """测试手动重建索引"""
    print("\n=== 测试 FaissStore - 手动重建索引 ===")
    
    store = FaissVectorStore(dimension=128, index_type="Flat")
    await store.connect()
    
    # 添加5个向量
    vectors = []
    for i in range(5):
        vectors.append(Vector(
            id=f"vec_{i}",
            embedding=np.random.rand(128).astype('float32'),
            metadata={"index": i}
        ))
    
    await store.add_vectors(vectors)
    
    # 删除1个向量（不足30%，不会自动重建）
    await store.delete_vector("vec_0")
    
    before_rebuild_ntotal = store.index.ntotal
    before_rebuild_count = await store.count()
    
    print(f"✓ 重建前Faiss索引数: {before_rebuild_ntotal}")
    print(f"✓ 重建前映射数: {before_rebuild_count}")
    
    # 手动重建
    result = await store.rebuild_if_needed(force=True)
    assert result, "手动重建失败"
    
    after_rebuild_ntotal = store.index.ntotal
    after_rebuild_count = await store.count()
    
    print(f"✓ 重建后Faiss索引数: {after_rebuild_ntotal}")
    print(f"✓ 重建后映射数: {after_rebuild_count}")
    
    # 验证重建成功
    assert after_rebuild_count == 4, f"重建后应该有4个向量，实际{after_rebuild_count}"
    assert after_rebuild_ntotal == after_rebuild_count, "重建后索引数应该等于映射数"
    
    await store.disconnect()
    print("✅ 手动重建索引测试通过")


async def test_delete_consistency():
    """测试删除后的一致性"""
    print("\n=== 测试 FaissStore - 删除一致性 ===")
    
    store = FaissVectorStore(dimension=128, index_type="Flat")
    await store.connect()
    
    # 添加向量
    base_vec = np.random.rand(128).astype('float32')
    vectors = []
    for i in range(8):
        embedding = base_vec + np.random.rand(128).astype('float32') * 0.1
        vectors.append(Vector(
            id=f"vec_{i}",
            embedding=embedding,
            metadata={"group": "A" if i < 4 else "B"}
        ))
    
    await store.add_vectors(vectors)
    
    # 删除组A的向量
    for i in range(4):
        await store.delete_vector(f"vec_{i}")
    
    # 检索应该只返回组B的向量
    query = base_vec
    results = await store.search(query, k=10)
    
    print(f"✓ 检索结果数: {len(results)}")
    for result in results:
        print(f"  - {result.id}: {result.metadata}")
        assert result.metadata["group"] == "B", f"{result.id}不应该被检索到"
    
    # 验证count准确性
    total_count = await store.count()
    group_b_count = await store.count(filter={"group": "B"})
    
    print(f"✓ 总向量数: {total_count}")
    print(f"✓ 组B向量数: {group_b_count}")
    
    assert total_count == 4, f"总数应该为4，实际{total_count}"
    assert group_b_count == 4, f"组B数量应该为4，实际{group_b_count}"
    
    await store.disconnect()
    print("✅ 删除一致性测试通过")


async def test_rebuild_preserves_metadata():
    """测试重建索引保留元数据"""
    print("\n=== 测试 FaissStore - 重建保留元数据 ===")
    
    store = FaissVectorStore(dimension=128, index_type="Flat")
    await store.connect()
    
    # 添加带元数据的向量
    vectors = []
    for i in range(10):
        vectors.append(Vector(
            id=f"vec_{i}",
            embedding=np.random.rand(128).astype('float32'),
            metadata={
                "name": f"Vector_{i}",
                "category": "test",
                "value": i * 10
            }
        ))
    
    await store.add_vectors(vectors)
    
    # 删除一些向量触发重建
    for i in range(5):
        await store.delete_vector(f"vec_{i}")
    
    # 验证剩余向量的元数据完整
    for i in range(5, 10):
        vec = await store.get_vector(f"vec_{i}")
        assert vec is not None, f"vec_{i}应该存在"
        assert vec.metadata["name"] == f"Vector_{i}", "名称元数据丢失"
        assert vec.metadata["category"] == "test", "类别元数据丢失"
        assert vec.metadata["value"] == i * 10, "数值元数据丢失"
        print(f"✓ vec_{i}元数据完整: {vec.metadata}")
    
    await store.disconnect()
    print("✅ 重建保留元数据测试通过")


async def test_batch_delete_with_rebuild():
    """测试批量删除触发重建"""
    print("\n=== 测试 FaissStore - 批量删除触发重建 ===")
    
    store = FaissVectorStore(dimension=128, index_type="Flat")
    await store.connect()
    
    # 添加20个向量
    vectors = []
    for i in range(20):
        vectors.append(Vector(
            id=f"vec_{i}",
            embedding=np.random.rand(128).astype('float32'),
            metadata={"index": i}
        ))
    
    await store.add_vectors(vectors)
    initial_ntotal = store.index.ntotal
    
    print(f"✓ 初始向量数: {initial_ntotal}")
    
    # 批量删除7个向量（35%，超过阈值）
    delete_ids = [f"vec_{i}" for i in range(7)]
    deleted_count = await store.delete_vectors(delete_ids)
    
    print(f"✓ 删除了{deleted_count}个向量")
    
    final_ntotal = store.index.ntotal
    final_count = await store.count()
    
    print(f"✓ 最终Faiss索引数: {final_ntotal}")
    print(f"✓ 最终映射数: {final_count}")
    
    # 验证批量删除触发重建
    assert deleted_count == 7, f"应该删除7个，实际{deleted_count}"
    assert final_count == 13, f"应该剩余13个，实际{final_count}"
    assert final_ntotal == final_count, "重建后索引数应该等于映射数"
    
    await store.disconnect()
    print("✅ 批量删除触发重建测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FaissStore删除优化测试套件")
    print("=" * 60)
    
    await test_auto_rebuild_on_delete()
    await test_manual_rebuild()
    await test_delete_consistency()
    await test_rebuild_preserves_metadata()
    await test_batch_delete_with_rebuild()
    
    print("\n" + "=" * 60)
    print("✅ 所有删除优化测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
