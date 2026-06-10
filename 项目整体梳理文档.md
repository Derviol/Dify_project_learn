# 乐乐亲子乐园智能服务系统 — 项目全景文档

> 生成日期：2026-06-05  
> 本文档基于项目实际代码 + 设计文档综合梳理，帮助你快速了解整个项目的方方面面。

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈一览](#2-技术栈一览)
3. [项目目录结构](#3-项目目录结构)
4. [架构设计](#4-架构设计)
5. [核心业务模块](#5-核心业务模块)
6. [数据库设计](#6-数据库设计)
7. [AI 集成（Dify）](#7-ai-集成dify)
8. [API 接口清单](#8-api-接口清单)
9. [实现状态评估](#9-实现状态评估)
10. [开发与运行指南](#10-开发与运行指南)
11. [项目文档索引](#11-项目文档索引)

---

## 1. 项目概述

| 项目 | 内容 |
|------|------|
| **项目名称** | 乐乐亲子乐园智能服务系统 |
| **项目定位** | 一个 AI 驱动的亲子主题乐园智能服务平台，提供 AI 导游、在线购票、智能排队、会员管理等服务 |
| **技术特征** | 前后端分离 + Dify AI 平台 + 全异步 Python 后端 |

---

## 2. 技术栈一览

### 实际已采用的（已编码实现）

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端框架** | FastAPI | 0.110+ | Web 框架，全异步 |
| **语言** | Python | 3.11+ | - |
| **ASGI 服务器** | Uvicorn | latest | 运行 FastAPI 应用 |
| **ORM** | SQLAlchemy 2.0 | async 模式 | 异步数据库操作 |
| **数据验证** | Pydantic v2 | - | 请求/响应模型校验 |
| **认证** | `python-jose` (JWT) + `passlib` (bcrypt) | - | 用户认证体系 |
| **数据库** | MySQL 8.0 | `aiomysql` 驱动 | 主业务数据库 |
| **缓存/排队** | Redis 7.x | `redis-py` async | 排队数据、票据缓存 |
| **AI 平台** | Dify | 社区版 | LLM Agent + 知识库 |
| **HTTP 客户端** | `httpx` | async | 调用 Dify API |
| **日志** | `loguru` | - | 结构化日志 |
| **任务调度** | `APScheduler` | 3.10+（已安装待用） | 定时任务（计划中） |
| **跨域** | FastAPI CORSMiddleware | - | CORS 配置 |

### 已在设计中但尚未完备实现

| 组件 | 状态 | 说明 |
|------|:----:|------|
| **Web 前端（Vue 3）** | ⚠️ 仅单页 | 已有 `web/index.html` 单页（通过 CDN 引入 Vue 3），功能不完整 |
| **微信小程序（uni-app）** | ❌ 未实现 | `miniapp/` 目录仅含模板构建输出 |
| **数据库迁移（Alembic）** | ❌ 未配置 | 使用 `scripts/create_missing_tables.sql` 替代 |
| **前端测试（Vitest）** | ❌ 未编写 | 文档中有测试方案 |
| **E2E 测试** | ❌ 未编写 | - |
| **语音输入** | ❌ 未实现 | 仅在设计阶段 |
| **打卡系统** | ❌ 未实现 | 仅在设计阶段 |
| **运营管理后台** | ❌ 未实现 | 仅在设计阶段 |

---

## 3. 项目目录结构

```
Dify_project/
│
├── .gitignore                            # Git 忽略规则
├── problem.txt                           # （空文件）
│
├── 项目文档/                              # 📚 11 份设计文档
│   ├── README.md
│   ├── 01-系统架构设计.md
│   ├── 02-Dify平台迁移方案.md
│   ├── 03-后端技术方案.md
│   ├── 04-前端技术方案.md
│   ├── 05-数据库设计.md
│   ├── 06-API接口设计.md
│   ├── 07-Dify工作流与Agent设计.md
│   ├── 08-知识库与数据设计.md
│   ├── 09-功能需求设计.md
│   ├── 10-测试方案.md
│   └── 11-项目计划与里程碑.md
│
├── 知识库/                               # 📖 9 份 Dify 知识库源文档
│   ├── 01-乐园项目大全.md
│   ├── 02-各年龄段游玩指南.md
│   ├── 03-安全游玩规则.md
│   ├── 04-园区便利设施指南.md
│   ├── 05-FAQ常见问题解答.md
│   ├── 06-演出与活动指南.md
│   ├── 07-天气应对指南.md
│   ├── 08-购票指南.md
│   └── 09-会员指南.md
│
├── 项目整体梳理文档.md                      # 📄 本文档
│
└── Project/                              # 💻 核心代码目录
    ├── .env                              # 环境变量（含 3 个 Dify App Key）
    ├── .env.example                      # 环境变量模板
    ├── requirements.txt                  # Python 依赖
    ├── start.txt                         # 启动步骤备忘录
    │
    ├── app/                              # ★ 核心后端代码
    │   ├── main.py                       # FastAPI 入口（lifespan + CORS + 路由注册）
    │   │
    │   ├── core/                         # 核心基础设施
    │   │   ├── config.py                 # Pydantic Settings 配置管理
    │   │   ├── database.py               # SQLAlchemy async 引擎 + 会话
    │   │   ├── redis.py                  # Redis 连接管理（单例）
    │   │   ├── security.py               # JWT 生成/验证 + bcrypt 密码
    │   │   ├── deps.py                   # 依赖注入（get_current_user 等）
    │   │   └── exceptions.py             # BizError + 全局异常处理器
    │   │
    │   ├── models/                       # SQLAlchemy ORM 数据模型
    │   │   ├── base.py                   # declarative_base
    │   │   ├── user.py                   # User, UserProfile
    │   │   ├── project.py                # Project, Facility
    │   │   ├── ticket.py                 # TicketType, TicketOrder, TicketItem
    │   │   └── misc.py                   # 其余 9 张表（Schedule, QueueRecord, Member 等）
    │   │
    │   ├── schemas/                      # Pydantic 请求/响应模型
    │   │   ├── common.py                 # ok() / fail() / page() 统一响应
    │   │   ├── auth.py                   # RegisterReq, LoginReq 等
    │   │   ├── chat.py                   # ChatMessageReq
    │   │   ├── ticket.py                 # CreateOrderReq
    │   │   └── queue.py                  # TakeNumberReq
    │   │
    │   ├── api/                          # API 路由层
    │   │   ├── v1/
    │   │   │   ├── router.py             # 路由聚合（11 个模块）
    │   │   │   ├── auth.py               # 认证 5 个接口
    │   │   │   ├── users.py              # 用户信息 3 个接口
    │   │   │   ├── projects.py           # 项目 3 个接口
    │   │   │   ├── tickets.py            # 票务 7 个接口
    │   │   │   ├── chat.py               # AI 对话（REST）
    │   │   │   ├── queue.py              # 排队 5 个接口
    │   │   │   ├── schedules.py          # 活动排期 1 个接口
    │   │   │   ├── facilities.py         # 便利设施 1 个接口
    │   │   │   ├── member.py             # 会员 2 个接口
    │   │   │   ├── community.py          # 社区 4 个接口
    │   │   │   └── weather.py            # 天气 1 个接口
    │   │   └── ws/
    │   │       └── chat_ws.py            # WebSocket 流式 AI 对话
    │   │
    │   └── services/                     # ★ 业务逻辑层
    │       ├── auth_service.py           # 注册/登录/改密/微信登录
    │       ├── dify_service.py           # Dify API 封装（核心：流式 + 阻塞 + 重试 + 模拟）
    │       ├── project_service.py        # 项目查询/推荐/适龄筛选
    │       ├── ticket_service.py         # 票务：创建/支付/取消 + Redis 缓存
    │       ├── queue_service.py          # 排队：Redis 全量实现（取号/叫号/取消）
    │       └── misc_service.py           # 排期/设施/天气/用户/会员/社区 6 合 1
    │
    ├── scripts/                          # 工具脚本
    │   ├── init_data.py                  # ★ 数据库初始化脚本（完整虚拟数据）
    │   └── create_missing_tables.sql     # 建表 SQL（含全部 16 张表）
    │
    ├── dify_tools/                       # Dify 工具配置（单个文件）
    │   └── 01_get_projects.json ~ 06_get_ticket_prices.json
    │
    ├── dify_tools_schema.json            # Dify 工具集完整 OpenAPI 3.0 Schema
    │
    ├── web/
    │   └── index.html                    # 简易前端页面（Vue 3 CDN 单页应用）
    │
    └── tests/
        └── __init__.py                   # 测试目录（空）
```

---

## 4. 架构设计

### 4.1 系统分层

```
┌────────────────────────────────┐
│        用户终端                 │
│  Web 前端 / 微信小程序          │
└─────────┬──────────────────────┘
          │ HTTPS / WSS
          ▼
┌────────────────────────────────┐
│    后端 API（FastAPI）          │  ← 你在这里
│                                │
│  Router → Service → Model      │
│  (路由)   (业务)   (数据)      │
└──────┬───────────┬─────────────┘
       │           │
       ▼           ▼
┌──────────┐ ┌──────────────────┐
│  MySQL   │ │  Dify AI 平台     │
│ (持久化) │ │ (LLM + 知识库)   │
└──────────┘ └──────────────────┘
       │
       ▼
┌──────────┐
│  Redis   │
│ (缓存)   │
└──────────┘
```

### 4.2 后端代码架构（三层架构）

```
API 路由 (api/v1/*.py)       ← 接收 HTTP 请求，参数校验，返回响应
    │
    ▼
Service 层 (services/*.py)   ← 核心业务逻辑，调用 Model 和外部服务
    │
    ▼
Model 层 (models/*.py)       ← SQLAlchemy ORM 数据模型定义
    │
    ▼
MySQL / Redis                ← 数据存储
```

### 4.3 AI 对话架构（核心流程）

```
用户发送消息
    │
    ▼
后端意图分类（chat.py: classify_intent）
    │
    ├── 推荐/规划/活动 → lele-travel-planner (Dify Agent)
    ├── 排队/设施/安全 → lele-park-guide (Dify Agent)
    ├── 票价/买票      → lele-ticket-assistant (Dify Chatflow)
    └── 问候           → 后端直接回复
    │
    ▼
Dify Agent 调用后端 API 工具（6 个 OpenAPI 工具）
    │
    ├── get_projects     → GET /api/v1/projects
    ├── get_queue_time   → GET /api/v1/queue/{id}
    ├── get_schedules    → GET /api/v1/schedules
    ├── get_facilities   → GET /api/v1/facilities
    ├── get_weather      → GET /api/v1/weather
    └── get_ticket_prices→ GET /api/v1/tickets/prices
    │
    ▼
LLM 生成回复 → 流式返回给用户（WebSocket / REST）
```

### 4.4 部署拓扑

```
Nginx（反向代理 + SSL） ──→ FastAPI (Gunicorn + Uvicorn) ──→ MySQL + Redis
                            │
                            └──→ Dify API (Docker)
```

---

## 5. 核心业务模块

### 5.1 认证系统

| 功能 | 接口 | 说明 |
|------|------|------|
| 手机号注册 | `POST /auth/register` | 手机号 + 密码 + 昵称 |
| 手机号登录 | `POST /auth/login` | 返回 access_token (2h) + refresh_token (7d) |
| 微信登录 | `POST /auth/wechat/login` | 模拟实现（code 直接映射为 openid） |
| 修改密码 | `PUT /auth/password` | 需验证旧密码 |
| 刷新 Token | `POST /auth/refresh` | 用 refresh_token 换取新 access_token |

**技术细节：**
- JWT 双 Token 机制：access_token 有效期 2 小时，refresh_token 7 天
- 密码使用 bcrypt 哈希存储，向下兼容旧版 SHA-256
- 微信登录为模拟模式（学习项目无需真实微信凭据）
- 注册时自动创建 UserProfile 和 Member

### 5.2 AI 智能对话（项目核心亮点）

**两种通信模式：**

| 模式 | 接口 | 适用场景 |
|------|------|----------|
| REST | `POST /chat/message` | 简单查询、非流式调用 |
| WebSocket | `WS /ws/chat?token=xxx` | 流式输出、多轮对话 |

**三条 Dify App：**

| App 名称 | App Key 环境变量 | 意图范围 |
|----------|-----------------|----------|
| **planner**（游玩规划师） | `DIFY_APP_KEY_PLANNER` | 推荐项目、路线规划、活动演出 |
| **guide**（园区百事通） | `DIFY_APP_KEY_GUIDE` | 排队查询、设施位置、安全规则、天气 |
| **ticket**（票务助手） | `DIFY_APP_KEY_TICKET` | 票价查询、购票咨询 |

**意图分类：**
- 后端使用关键词规则（9 类意图），无需额外 LLM 调用
- 多轮会话自动保持同一个 Agent（`_conv_agent` 字典）
- 问候类直接后端回复，无需 Dify 调用

**关键特性：**
- 自动重试：无结果时自动重试一次
- 模拟模式：当 Dify API Key 未配置时返回本地模拟回复
- 回复清洗：`clean_answer()` 函数去除工具调用标记、思考过程、乱码
- 上下文注入：用户画像（孩子年龄、兴趣）随请求发送到 Dify

### 5.3 项目与推荐

**数据规模：** 15 个项目，分布在 6 大主题区

| 主题区 | 项目数 | 代表项目 |
|--------|:------:|---------|
| 梦幻城堡区 | 3 | 旋转木马、魔术秀、摩天轮 |
| 海洋探险区 | 3 | 泡泡海洋馆、海洋动物表演、海底隧道 |
| 冒险区 | 2 | 过山车·极速飞鹰、碰碰车乐园 |
| 科普区 | 2 | 恐龙科普馆、鸟语林 |
| 欢乐农场区 | 1 | 小火车 |
| 水上乐园区 | 1 | 水上乐园·浪花谷（维护中） |

**推荐逻辑：**
- 按年龄匹配（解析 "3-6岁"、"全年龄"、"3岁以上" 格式）
- 支持室内/室外、兴趣标签筛选
- 推荐列表附带排队时间

### 5.4 票务系统

| 功能 | 接口 | 说明 |
|------|------|------|
| 票价查询 | `GET /tickets/prices` | 返回所有票种及价格 |
| 创建订单 | `POST /tickets/orders` | 选择票种 + 日期 + 数量 |
| 订单支付 | `POST /tickets/orders/{no}/pay` | 模拟支付（含 `SELECT FOR UPDATE` 行锁防并发） |
| 订单查询 | `GET /tickets/orders` | 分页查询 |
| 订单详情 | `GET /tickets/orders/{no}` | 单笔订单详情 |
| 取消订单 | `POST /tickets/orders/{no}/cancel` | 可取消 pending/confirmed 状态 |
| 有效票据查询 | `GET /tickets/my-tickets` | Redis 校验 |

**票种设计（7 种）：**

| 票种 | 原价 | 线上优惠价 | 说明 |
|------|:----:|:----------:|------|
| 成人票 | ¥120 | ¥108 | 标准成人票 |
| 儿童票 | ¥80 | ¥72 | 身高 1.2m–1.5m |
| 婴幼儿票 | ¥0 | 免费 | 身高 < 1.2m |
| 家庭套票 A（1大1小） | ¥180 | ¥158 | - |
| 家庭套票 B（2大1小） | ¥280 | ¥248 | - |
| 家庭套票 C（2大2小） | ¥360 | ¥318 | - |
| 长者票 | ¥60 | ¥48 | 65 岁以上 |

**Redis 缓存策略：** 支付成功后票据缓存 12 小时，排队取号时校验 Redis 中是否有有效票据。

### 5.5 智能排队系统

完全基于 **Redis** 实现，无需数据库事务。排队取号又快又稳。

**Redis Key 设计：**

```
queue:{project_id}:{date}:counter       → 自增取号计数器
queue:{project_id}:{date}:current       → 当前叫到的号码
queue:{project_id}:{date}:user:{uid}    → 用户 → 排队号码
queue:{project_id}:{date}:num:{num}     → 号码 → 用户 ID
queue:{project_id}:{date}:cancelled     → 已取消的号码集合（Set）
```

**功能清单：**

| 操作 | 说明 |
|------|------|
| 取号 | 自增计数器 + 校验有效票 + 动态 TTL |
| 查询 | 当前号码、前方人数、预计等待时间 |
| 取消 | 删除 Redis 记录 + 加入 cancelled 集合 |
| 叫号 | 运营端使用，自动跳过已取消号码 |
| 自动过期 | 所有 Key 的 TTL = 等待时间 + 30 分钟（最少 30 分钟） |

**排队校验逻辑：** 取号前检查 Redis 中是否有未过期的有效票（`ticket:active:{order_no}`），无票拒绝取号。

### 5.6 会员系统

| 功能 | 接口 | 说明 |
|------|------|------|
| 会员信息 | `GET /member/info` | 等级、积分、余额 |
| 每日签到 | `POST /member/checkin` | +5 积分 |
| 自动创建 | - | 首次查询时自动创建会员 |

**会员等级：**

| 等级 | 名称 | 条件 |
|:----:|------|------|
| 1 | 普通会员 | 注册即得 |
| 2 | 银卡会员 | 累计消费 ≥ ¥500 或游玩 ≥ 3 次 |
| 3 | 金卡会员 | 累计消费 ≥ ¥2000 或游玩 ≥ 10 次 |
| 4 | 钻石会员 | 累计消费 ≥ ¥5000 或游玩 ≥ 25 次 |

### 5.7 社区系统

| 功能 | 接口 | 说明 |
|------|------|------|
| 帖子列表 | `GET /community/posts` | 分页 + 类型筛选（游记/评价/攻略/提问） |
| 发布帖子 | `POST /community/posts` | 支持标签和关联项目 |
| 点赞 | `POST /community/posts/{id}/like` | 累加计数 |
| 评论 | `POST /community/posts/{id}/comments` | 支持嵌套回复（parent_id） |

### 5.8 其他服务

| 服务 | 实现方式 | 说明 |
|------|----------|------|
| **天气查询** | 模拟数据 | 返回 28°C 多云，含 UV、AQI 和游玩建议 |
| **设施查询** | MySQL 查询 | 24 个设施（母婴室 5 + 餐厅 4 + 小吃站 8 + 其他） |
| **活动排期** | MySQL 查询 | 按日期和类型筛选，每天 5 场活动 |
| **用户画像** | MySQL 读写 | 孩子年龄、兴趣偏好、游玩次数 |
| **WebSocket** | 原生 | 低层 ws 协议，流式转发 Dify SSE |

---

## 6. 数据库设计

### 6.1 16 张表一览

| 领域 | 表名 | 说明 | 初始化数据量 |
|:----:|------|------|:-----------:|
| **用户** | `users` | 用户账户（含微信 openid） | 2 条 |
| | `user_profiles` | 用户画像（孩子年龄、兴趣） | 2 条 |
| **票务** | `ticket_types` | 7 种票种定义 | 7 条 |
| | `ticket_orders` | 订单主表 | 运行时创建 |
| | `ticket_items` | 订单明细 | 运行时创建 |
| **项目** | `projects` | 15 个项目 | 15 条 |
| | `facilities` | 24 个便利设施 | 24 条 |
| **排期** | `schedules` | 活动演出排期 | 10+ 条（按日期） |
| **排队** | `queue_records` | 排队持久化记录 | 运行时创建 |
| **会员** | `members` | 会员信息 | 运行时创建 |
| | `point_records` | 积分变动记录 | 运行时创建 |
| **社区** | `community_posts` | 社区帖子 | 3 条（样例） |
| | `post_reviews` | 帖子评论 | 运行时创建 |
| **安全** | `safety_rules` | 安全规则 | 10 条 |
| **运营** | `notifications` | 通知消息 | 运行时创建 |
| | `operation_logs` | 运营日志 | 运行时创建 |

### 6.2 核心 ER 关系

```
users ──1:1──> user_profiles
users ──1:N──> ticket_orders ──1:N──> ticket_items
users ──1:1──> members ──1:N──> point_records
users ──1:N──> queue_records ──N:1──> projects
users ──1:N──> community_posts ──1:N──> post_reviews
users ──1:N──> notifications
projects ──1:N──> schedules
```

### 6.3 建表方式

> ⚠️ 项目未使用 Alembic 迁移。建表方式有两种：
>
> 1. **SQL 脚本** → `scripts/create_missing_tables.sql` 手动执行
> 2. **初始化脚本自动建表** → `python -m scripts.init_data` 会自动创建所有表（推荐）

---

## 7. AI 集成（Dify）

### 7.1 Dify 配置（已在 .env 中配置）

```env
DIFY_API_BASE=http://192.168.88.100/v1
DIFY_APP_KEY_PLANNER=app-d3E27nDbxrJy5tx8PXPH24cH
DIFY_APP_KEY_GUIDE=app-7aS9iyh88pUUCy3WVd22KX3z
DIFY_APP_KEY_TICKET=app-xWJ2Af0SM5dXLnaKixyZbM5w
```

> 这三个 App Key 对应 Dify 平台上的三个应用，需要在 Dify 平台中创建。

### 7.2 Dify 后端 API 工具（6 个）

定义在 `dify_tools_schema.json` 中，供 Dify Agent 通过 Function Calling 调用：

| 工具名 | API 端点 | 用途 |
|--------|----------|------|
| `get_projects` | `GET /api/v1/projects` | 查询项目列表（按区域、类别、适合年龄） |
| `get_queue_time` | `GET /api/v1/queue/{project_id}` | 实时排队人数和等待时间 |
| `get_schedules` | `GET /api/v1/schedules` | 活动演出排期 |
| `get_facilities` | `GET /api/v1/facilities` | 母婴室、餐厅等便利设施 |
| `get_weather` | `GET /api/v1/weather` | 实时天气信息 |
| `get_ticket_prices` | `GET /api/v1/tickets/prices` | 票价信息 |

### 7.3 知识库文档（9 份源文件）

这些 `.md` 文件在 `知识库/` 目录中，**需要导入到 Dify 知识库**。每个文件对应一个知识库：

| 知识库 ID | 源文件 | 适用 Agent | 分段策略 |
|-----------|--------|:----------:|----------|
| kb-projects | `01-乐园项目大全.md` | planner | 按项目分段，每个项目一个 chunk |
| kb-age-guide | `02-各年龄段游玩指南.md` | planner | 按年龄段 + 兴趣分段 |
| kb-events | `06-演出与活动指南.md` | planner | 按演出类型 + 场次分段 |
| kb-safety | `03-安全游玩规则.md` | guide | 按项目类型 + 年龄段分段 |
| kb-facilities | `04-园区便利设施指南.md` | guide | 按设施类型分段 |
| kb-faq | `05-FAQ常见问题解答.md` | planner + guide | QA 模式自动提取 |
| kb-weather | `07-天气应对指南.md` | guide | 按天气类型分段 |
| kb-ticket | `08-购票指南.md` | ticket | 按票种 + 流程分段 |
| kb-member | `09-会员指南.md` | guide | 按等级 + 权益分段 |

### 7.4 意图分类规则（代码中的实际映射）

```python
# 9 类意图 → Agent 映射
INTENT_KEYWORDS = {
    "recommend":  ["推荐", "玩什么", "适合", "有什么项目", "能玩"],  → planner
    "route_plan": ["路线", "规划", "一日游", "怎么安排", "行程"],   → planner
    "event":      ["表演", "演出", "活动", "今天有什么", "花车"],   → planner
    "queue":      ["排队", "等多久", "要排", "多久"],                → guide
    "facility":   ["母婴室", "厕所", "卫生间", "餐厅", "充电"],      → guide
    "safety":     ["安全", "身高", "限制", "能玩吗", "下雨"],        → guide
    "ticket":     ["票价", "买票", "多少钱", "门票", "订单"],        → ticket
    "greeting":   ["你好", "谢谢", "再见", "你是谁"],                 → 后端直接回复
    "unknown":    → fallback 到 planner
}
```

---

## 8. API 接口清单

### 8.1 全部已实现接口（36 个）

| # | 方法 | 路径 | 认证 | 说明 |
|:-:|:----:|------|:----:|------|
| **系统** | | | | |
| 1 | GET | `/` | ❌ | 重定向到前端页面 |
| 2 | GET | `/api/health` | ❌ | 健康检查 |
| **认证** | | | | |
| 3 | POST | `/api/v1/auth/register` | ❌ | 注册 |
| 4 | POST | `/api/v1/auth/login` | ❌ | 登录 |
| 5 | POST | `/api/v1/auth/wechat/login` | ❌ | 微信登录 |
| 6 | PUT | `/api/v1/auth/password` | ✅ | 修改密码 |
| 7 | POST | `/api/v1/auth/refresh` | ❌ | 刷新 Token |
| **用户** | | | | |
| 8 | GET | `/api/v1/users/me` | ✅ | 个人信息（含会员、票据） |
| 9 | PUT | `/api/v1/users/me` | ✅ | 更新昵称/头像 |
| 10 | PUT | `/api/v1/users/me/profile` | ✅ | 更新画像 |
| **项目** | | | | |
| 11 | GET | `/api/v1/projects` | ❌ | 项目列表（含排队信息） |
| 12 | GET | `/api/v1/projects/recommend` | ❌ | 智能推荐 |
| 13 | GET | `/api/v1/projects/{id}` | ❌ | 项目详情 |
| **票务** | | | | |
| 14 | GET | `/api/v1/tickets/prices` | ❌ | 票价查询 |
| 15 | POST | `/api/v1/tickets/orders` | ✅ | 创建订单 |
| 16 | GET | `/api/v1/tickets/orders` | ✅ | 我的订单列表 |
| 17 | GET | `/api/v1/tickets/orders/{no}` | ✅ | 订单详情 |
| 18 | POST | `/api/v1/tickets/orders/{no}/pay` | ✅ | 订单支付 |
| 19 | POST | `/api/v1/tickets/orders/{no}/cancel` | ✅ | 取消订单 |
| 20 | GET | `/api/v1/tickets/my-tickets` | ✅ | 有效票据查询 |
| **AI 对话** | | | | |
| 21 | POST | `/api/v1/chat/message` | ✅ | AI 对话（REST） |
| 22 | WS | `/api/v1/ws/chat?token=` | ✅ | WebSocket 流式对话 |
| **排队** | | | | |
| 23 | POST | `/api/v1/queue/take` | ✅ | 取号 |
| 24 | GET | `/api/v1/queue/my` | ✅ | 我的排队列表 |
| 25 | GET | `/api/v1/queue/{id}` | ❌ | 项目排队信息 |
| 26 | DELETE | `/api/v1/queue/{id}/cancel` | ✅ | 取消排队 |
| 27 | POST | `/api/v1/queue/{id}/call-next` | ✅ | 叫号（运营端） |
| **排期** | | | | |
| 28 | GET | `/api/v1/schedules` | ❌ | 活动排期 |
| **设施** | | | | |
| 29 | GET | `/api/v1/facilities` | ❌ | 便利设施 |
| **会员** | | | | |
| 30 | GET | `/api/v1/member/info` | ✅ | 会员信息 |
| 31 | POST | `/api/v1/member/checkin` | ✅ | 每日签到 |
| **社区** | | | | |
| 32 | GET | `/api/v1/community/posts` | ❌ | 帖子列表 |
| 33 | POST | `/api/v1/community/posts` | ✅ | 发布帖子 |
| 34 | POST | `/api/v1/community/posts/{id}/like` | ✅ | 点赞 |
| 35 | POST | `/api/v1/community/posts/{id}/comments` | ✅ | 评论 |
| **天气** | | | | |
| 36 | GET | `/api/v1/weather` | ❌ | 天气查询 |

### 8.2 统一响应格式

```json
// 成功
{ "code": 200, "message": "success", "data": { ... } }

// 失败（业务错误）
{ "code": 40001, "message": "该手机号已注册", "data": null }

// 失败（参数校验）
{ "code": 40001, "message": "参数错误: phone: 手机号格式不正确", "data": null }

// 失败（服务器错误，HTTP 500）
{ "code": 50001, "message": "服务器内部错误", "data": null }
```

### 8.3 错误码表

| 错误码 | 说明 |
|:------:|------|
| 200 | 成功 |
| 40001 | 参数错误 / 业务校验失败 |
| 40101 | 手机号或密码错误 |
| 40102 | Token 无效或过期 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 50001 | 服务器内部错误 |

---

## 9. 实现状态评估

### ✅ 已完成（后端功能齐备）

| 模块 | 完成度 | 关键文件 |
|------|:------:|---------|
| FastAPI 后端骨架 | 100% | `main.py`, `core/*` |
| 配置管理（.env） | 100% | `core/config.py` |
| JWT 认证 | 100% | `core/security.py` |
| 异常处理 | 100% | `core/exceptions.py` |
| 依赖注入 | 100% | `core/deps.py` |
| 数据库连接 | 100% | `core/database.py` |
| Redis 连接 | 100% | `core/redis.py` |
| 用户注册登录 | 100% | `auth_service.py` |
| 项目 CRUD + 推荐 | 100% | `project_service.py` |
| 票务系统 | 100% | `ticket_service.py` |
| 排队系统（Redis） | 100% | `queue_service.py` |
| Dify 集成 | 100% | `dify_service.py` |
| 意图分类 | 100% | `chat.py` |
| WebSocket 对话 | 100% | `chat_ws.py` |
| 会员系统 | 100% | `misc_service.py` |
| 社区系统 | 100% | `misc_service.py` |
| 天气/设施/排期 | 100% | `misc_service.py` |
| 数据初始化脚本 | 100% | `scripts/init_data.py` |
| 所有 16 张表的模型 | 100% | `models/*.py` |

### ⚠️ 部分完成

| 模块 | 完成度 | 说明 |
|------|:------:|------|
| Web 前端 | ~20% | 仅有 `index.html` Vue 3 CDN 单页，无路由/组件化 |
| 运营管理后台 | 0% | 仅有设计文档 |
| 微信小程序 | 0% | 仅有 uni-app 模板目录 |

### ❌ 未开始

| 模块 | 说明 |
|------|------|
| 微信支付 | 设计中有，实际为模拟支付 |
| 语音输入 | 设计阶段 |
| 游园打卡系统 | 设计阶段 |
| 定时任务 | APScheduler 已安装但在代码中未启用 |
| 单元测试 / 集成测试 | `tests/` 目录为空 |
| Alembic 迁移 | 使用 SQL 脚本替代 |
| Dify 知识库导入 | 源文件已准备好，但需手动导入 Dify |
| Dify Agent/Workflow 配置 | 设计文档中有，需在 Dify 平台中手动创建 |

---

## 10. 开发与运行指南

### 10.1 快速启动

```bash
# 1. 进入项目代码目录
cd Dify_project/Project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
# .env 文件已存在（含实际 Dify API Key 和数据库配置）
# 如需修改，直接编辑 .env

# 4. 确保 MySQL + Redis 已启动

# 5. 初始化数据库（建表 + 灌入全部虚拟数据）
python -m scripts.init_data

# 6. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. 访问
#   前端页面:    http://localhost:8000/web/index.html
#   API 文档:   http://localhost:8000/docs
#   OpenAPI JSON: http://localhost:8000/openapi.json
```

### 10.2 测试账户

| 角色 | 手机号 | 密码 |
|:----:|--------|------|
| 管理员 | `13800000000` | `Admin@123` |
| 测试用户 | 运行注册接口获得 | - |

### 10.3 依赖清单（来自 `requirements.txt`）

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.0
aiomysql>=0.2.0
alembic>=1.13.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
httpx>=0.27.0
redis>=5.0.0
python-multipart>=0.0.9
loguru>=0.7.0
apscheduler>=3.10.0
qrcode[pil]>=7.4
```

### 10.4 环境变量（`.env` 文件）

```env
DATABASE_URL=mysql+aiomysql://root:123456@localhost:3306/lele_park
REDIS_URL=redis://localhost:6379/0
DIFY_API_BASE=http://192.168.88.100/v1
DIFY_APP_KEY_PLANNER=app-d3E27nDbxrJy5tx8PXPH24cH
DIFY_APP_KEY_GUIDE=app-7aS9iyh88pUUCy3WVd22KX3z
DIFY_APP_KEY_TICKET=app-xWJ2Af0SM5dXLnaKixyZbM5w
JWT_SECRET=lele-park-jwt-secret-key-2026
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 11. 项目文档索引

`Dify_project/项目文档/` 目录下的 11 份设计文档一览：

| 编号 | 文件名 | 核心内容 |
|:----:|--------|---------|
| 01 | `01-系统架构设计.md` | 整体架构、技术选型对比、部署架构、安全设计 |
| 02 | `02-Dify平台迁移方案.md` | 从 Coze 迁移到 Dify 的完整映射方案、Workflow 节点设计 |
| 03 | `03-后端技术方案.md` | Python 项目结构、各服务伪代码、中间件设计 |
| 04 | `04-前端技术方案.md` | Vue 3 + uni-app 页面设计、组件树、交互原型 |
| 05 | `05-数据库设计.md` | 16 张表的完整 SQL 定义、索引策略、ER 关系 |
| 06 | `06-API接口设计.md` | 所有接口的请求/响应示例、错误码定义 |
| 07 | `07-Dify工作流与Agent设计.md` | 3 个 Agent 的系统 Prompt、Workflow 节点图 |
| 08 | `08-知识库与数据设计.md` | 9 个知识库的分段策略、chunk 示例 |
| 09 | `09-功能需求设计.md` | 用户故事、功能流程、交互原型 |
| 10 | `10-测试方案.md` | 测试金字塔、API 测试用例示例 |
| 11 | `11-项目计划与里程碑.md` | 4 阶段 18 周排期甘特图、风险矩阵 |

另外，`Dify_project/知识库/` 目录下有 9 份知识库源文档，用于导入 Dify 平台。

---

> **一句话总结：** 这是一个**后端完备**的 AI 驱动的亲子乐园服务平台。后端（FastAPI + SQLAlchemy + Redis + Dify）几乎全功能实现，仅前端（Web / 小程序 / 管理后台）尚待开发。核心亮点是 **Dify 驱动的多 Agent AI 对话系统** + **Redis 支撑的实时排队引擎** + **全套票务与会员体系**。
