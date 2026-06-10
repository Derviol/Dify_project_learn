# Dify 平台迁移方案

> **职责**：定义从 Coze 平台到 Dify 平台的完整迁移映射与实施策略
> **说明**：本项目为学习练习用途，迁移方案中的数据和配置均为虚拟。
> **关联**：[README.md](./README.md)、[07-Dify工作流与Agent设计.md](./07-Dify工作流与Agent设计.md)

---

## 1. 迁移总览

### 1.1 迁移范围

| Coze 组件 | 数量 | 迁移目标 | 迁移方式 |
|-----------|:----:|----------|----------|
| 父 Agent（乐乐总机） | 1 | Dify Agent / Chatflow | 重建 Prompt + 路由逻辑 |
| 子 Agent 1（游玩规划师） | 1 | Dify Agent | 重建 Prompt + 工作流绑定 |
| 子 Agent 2（园区百事通） | 1 | Dify Agent | 重建 Prompt + 工作流绑定 |
| Workflow | 6 | Dify Workflow | 节点逐一映射重建 |
| Knowledge Base | 7 | Dify Knowledge | 文档导入 + 向量化 |
| Database | 5 表 | 外部 MySQL | 数据迁移 + API 工具对接 |
| Plugin | - | Dify 自定义工具 | 后端 API 封装为工具 |

### 1.2 迁移策略

采用**渐进式迁移**策略：

```
Phase 1: 基础设施搭建（Dify 环境 + 后端骨架）
    │
Phase 2: 知识库迁移（7 个知识文档导入 Dify）
    │
Phase 3: Agent 重建（3 个 Agent Prompt + 配置）
    │
Phase 4: Workflow 重建（6 个工作流）
    │
Phase 5: 工具对接（后端 API → Dify 自定义工具）
    │
Phase 6: 集成测试 + 优化
```

---

## 2. Agent 迁移映射

### 2.1 架构差异

**Coze 多 Agent 模式**：
- 父 Agent 通过"Bot 间调用"路由到子 Agent
- 子 Agent 是独立的 Bot，通过 Coze 内部机制通信
- 共享 Database 和 Knowledge

**Dify Agent 模式**：
- 方案 A：使用 **Chatflow** 构建统一对话流，用条件分支实现路由
- 方案 B：使用 **多 Agent 编排**（Dify 1.x+），一个主编排 Agent + 子 Agent 工具
- 方案 C：**后端编排**模式，后端做意图分类，调用不同的 Dify App

**推荐方案：方案 C（后端编排）**

理由：
1. 后端拥有完整的用户上下文，路由更精准
2. 可以结合后端数据（排队、票务）做更智能的路由
3. Dify 各 Agent/Workflow 作为独立服务，解耦更彻底
4. 方便做 A/B 测试和灰度发布

### 2.2 Agent 映射表

| 原 Coze Agent | Dify 映射 | Dify App 类型 | 说明 |
|--------------|-----------|:------------:|------|
| 父 Agent（乐乐总机） | 后端 intent_classifier + dify_chat_router | 后端逻辑 | 意图分类在后端完成 |
| 子 Agent 1（游玩规划师） | Dify App: "lele-travel-planner" | Agent | 项目推荐 + 路线规划 + 活动查询 |
| 子 Agent 2（园区百事通） | Dify App: "lele-park-guide" | Agent | 实时查询 + 便利设施 + 安全指导 |
| — （新增）| Dify App: "lele-ticket-assistant" | Chatflow | 购票咨询 + 订单查询 |

### 2.3 后端路由逻辑

```python
# 后端意图分类与路由
INTENT_MAP = {
    "recommend": "lele-travel-planner",      # 推荐相关
    "route_plan": "lele-travel-planner",     # 路线规划
    "event": "lele-travel-planner",          # 活动演出
    "queue": "lele-park-guide",              # 排队查询
    "facility": "lele-park-guide",           # 便利设施
    "safety": "lele-park-guide",             # 安全指导
    "ticket": "lele-ticket-assistant",       # 购票相关
    "greeting": None,                        # 后端直接回复
    "unknown": None,                         # 追问引导
}

async def classify_intent(message: str, context: dict) -> str:
    """使用 LLM 或规则引擎分类用户意图"""
    # 策略 1: 关键词规则匹配（快速，无 LLM 调用）
    # 策略 2: 调用 Dify 工作流做意图分类（精准，有延迟）
    # 策略 3: 混合 - 规则优先，模糊时调用 LLM
    pass

async def route_to_dify(intent: str, message: str, context: dict):
    """根据意图路由到对应的 Dify App"""
    app_id = INTENT_MAP.get(intent)
    if app_id is None:
        return await handle_locally(intent, message, context)
    return await dify_service.chat(app_id, message, context)
```

