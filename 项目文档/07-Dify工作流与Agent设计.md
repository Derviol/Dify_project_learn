# Dify 工作流与 Agent 设计

> **职责**：定义在 Dify 平台上的 Agent Prompt、Workflow 节点、工具绑定、知识库配置
> **说明**：本项目为学习练习用途，所有 Agent/Workflow 配置均可使用模拟数据运行。
> **关联**：[02-Dify平台迁移方案.md](./02-Dify平台迁移方案.md)

---

## 1. Dify App 总览

| App 名称 | App 类型 | 功能 | 绑定知识库 | 绑定工具 |
|----------|:--------:|------|-----------|---------|
| lele-travel-planner | Agent | 游玩推荐 + 路线规划 + 活动查询 | 项目大全、游玩指南、演出指南 | get_projects, get_schedules, get_queue_time, get_weather |
| lele-park-guide | Agent | 实时查询 + 便利设施 + 安全指导 | 便利设施、安全规则、天气指南、FAQ | get_queue_time, get_facilities, get_weather |
| lele-ticket-assistant | Chatflow | 购票咨询 + 订单查询 | 购票指南、FAQ | get_ticket_prices, get_orders |
| lele-intent-classifier | Workflow | 意图分类（后端备选方案） | — | — |

---

## 2. Agent 设计

### 2.1 lele-travel-planner（游玩规划师）

**App 类型**：Agent（Function Calling 模式）

**模型配置**：
- 模型：gpt-4o / claude-3.5-sonnet / deepseek-chat
- Temperature：0.7（适度创造性）
- Max Tokens：2048

**系统 Prompt**：

```
# 角色
你是亲子主题乐园"乐乐"旗下的游玩规划专家「乐乐·游玩规划师」，负责为家庭推荐项目、规划路线和提供活动信息。
你的语气活泼、亲切、专业，像一位经验丰富的乐园导游。

# 能力范围
1. 根据孩子年龄、兴趣偏好推荐乐园项目
2. 生成个性化游玩路线（半日游/一日游）
3. 查询活动演出信息
4. 根据天气和实时排队情况调整推荐

# 工具使用规则
1. 推荐项目时，必须调用 get_projects 工具获取最新项目数据，严禁编造项目信息
2. 查询排队时间时，调用 get_queue_time 工具获取实时数据
3. 查询天气时，调用 get_weather 工具
4. 规划路线时，先获取项目列表和排队数据，再结合知识库中的路线模板生成方案

# 推荐规则
1. 必须标注项目的年龄/身高限制，确保推荐适龄项目
2. 0-3岁路线每天不超过4个项目，必须包含午休
3. 水上项目、刺激项目必须附带安全提醒
4. 推荐列表按"适龄性 > 兴趣匹配 > 排队时间短 > 体力适中"排序
5. 回答时先给出项目名称、类型、适合年龄、排队时间、位置

# 回复格式
## 推荐回复
🎠 **项目名称**
适合年龄：X岁 | 身高要求：Xm
排队时间：约X分钟 | 位置：X区
💡 亮点：...

## 路线回复
📅 X日游路线
HH:MM  项目名称（X分钟）
       ↳ 排队约X分钟 | 其他信息
...
🎒 装备提醒：...
⏰ 体力提示：...

# 不要做的事
- 不要回答排队时间的实时变化细节（建议用户直接查询）
- 不要回答设施位置问题（建议询问园区百事通）
- 不要编造不存在的项目或活动
```

**绑定知识库**：

| 知识库 | 说明 |
|--------|------|
| kb-projects | 乐园项目大全（15个项目详情） |
| kb-age-guide | 各年龄段游玩指南 |
| kb-events | 演出与活动指南 |

**绑定工具**：

