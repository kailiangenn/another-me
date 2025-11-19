# Storage 模块测试

本目录包含Storage模块的测试文件。

## 📁 测试文件

### 1. `test_storage_basic.py` - 基础功能测试

测试内容：
- ✅ 数据模型创建（GraphNode, GraphEdge）
- ✅ 边的时间有效性判断
- ✅ Schema验证
- ✅ 验证器功能
- ✅ 领域标签分类

**运行方式**：
```bash
cd /Users/kailiangsennew/Desktop/another-me
python ame-tests/foundation/storage/test_storage_basic.py
```

**依赖**：无需外部服务，纯Python测试

---

### 2. `test_pipeline.py` - Pipeline集成测试

测试内容：
- ✅ LifeGraphPipeline初始化
- ✅ WorkGraphPipeline初始化
- ✅ 节点创建和查询
- ✅ 关系创建（含时间属性）
- ✅ 边的时间标记（失效）
- ✅ 查询活跃关系
- ✅ 批量操作
- ✅ Merge操作（去重）
- ✅ 工作图谱任务创建
- ✅ 领域隔离验证

**运行方式**：
```bash
cd /Users/kailiangsennew/Desktop/another-me
python ame-tests/foundation/storage/test_pipeline.py
```

**依赖**：需要FalkorDB服务

---

## 🚀 快速开始

### 准备工作

#### 1. 启动FalkorDB（必需）

**使用Docker**：
```bash
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest
```

**使用Docker Compose**：
```yaml
# docker-compose.yml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data

volumes:
  falkordb_data:
```

启动：
```bash
docker-compose up -d falkordb
```

#### 2. 验证FalkorDB运行

```bash
# 使用redis-cli测试
redis-cli -h localhost -p 6379 ping
# 应返回: PONG
```

---

### 运行测试

#### 方式1：使用默认配置

如果FalkorDB在本地运行（localhost:6379），直接运行：

```bash
# 基础测试（无需FalkorDB）
python ame-tests/foundation/storage/test_storage_basic.py

# Pipeline测试（需要FalkorDB）
python ame-tests/foundation/storage/test_pipeline.py
```

#### 方式2：自定义FalkorDB地址

编辑 `test_pipeline.py` 文件顶部的配置：

```python
# ===== 配置区域 =====
FALKORDB_HOST = "your-host"      # 修改为你的FalkorDB地址
FALKORDB_PORT = 6379             # 修改端口（如需要）
FALKORDB_PASSWORD = "password"   # 设置密码（如需要）
```

然后运行：
```bash
python ame-tests/foundation/storage/test_pipeline.py
```

---

## 📊 测试覆盖范围

### Core层测试
- ✅ GraphNode 创建和属性
- ✅ GraphEdge 创建和时间属性
- ✅ 时间有效性判断（is_valid_at, is_currently_valid, duration）
- ✅ Schema验证（必需属性检查）
- ✅ 数据验证器

### Atomic层测试（通过Pipeline间接测试）
- ✅ FalkorDB连接和健康检查
- ✅ 节点CRUD操作
- ✅ 边CRUD操作
- ✅ 时间范围查询（find_valid_edges_at）
- ✅ 图遍历（find_edges, get_neighbors）

### Pipeline层测试
- ✅ 生活图谱初始化
- ✅ 工作图谱初始化
- ✅ 领域隔离验证
- ✅ 批量操作（batch_create_nodes/edges）
- ✅ Merge操作（merge_or_create_node）
- ✅ 时间便捷方法（mark_edge_as_invalid, get_active_relationships）

---

## ⚠️ 注意事项

### 1. 测试数据隔离

测试会在FalkorDB中创建以下Graph：
- `life_graph` - 生活图谱
- `work_graph` - 工作图谱

**清理测试数据**：
```bash
# 连接到FalkorDB
redis-cli -h localhost -p 6379

# 删除测试图谱
GRAPH.DELETE life_graph
GRAPH.DELETE work_graph
```

### 2. 并发测试

如果需要并发测试，建议为每个测试会话使用独立的Graph名称。

### 3. 性能测试

当前测试关注功能正确性，如需性能测试，请参考：
```
ame-back/tests/performance/test_graph_performance.py
```

---

## 🐛 故障排查

### 问题1：连接FalkorDB失败

**错误信息**：
```
ConnectionError: 无法连接到FalkorDB
```

**解决方法**：
1. 检查FalkorDB是否启动：`docker ps | grep falkordb`
2. 检查端口是否开放：`telnet localhost 6379`
3. 检查配置参数是否正确

### 问题2：falkordb未安装

**错误信息**：
```
ImportError: falkordb未安装
```

**解决方法**：
```bash
pip install falkordb
```

### 问题3：测试中断

如果测试中断，可能有残留连接，重启FalkorDB：
```bash
docker restart falkordb
```

---

## 📝 扩展测试

### 添加新测试

在 `test_pipeline.py` 中添加新的测试函数：

```python
async def test_your_feature():
    """测试你的功能"""
    print("\n测试你的功能...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 你的测试代码
        pass
        
        print("✓ 测试通过")
        
    finally:
        await pipeline.store.disconnect()

# 在 run_all_tests() 中调用
async def run_all_tests():
    # ... 其他测试
    await test_your_feature()
```

---

## 📚 参考文档

- [Storage模块使用文档](../../ame/foundation/storage/README.md)
- [FalkorDB官方文档](https://docs.falkordb.com/)
- [测试框架说明](../README.md)