---

## 3. Workflow 迁移映射

### 3.1 工作流对照表

| 原 Coze Workflow | Dify Workflow | 所属 Dify App | 节点变化 |
|-----------------|---------------|:------------:|---------|
| `Project_Recommendation` | `wf_project_recommend` | lele-travel-planner | 数据源从 Coze DB → 后端 API |
| `Route_Planning` | `wf_route_plan` | lele-travel-planner | 增加实时排队数据接入 |
| `Event_and_Performance_Services` | `wf_event_query` | lele-travel-planner | 增加活动报名功能 |
| `Real_time_workflow_query` | `wf_realtime_query` | lele-park-guide | 数据源从 Coze DB → Redis + 后端 API |
| `Safety_and_Age_Appropriate` | `wf_safety_guide` | lele-park-guide | 增加天气 API 接入 |
| `Park_Convenience_Service_Modul` | `wf_facility_query` | lele-park-guide | 对接后端设施 API |
| — （新增） | `wf_intent_classifier` | 独立 App | 后端备选的 LLM 意图分类 |
| — （新增） | `wf_ticket_service` | lele-ticket-assistant | 购票 + 订单查询 |

### 3.2 Dify Workflow 节点设计示例

#### wf_project_recommend（项目推荐工作流）

```
开始节点
  │
  ▼
LLM 节点: 解析用户意图（提取年龄、兴趣、条件）
  │
  ▼
条件分支: 是否需要查询实时数据？
  ├── 是 → HTTP 请求节点: 调用后端 /api/v1/projects/recommend
  └── 否 → 知识库检索节点: 检索项目知识库
  │
  ▼
LLM 节点: 组织推荐结果（格式化输出）
  │
  ▼
结束节点: 返回推荐结果
```

#### wf_route_plan（路线规划工作流）

```
开始节点
  │
  ▼
LLM 节点: 解析路线参数（年龄、天数、偏好、日期）
  │
  ▼
HTTP 请求节点: 获取实时排队数据
  │
  ▼
HTTP 请求节点: 获取活动排期数据
  │
  ▼
知识库检索节点: 检索路线模板和项目信息
  │
  ▼
LLM 节点: 生成个性化路线（结合实时数据 + 知识库）
  │
  ▼
结束节点: 返回路线方案
```

---

## 4. Knowledge Base 迁移

### 4.1 知识库映射表

| 原 Coze 知识库 | Dify Knowledge | 分段策略 | 绑定 App |
|---------------|----------------|----------|:--------:|
| 乐园项目大全 | kb-projects | 按项目分段（每个项目一个 chunk） | planner |
| 各年龄段游玩指南 | kb-age-guide | 按年龄段 + 兴趣分段 | planner |
| 演出与活动指南 | kb-events | 按演出类型 + 场次分段 | planner |
| 安全游玩规则 | kb-safety | 按项目类型 + 年龄段分段 | guide |
| 园区便利设施指南 | kb-facilities | 按设施类型分段 | guide |
| FAQ 常见问题解答 | kb-faq | 按问题分段（QA 对） | planner + guide |
| 天气应对指南 | kb-weather | 按天气类型分段 | guide |
| — （新增）购票指南 | kb-ticket | 按票种 + 流程分段 | ticket |
| — （新增）会员指南 | kb-member | 按等级 + 权益分段 | guide |

### 4.2 分段策略

Dify 知识库支持以下分段模式：

| 策略 | 适用文档 | 配置 |
|------|----------|------|
| **自动分段** | FAQ、天气指南 | Dify 自动按段落/标题分段 |
| **自定义分段** | 项目大全、安全规则 | 按 `##` 二级标题分段，每个项目/规则一个 chunk |
| **QA 模式** | FAQ | 自动提取 Q-A 对 |
| **CSV/表格** | 演出排期、票价信息 | 按行导入 |