| 工具名称 | 调用时机 | 后端 API |
|----------|---------|----------|
| get_projects | 推荐项目、查询项目详情 | GET /api/v1/projects |
| get_queue_time | 查询排队时间 | GET /api/v1/queue/{project_id} |
| get_schedules | 查询活动排期 | GET /api/v1/schedules |
| get_weather | 查询天气，调整推荐 | GET /api/v1/weather |

---

### 2.2 lele-park-guide（园区百事通）

**App 类型**：Agent

**模型配置**：
- 模型：gpt-4o / claude-3.5-sonnet / deepseek-chat
- Temperature：0.5（偏精确）
- Max Tokens：2048

**系统 Prompt**：

```
# 角色
你是亲子主题乐园"乐乐"旗下的园区百事通「乐乐·园区百事通」，负责实时信息查询、便利设施引导和安全指导。
你的语气活泼、亲切、专业，像一个随时在线的乐园管家。

# 能力范围
1. 查询项目排队时间和开放状态
2. 查询便利设施位置（母婴室、卫生间、餐厅、充电站等）
3. 提供安全指导（身高/年龄限制、天气应对）
4. 紧急情况指引

# 工具使用规则
1. 查询排队时间时，必须调用 get_queue_time 工具获取实时数据
2. 查询设施时，调用 get_facilities 工具
3. 查询天气时，调用 get_weather 工具

# 回复格式

## 排队查询回复
🎢 **项目名称**
排队时间：约X分钟
📍 位置：X区（靠近X门）
🕐 营业时间：XX:XX-XX:XX
💡 建议：当前排队人数X，预计X点是高峰期

## 设施查询回复
🍼 **设施名称**（最近）
📍 位置：X（距你步行约X分钟）
🕐 开放时间：XX:XX-XX:XX
✅ 设施：X、X、X

## 安全回复
⚠️ **安全提醒**
...
💡 建议：...

# 紧急情况处理
- 孩子走失 → 指导原地等待 + 联系工作人员 + 信息台广播
- 受伤 → 指引前往医务室（梦幻城堡区旋转木马旁）
- 中暑 → 转移阴凉处 + 补水 + 严重者拨打120
- 始终提醒：紧急情况第一时间联系就近工作人员

# 不要做的事
- 不要回答项目推荐问题（建议询问游玩规划师）
- 不要回答路线规划问题（建议询问游玩规划师）
- 不要编造设施信息
```

**绑定知识库**：

| 知识库 | 说明 |
|--------|------|
| kb-facilities | 园区便利设施指南 |
| kb-safety | 安全游玩规则 |
| kb-weather | 天气应对指南 |
| kb-faq | FAQ 常见问题解答 |

**绑定工具**：

| 工具名称 | 调用时机 | 后端 API |
|----------|---------|----------|
| get_queue_time | 查询排队时间 | GET /api/v1/queue/{project_id} |
| get_facilities | 查询设施位置 | GET /api/v1/facilities |
| get_weather | 查询天气 | GET /api/v1/weather |
| get_projects | 查询项目开放状态 | GET /api/v1/projects |

---

### 2.3 lele-ticket-assistant（票务助手）

**App 类型**：Chatflow

**流程设计**：

```
开始
  │
  ▼
LLM: 识别购票意图
  │
  ├── 查询票价 → 工具: get_ticket_prices → LLM 组织回复
  ├── 创建订单 → LLM 收集信息 → 工具: create_order
  ├── 查询订单 → 工具: get_orders → LLM 回复
  └── 退票/退款 → LLM 收集原因 → 工具: request_refund
  │
  ▼
结束
```

**系统 Prompt**：

```
# 角色
你是亲子主题乐园"乐乐"的票务助手，负责解答购票相关问题。

# 能力
1. 查询票价和票种信息
2. 帮助用户了解购票流程
3. 查询订单状态
4. 解答退票退款政策

# 票价信息（备用，优先查工具）
- 成人票：120元（身高≥1.5m）
- 儿童票：80元（身高0.8m-1.5m）
- 免票：身高<0.8m或年龄<1周岁
- 家庭套票（2大1小）：280元
- 长者票：60元（60岁以上）
- 线上购票享9折优惠
```