### 4.3 向量化配置

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| **Embedding 模型** | text-embedding-3-small (OpenAI) 或 bge-large-zh (本地) | 中文场景推荐 bge-large-zh |
| **检索模式** | 混合检索（向量 + 关键词） | 中文关键词匹配很重要 |
| **TopK** | 5 | 返回最相关的 5 个 chunk |
| **Score 阈值** | 0.5 | 低于阈值的结果不返回 |
| **Rerank** | 开启（bge-reranker-v2-m3） | 对检索结果重排序 |

---

## 5. Database 迁移

### 5.1 迁移策略

原 Coze 版的 5 张表存储在 Coze 平台内部数据库中。迁移后，所有数据表移至独立的 MySQL 数据库，由后端应用管理。

| 原 Coze 表 | MySQL 表 | 变化说明 |
|-----------|----------|---------|
| projects | projects | 扩展字段（评分、封面图） |
| schedules | schedules | 扩展字段（报名人数、活动类型） |
| user_preferences | user_preferences | 合并到 users 表的 profile 字段 |
| realtime_status | realtime_status | 部分数据迁移至 Redis 缓存 |
| safety_rules | safety_rules | 保留，扩展天气和设备类型 |
| — （新增） | users | 用户账号体系 |
| — （新增） | tickets | 票务订单 |
| — （新增） | members | 会员信息 |
| — （新增） | checkins | 打卡记录 |
| — （新增） | community_posts | 社区帖子 |
| — （新增） | reviews | 评价 |
| — （新增） | notifications | 通知消息 |
| — （新增） | operation_logs | 运营日志 |

> 完整数据库设计见 [05-数据库设计.md](./05-数据库设计.md)

### 5.2 数据迁移步骤

```
1. 从 Coze 平台导出 5 张表数据（Excel/CSV）
2. 使用 Python 脚本清洗数据（处理 Coze 特有字段格式）
3. 映射到新 MySQL 表结构
4. 导入 MySQL（使用 Alembic 做 Schema 管理）
5. 验证数据完整性
```

---

## 6. Plugin → Dify Tool 迁移

### 6.1 工具映射

Dify 的自定义工具通过 API 调用外部服务。我们将后端 API 封装为 Dify 工具：

| 功能 | Dify 工具名称 | 对应后端 API | 说明 |
|------|--------------|-------------|------|
| 查询项目列表 | `get_projects` | GET /api/v1/projects | 按条件筛选项目 |
| 查询排队时间 | `get_queue_time` | GET /api/v1/queue/{project_id} | 实时排队数据 |
| 查询活动排期 | `get_schedules` | GET /api/v1/schedules | 当日/次日排期 |
| 查询设施位置 | `get_facilities` | GET /api/v1/facilities | 母婴室等设施 |
| 查询天气 | `get_weather` | GET /api/v1/weather | 外部天气 API |
| 推荐项目 | `recommend_projects` | POST /api/v1/projects/recommend | 智能推荐 |
| 生成路线 | `generate_route` | POST /api/v1/routes/generate | 路线规划 |
| 查询票价 | `get_ticket_prices` | GET /api/v1/tickets/prices | 票价信息 |

### 6.2 Dify 工具配置示例

在 Dify 平台中创建自定义工具：

```yaml
# Dify 自定义工具: get_queue_time
tool_name: get_queue_time
description: "查询指定项目的实时排队时间和拥挤程度"
method: GET
url: "{{base_url}}/api/v1/queue/{project_id}"
headers:
  Authorization: "Bearer {{api_key}}"
parameters:
  - name: project_id
    type: string
    required: true
    description: "项目ID，如 P001"
  - name: date
    type: string
    required: false
    description: "查询日期，默认今天"
response_filter: ".data"  # 只返回 data 字段
```

---

## 7. 迁移验证清单

| 验证项 | 说明 | 通过标准 |
|--------|------|---------|
| **知识库检索准确率** | 同一问题在 Dify 和 Coze 的检索结果对比 | Top5 命中率 ≥ 90% |
| **Agent 响应质量** | 相同输入，对比两个平台的回复质量 | 人工评分不低于 Coze |
| **意图识别准确率** | 100 条测试用例的路由准确率 | ≥ 95% |
| **工作流执行成功率** | 6 个工作流 × 10 条测试数据 | 100% 执行成功 |
| **API 响应延迟** | 端到端对话延迟（用户输入 → 收到回复） | P95 < 5 秒 |
| **数据完整性** | 迁移后数据条数和字段值校验 | 100% 一致 |