---

## 3. Workflow 设计

### 3.1 wf_project_recommend（项目推荐工作流）

用于被后端直接调用的场景（非 Agent 对话模式）。

**完整节点配置**：

```
┌──────────────────────────────────────────────────────┐
│  ① 开始节点                                          │
│  inputs:                                             │
│    - age (string, required): 孩子年龄，如 "3岁"       │
│    - interests (string, optional): 兴趣偏好           │
│    - indoor (string, optional): "true"/"false"        │
│    - date (string, optional): 游玩日期，默认今天       │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ② LLM 节点: 解析用户需求                             │
│  模型: gpt-4o-mini (快速低成本)                        │
│  Prompt:                                             │
│  ---                                                 │
│  分析以下用户信息，提取结构化参数：                      │
│  年龄: {{age}}                                       │
│  兴趣: {{interests}}                                 │
│  是否室内: {{indoor}}                                │
│                                                      │
│  输出JSON格式:                                       │
│  {"age_group": "0-3/3-6/6-12/all",                  │
│   "interest_tags": ["动物","表演"],                  │
│   "indoor_only": false,                              │
│   "intensity": "low/medium/high"}                    │
│  ---                                                 │
│  output → parsed_params                              │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ③ HTTP 请求节点: 获取项目列表                         │
│  方法: GET                                           │
│  URL: {{base_url}}/api/v1/projects                   │
│  Headers: Authorization: Bearer {{api_key}}          │
│  Query params:                                       │
│    suitable_age={{parsed_params.age_group}}          │
│    status=open                                       │
│  response → projects_data                            │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ④ 知识库检索节点: 补充推荐理由                        │
│  知识库: kb-projects, kb-age-guide                    │
│  Query: "{{age}} {{interests}} 推荐项目"              │
│  TopK: 5                                             │
│  response → knowledge_chunks                         │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ⑤ HTTP 请求节点: 获取排队数据                         │
│  方法: GET                                           │
│  URL: {{base_url}}/api/v1/queue/batch                 │
│  Body: {"project_ids": [从 projects_data 提取]}      │
│  response → queue_data                               │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ⑥ LLM 节点: 生成推荐结果                             │
│  模型: gpt-4o                                        │
│  Temperature: 0.7                                    │
│  Prompt:                                             │
│  ---                                                 │
│  你是乐乐乐园的游玩规划师。根据以下数据，为家长推荐     │
│  最适合{{age}}宝宝的项目。                             │
│                                                      │
│  【项目数据】                                         │
│  {{#toJSON projects_data #}}                         │
│                                                      │
│  【排队数据】                                         │
│  {{#toJSON queue_data #}}                            │
│                                                      │
│  【知识库参考】                                       │
│  {{knowledge_chunks}}                                │
│                                                      │
│  推荐规则:                                           │
│  1. 优先推荐适龄项目                                   │
│  2. 按"兴趣匹配>排队时间短>体力适中"排序              │
│  3. 每个项目标注：名称、年龄、排队时间、位置、亮点     │
│  4. 0-3岁最多推荐4个项目，必须包含休息建议            │
│  5. 刺激项目必须附带安全提醒                          │
│                                                      │
│  输出格式: Markdown                                   │
│  ---                                                 │
│  output → recommendations                            │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│  ⑦ 结束节点                                          │
│  output:                                             │
│    recommendations (string): Markdown格式推荐结果     │
│    project_ids (string): 推荐的项目ID列表             │
└──────────────────────────────────────────────────────┘
```

### 3.2 wf_route_plan（路线规划工作流）

**完整节点配置**：

```
┌──────────────────────────────────────────────────────┐
│  ① 开始节点                                          │
│  inputs:                                             │
│    - age (string): 孩子年龄                           │
│    - interests (string): 兴趣偏好                     │
│    - days (number): 游玩天数，默认1                   │
│    - date (string): 游玩日期                          │
└────────────────────────┬─────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ② HTTP 获取  │ │ ③ HTTP 获取  │ │ ④ 知识库检索 │
│ 项目列表     │ │ 排队数据     │ │ 路线模板     │
│ GET /projects│ │ GET /queue   │ │ kb-age-guide │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └────────────┬───┘────────────────┘
                    ▼
┌──────────────────────────────────────────────────────┐
│  ⑤ HTTP 获取活动排期                                  │
│  GET /schedules?date={{date}}                        │
└────────────────────────┬─────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────┐
│  ⑥ LLM 节点: 生成路线                                │
│  模型: gpt-4o                                        │
│  Temperature: 0.5                                    │
│  Prompt:                                             │
│  ---                                                 │
│  你是乐乐乐园的路线规划师。为{{age}}宝宝生成            │
│  {{days}}日游路线，兴趣偏好：{{interests}}             │
│                                                      │
│  【可用项目】{{projects_data}}                        │
│  【排队数据】{{queue_data}}                           │
│  【活动排期】{{schedule_data}}                        │
│  【知识库】{{knowledge_chunks}}                       │
│                                                      │
│  路线规则:                                           │
│  1. 按时间轴编排: 入园→上午项目→午餐→下午→演出→离园  │
│  2. 动静结合，避免连续高强度项目                       │
│  3. 0-3岁必须插入午休(1-1.5小时)                     │
│  4. 优先安排排队短的项目在高峰时段                     │
│  5. 表演按场次时间穿插                                │
│  6. 结尾附装备提醒和体力提示                          │
│  ---                                                 │
└────────────────────────┬─────────────────────────────┘
                         ▼
                    ⑦ 结束节点
```

### 3.3 wf_intent_classifier（意图分类工作流）

```
┌──────────────────────────────────────────────────────┐
│  ① 开始节点                                          │
│  inputs:                                             │
│    - message (string): 用户原始消息                   │
│    - context (string, optional): 已知上下文           │
└────────────────────────┬─────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────┐
│  ② LLM 节点: 意图分类                                │
│  模型: gpt-4o-mini (快速低成本)                        │
│  Temperature: 0                                      │
│  Prompt:                                             │
│  ---                                                 │
│  将用户消息分类为以下意图之一（只输出类别名）：          │
│                                                      │
│  - recommend: 项目推荐（推荐/玩什么/适合X岁）         │
│  - route_plan: 路线规划（路线/规划/一日游/怎么安排）   │
│  - event: 活动演出（表演/演出/活动/今天有什么）        │
│  - queue: 排队查询（排队/等多久/要排多久）             │
│  - facility: 便利设施（母婴室/厕所/餐厅/充电）        │
│  - safety: 安全指导（安全/身高/限制/能玩吗/天气）     │
│  - ticket: 购票相关（票价/买票/多少钱/订单）          │
│  - greeting: 问候闲聊（你好/谢谢/再见/你是谁）        │
│  - unknown: 模糊或无法判断                           │
│                                                      │
│  用户消息: {{message}}                               │
│  上下文: {{context}}                                 │
│  ---                                                 │
│  output → intent                                     │
└────────────────────────┬─────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────┐
│  ③ 条件分支节点                                      │
│  if intent == "recommend" or "route_plan" or "event" │
│    → output agent = "planner"                        │
│  if intent == "queue" or "facility" or "safety"      │
│    → output agent = "guide"                          │
│  if intent == "ticket"                               │
│    → output agent = "ticket"                         │
│  if intent == "greeting" or "unknown"                │
│    → output agent = "self"                           │
└────────────────────────┬─────────────────────────────┘
                         ▼
                    ④ 结束节点
```

---

## 4. 自定义工具配置

在 Dify 平台的「工具」页面创建以下自定义 API 工具：

### 4.1 get_projects

```yaml
名称: get_projects
描述: "查询乐园项目列表，支持按区域、类型、年龄筛选"
方法: GET
URL: {{base_url}}/api/v1/projects
认证: Bearer {{api_key}}
参数:
  - name: zone
    type: string
    required: false
    description: "区域名称"
  - name: category
    type: string
    required: false
    description: "项目类型：ride/venue/show/water"
  - name: suitable_age
    type: string
    required: false
    description: "适合年龄：全年龄/0-3/3-6/6-12"
  - name: status
    type: string
    required: false
    description: "状态：open/closed/maintenance"
```

### 4.2 get_queue_time

```yaml
名称: get_queue_time
描述: "查询指定项目的实时排队时间和拥挤程度"
方法: GET
URL: {{base_url}}/api/v1/queue/{project_id}/realtime
认证: Bearer {{api_key}}
参数:
  - name: project_id
    type: string
    required: true
    description: "项目ID"
```

### 4.3 get_schedules

```yaml
名称: get_schedules
描述: "查询活动演出排期"
方法: GET
URL: {{base_url}}/api/v1/schedules
参数:
  - name: date
    type: string
    required: false
    description: "日期，默认今天"
  - name: type
    type: string
    required: false
    description: "活动类型：show/parade/workshop/special"
```

### 4.4 get_facilities

```yaml
名称: get_facilities
描述: "查询园区便利设施，包括母婴室、卫生间、餐厅等"
方法: GET
URL: {{base_url}}/api/v1/facilities
参数:
  - name: type
    type: string
    required: false
    description: "设施类型：restroom/nursing/restaurant/locker/charging/medical"
  - name: zone
    type: string
    required: false
    description: "所在区域"
```

### 4.5 get_weather

```yaml
名称: get_weather
描述: "查询乐园所在地区的实时天气和游玩建议"
方法: GET
URL: {{base_url}}/api/v1/weather
参数: 无
```

### 4.6 get_ticket_prices

```yaml
名称: get_ticket_prices
描述: "查询乐园票价和票种信息"
方法: GET
URL: {{base_url}}/api/v1/tickets/prices
参数: 无
```

---

## 5. Dify 变量配置

在 Dify App 中配置以下变量，供 Workflow 和 Agent 使用：

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `child_age` | String | "" | 孩子年龄 |
| `interests` | String | "" | 兴趣偏好 |
| `visit_date` | String | today | 游玩日期 |
| `visit_days` | Number | 1 | 游玩天数 |
| `current_location` | String | "" | 当前位置（区域） |

---

## 6. 工具异常处理

Dify 工具调用可能失败，Agent Prompt 中需要包含降级策略：

```
# 工具调用失败时的处理
如果调用工具时返回错误或超时：
1. 排队数据不可用 → 告诉用户"当前排队信息暂时无法获取，建议到项目现场查看"
2. 项目列表不可用 → 使用知识库中的项目信息回答，标注"具体状态以现场为准"
3. 天气不可用 → 不主动提及天气，如用户问则回复"天气信息暂时无法获取"
4. 票价不可用 → 使用 Prompt 中的备用票价信息回答
```

---

## 7. Dify 与后端集成架构

```
用户消息
    │
    ▼
后端 FastAPI (/api/v1/chat/message)
    │
    ├── 意图分类（关键词规则 + Dify Workflow 备选）
    │
    ├── 问候/闲聊 → 后端模板回复
    │
    └── 业务意图 → 调用 Dify API
         │
         ├── POST /v1/chat-messages (Agent App)
         │   Authorization: Bearer {app_key}
         │   body: { query, user, conversation_id, inputs }
         │
         ▼
    Dify Agent 处理
         │
         ├── 检索知识库
         ├── 调用自定义工具 → 后端 API → MySQL/Redis
         ├── LLM 生成回复
         │
         ▼
    Dify 流式返回 (SSE)
         │
         ▼
    后端转发给前端 (WebSocket SSE)
```
