# API 接口设计

> **职责**：定义所有 RESTful API 和 WebSocket 接口规范
> **说明**：本项目为学习练习用途，所有接口数据均为虚拟。
> **关联**：[03-后端技术方案.md](./03-后端技术方案.md)

---

## 1. 接口规范

### 1.1 通用规则

| 规则 | 说明 |
|------|------|
| **基础路径** | `/api/v1` |
| **协议** | HTTPS（生产环境） / HTTP（开发环境） |
| **请求格式** | `application/json` |
| **响应格式** | JSON |
| **认证方式** | Bearer Token（JWT） |
| **时间格式** | ISO 8601（`2026-06-05T14:30:00+08:00`） |
| **分页参数** | `page`（页码，从1开始）、`page_size`（每页条数，默认20） |

### 1.2 统一响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": { ... },
    "request_id": "a1b2c3d4"
}
```

### 1.3 错误响应格式

```json
{
    "code": 40001,
    "message": "参数错误：手机号格式不正确",
    "data": null,
    "request_id": "a1b2c3d4"
}
```

### 1.4 错误码表

| 错误码 | HTTP 状态 | 说明 |
|--------|:---------:|------|
| 200 | 200 | 成功 |
| 40001 | 400 | 参数错误 |
| 40101 | 401 | 未登录 |
| 40102 | 401 | Token 过期 |
| 40301 | 403 | 无权限 |
| 40401 | 404 | 资源不存在 |
| 42901 | 429 | 请求过于频繁 |
| 50001 | 500 | 服务器内部错误 |
| 50201 | 502 | Dify 服务异常 |

---

## 2. 接口清单

### 2.1 认证模块 `/api/v1/auth`

#### POST /auth/register — 注册

```json
// Request
{
    "phone": "13800138000",
    "password": "Abc123456",
    "nickname": "乐乐妈",
    "sms_code": "123456"
}

// Response 200
{
    "code": 200,
    "data": {
        "user_id": 1001,
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG...",
        "expires_in": 7200
    }
}
```

#### POST /auth/login — 登录

```json
// Request
{
    "phone": "13800138000",
    "password": "Abc123456"
}

// Response 200
{
    "code": 200,
    "data": {
        "user_id": 1001,
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG...",
        "expires_in": 7200
    }
}
```

#### POST /auth/wechat/login — 微信小程序登录

```json
// Request
{
    "code": "wx_login_code_xxx"
}

// Response 200
{
    "code": 200,
    "data": {
        "user_id": 1001,
        "is_new_user": false,
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG..."
    }
}
```

#### POST /auth/refresh — 刷新 Token

```json
// Request
{
    "refresh_token": "eyJhbG..."
}

// Response 200
{
    "code": 200,
    "data": {
        "access_token": "eyJhbG...(new)",
        "expires_in": 7200
    }
}

// Error 401
{
    "code": 40102,
    "message": "Refresh Token 已过期，请重新登录"
}
```

#### POST /auth/sms/send — 发送短信验证码

```json
// Request
{
    "phone": "13800138000"
}

// Response 200
{
    "code": 200,
    "data": {
        "expire_seconds": 300
    }
}

// Error 429 (60秒内重复请求)
{
    "code": 42901,
    "message": "验证码发送过于频繁，请60秒后重试"
}
```

---

### 2.2 用户模块 `/api/v1/users`

#### GET /users/me — 获取当前用户信息

```json
// Response 200
{
    "code": 200,
    "data": {
        "id": 1001,
        "nickname": "乐乐妈",
        "avatar_url": "https://...",
        "phone": "138****8000",
        "profile": {
            "child_age": "3岁",
            "interests": ["动物", "表演"],
            "visit_count": 2
        },
        "member": {
            "level": 2,
            "points": 1580,
            "balance": 50.00
        }
    }
}
```

#### PUT /users/me — 更新用户信息

#### PUT /users/me/profile — 更新用户画像（孩子年龄、兴趣等）

---

### 2.3 项目模块 `/api/v1/projects`

#### GET /projects — 项目列表

```json
// Query: ?zone=梦幻城堡区&category=ride&suitable_age=全年龄&status=open

// Response 200
{
    "code": 200,
    "data": {
        "total": 15,
        "items": [
            {
                "id": 1,
                "project_code": "P001",
                "name": "旋转木马",
                "zone": "梦幻城堡区",
                "category": "ride",
                "suitable_age": "全年龄",
                "min_height": null,
                "intensity": "low",
                "is_indoor": false,
                "duration_minutes": 10,
                "cover_image": "https://...",
                "status": "open",
                "queue_info": {
                    "queue_time": 15,
                    "crowd_level": "适中"
                }
            }
        ]
    }
}
```

#### GET /projects/{id} — 项目详情

```json
// GET /api/v1/projects/1

// Response 200
{
    "code": 200,
    "data": {
        "id": 1,
        "project_code": "P001",
        "name": "旋转木马",
        "zone": "梦幻城堡区",
        "category": "ride",
        "description": "经典童话风格旋转木马，双层设计，配有主题音乐...",
        "suitable_age": "全年龄",
        "min_height": null,
        "intensity": "low",
        "is_indoor": false,
        "has_ac": false,
        "stroller_friendly": true,
        "duration_minutes": 10,
        "capacity": 40,
        "fast_pass": false,
        "queue_enabled": true,
        "location_desc": "梦幻城堡区中心位置",
        "tips": "适合低龄宝宝首次体验，家长可陪同乘坐...",
        "safety_notes": "婴幼儿需家长陪同。",
        "status": "open",
        "queue_info": {
            "queue_time": 15,
            "crowd_level": "适中",
            "current_number": 35
        }
    }
}
```

#### GET /projects/recommend — 智能推荐

```json
// Query: ?age=3&interests=动物,表演&indoor=false&date=2026-06-05

// Response 200
{
    "code": 200,
    "data": {
        "recommendations": [
            {
                "project": { ... },
                "match_score": 95,
                "match_reasons": ["适合3岁", "包含动物互动", "当前排队短"],
                "safety_tips": "接触动物后请立即洗手消毒"
            }
        ]
    }
}
```

#### GET /projects/{id}/reviews — 项目评价

---

### 2.4 AI 对话模块 `/api/v1/chat`

#### POST /chat/message — 发送消息（非流式）

```json
// Request
{
    "message": "3岁宝宝能玩什么？",
    "conversation_id": "conv_xxx",  // 可选，续接对话
    "user_context": {
        "child_age": "3岁",
        "interests": ["动物"]
    }
}

// Response 200
{
    "code": 200,
    "data": {
        "conversation_id": "conv_xxx",
        "answer": "以下是适合3岁宝宝的项目推荐...",
        "intent": "recommend",
        "agent": "lele-travel-planner",
        "suggested_questions": ["帮我规划路线", "旋转木马排多久"]
    }
}
```

#### WebSocket /ws/chat — 流式对话

```
连接: ws://api.lelepark.com/api/v1/ws/chat?token=xxx

发送:
{
    "type": "chat",
    "message": "3岁宝宝能玩什么？",
    "conversation_id": "conv_xxx"
}

接收（流式）:
{"type": "thinking", "content": "正在分析您的需求..."}
{"type": "token", "content": "以下"}
{"type": "token", "content": "是适合"}
{"type": "token", "content": "3岁"}
{"type": "token", "content": "宝宝"}
{"type": "done", "conversation_id": "conv_xxx", "intent": "recommend"}
{"type": "suggested", "questions": ["帮我规划路线", "旋转木马排多久"]}
```

#### GET /chat/history — 对话历史列表

#### GET /chat/history/{conversation_id} — 某次对话详情

#### DELETE /chat/history/{conversation_id} — 删除对话

---

### 2.5 票务模块 `/api/v1/tickets`

#### GET /tickets/prices — 查询票价

```json
// Response 200
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "name": "成人票",
            "code": "ADULT",
            "category": "adult",
            "price": 120.00,
            "discount_price": 108.00,
            "description": "身高≥1.5m"
        },
        {
            "id": 2,
            "name": "儿童票",
            "code": "CHILD",
            "category": "child",
            "price": 80.00,
            "discount_price": 72.00,
            "description": "身高0.8m-1.5m"
        },
        {
            "id": 3,
            "name": "家庭套票（2大1小）",
            "code": "FAMILY_2A1C",
            "category": "family",
            "price": 280.00,
            "discount_price": 258.00,
            "includes": ["成人票×2", "儿童票×1"]
        }
    ]
}
```

#### POST /tickets/orders — 创建订单

```json
// Request
{
    "visit_date": "2026-06-10",
    "items": [
        {"ticket_type_id": 1, "quantity": 2},
        {"ticket_type_id": 2, "quantity": 1}
    ],
    "visitors": [
        {"name": "张三", "id_no": "encrypted_xxx"},
        {"name": "李四", "id_no": "encrypted_xxx"},
        {"name": "张小宝", "id_no": "encrypted_xxx"}
    ],
    "coupon_code": "SUMMER2026"
}

// Response 200
{
    "code": 200,
    "data": {
        "order_no": "T20260605143000001",
        "total_amount": 320.00,
        "discount_amount": 20.00,
        "pay_amount": 300.00,
        "pay_params": {
            "prepay_id": "wx_prepay_xxx"
        }
    }
}
```

#### GET /tickets/orders — 我的订单列表

#### GET /tickets/orders/{order_no} — 订单详情

#### POST /tickets/orders/{order_no}/cancel — 取消订单

```json
// POST /api/v1/tickets/orders/T20260605143000001/cancel

// Response 200
{
    "code": 200,
    "data": {
        "order_no": "T20260605143000001",
        "status": "cancelled",
        "refund_status": "refunding",
        "refund_amount": 300.00
    }
}

// Error 400
{
    "code": 40001,
    "message": "当前状态(used)不可取消"
}
```

#### POST /tickets/orders/{order_no}/pay — 模拟支付

```json
// POST /api/v1/tickets/orders/T20260605143000001/pay
// 学习项目使用模拟支付，无需真实微信支付

// Response 200
{
    "code": 200,
    "data": {
        "order_no": "T20260605143000001",
        "status": "confirmed",
        "qr_code": "LELE-T20260605143000001-a3b4c5d6"
    }
}
```

#### GET /tickets/orders — 我的订单列表

```json
// Query: ?page=1&page_size=10

// Response 200
{
    "code": 200,
    "data": {
        "total": 3,
        "items": [
            {
                "order_no": "T20260605143000001",
                "visit_date": "2026-06-10",
                "total_amount": 300.00,
                "pay_amount": 300.00,
                "status": "confirmed",
                "pay_status": "paid",
                "qr_code": "LELE-T20260605143000001-a3b4c5d6",
                "items": [
                    {"name": "成人票", "quantity": 2, "unit_price": 108.00},
                    {"name": "儿童票", "quantity": 1, "unit_price": 72.00}
                ],
                "created_at": "2026-06-05T14:30:00"
            }
        ]
    }
}
```

#### GET /tickets/orders/{order_no} — 订单详情

```json
// Response 200 (同列表中单条数据，额外包含 visitors 信息)
{
    "code": 200,
    "data": {
        "order_no": "T20260605143000001",
        "visit_date": "2026-06-10",
        "total_amount": 320.00,
        "pay_amount": 300.00,
        "discount_amount": 20.00,
        "status": "confirmed",
        "qr_code": "LELE-T20260605143000001-a3b4c5d6",
        "items": [...],
        "visitors": [
            {"name": "张三", "ticket_type": "成人票"},
            {"name": "李四", "ticket_type": "成人票"},
            {"name": "张小宝", "ticket_type": "儿童票"}
        ],
        "created_at": "2026-06-05T14:30:00"
    }
}
```

---

### 2.6 排队模块 `/api/v1/queue`

#### POST /queue/take — 线上取号

```json
// Request
{
    "project_id": 1
}

// Response 200
{
    "code": 200,
    "data": {
        "queue_number": 42,
        "current_number": 35,
        "ahead_count": 7,
        "estimated_wait": 21,
        "project_name": "旋转木马"
    }
}
```

#### GET /queue/my — 我当前所有排队

```json
// Response 200
{
    "code": 200,
    "data": [
        {
            "project_id": 1,
            "project_name": "旋转木马",
            "queue_number": 42,
            "current_number": 38,
            "ahead_count": 4,
            "estimated_wait": 12,
            "status": "waiting"
        },
        {
            "project_id": 5,
            "project_name": "碰碰车乐园",
            "queue_number": 15,
            "current_number": 15,
            "ahead_count": 0,
            "estimated_wait": 0,
            "status": "serving"
        }
    ]
}
```

#### GET /queue/{project_id} — 查询指定项目排队状态

```json
// GET /api/v1/queue/1

// Response 200
{
    "code": 200,
    "data": {
        "project_id": 1,
        "project_name": "旋转木马",
        "queue_length": 12,
        "estimated_wait": 36,
        "current_number": 35,
        "crowd_level": "适中",
        "status": "open"
    }
}
```

#### DELETE /queue/{project_id}/cancel — 取消排队

```json
// DELETE /api/v1/queue/1/cancel

// Response 200
{
    "code": 200,
    "data": {
        "message": "排队已取消",
        "queue_number": 42
    }
}
```

#### GET /queue/{project_id}/realtime — 实时排队数据（Redis）

```json
// GET /api/v1/queue/1/realtime
// 直接从 Redis 读取，适合 Dify 工具调用

// Response 200
{
    "code": 200,
    "data": {
        "project_id": "1",
        "queue_length": 12,
        "estimated_wait": 36,
        "status": "open",
        "crowd_level": "适中",
        "updated_at": "2026-06-05T14:30:00"
    }
}
```

---

### 2.7 排期模块 `/api/v1/schedules`

#### GET /schedules — 排期列表

```json
// Query: ?date=2026-06-05&type=show

// Response 200
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "event_name": "海洋动物表演（上午场）",
            "event_type": "show",
            "start_time": "10:30",
            "end_time": "11:00",
            "location": "海洋剧场",
            "capacity": 800,
            "enrolled_count": 120,
            "status": "normal"
        }
    ]
}
```

#### POST /schedules/{id}/remind — 设置提醒

```json
// POST /api/v1/schedules/1/remind

// Request
{
    "remind_minutes_before": 15
}

// Response 200
{
    "code": 200,
    "data": {
        "message": "提醒设置成功，将在演出前15分钟通知您",
        "schedule_id": 1,
        "remind_at": "2026-06-05T10:15:00"
    }
}
```

#### POST /schedules/{id}/enroll — 活动报名

```json
// POST /api/v1/schedules/1/enroll

// Response 200
{
    "code": 200,
    "data": {
        "message": "报名成功",
        "schedule_id": 1,
        "enrolled_count": 121,
        "remaining": 679
    }
}

// Error 400 (已满)
{
    "code": 40001,
    "message": "该场次名额已满"
}
```

---

### 2.8 设施模块 `/api/v1/facilities`

#### GET /facilities — 设施列表

```json
// Query: ?type=nursing&zone=梦幻城堡区

// Response 200
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "name": "梦幻城堡区母婴室",
            "type": "nursing",
            "zone": "梦幻城堡区",
            "location_desc": "旋转木马旁，步行约3分钟",
            "open_time": "09:00",
            "close_time": "18:00",
            "features": ["哺乳隔间", "换尿布台", "热水", "微波炉", "婴儿床"],
            "status": "open"
        }
    ]
}
```

---

### 2.9 会员模块 `/api/v1/member`

#### GET /member/info — 会员信息

```json
// Response 200
{
    "code": 200,
    "data": {
        "member_no": "M20260600001",
        "level": 2,
        "level_name": "银卡会员",
        "points": 1580,
        "total_points": 3200,
        "balance": 50.00,
        "card_type": "silver",
        "join_date": "2026-01-15",
        "next_level_points": 5000,
        "benefits": [
            "9.5折购票",
            "生日礼品",
            "优先客服"
        ]
    }
}
```

#### GET /member/points — 积分明细

```json
// Query: ?page=1&page_size=20

// Response 200
{
    "code": 200,
    "data": {
        "total": 15,
        "items": [
            {
                "points": 300,
                "balance_after": 1580,
                "type": "earn_purchase",
                "description": "购买家庭套票获得积分",
                "related_order": "T20260605143000001",
                "created_at": "2026-06-05T14:30:00"
            },
            {
                "points": 5,
                "balance_after": 1285,
                "type": "earn_checkin",
                "description": "每日签到",
                "created_at": "2026-06-04T09:00:00"
            }
        ]
    }
}
```

#### POST /member/checkin — 每日签到

```json
// Response 200
{
    "code": 200,
    "data": {
        "message": "签到成功！获得5积分",
        "points_earned": 5,
        "total_points": 1585,
        "consecutive_days": 3
    }
}

// Error 400 (已签到)
{
    "code": 40001,
    "message": "今天已经签到过了"
}
```

#### GET /member/benefits — 会员权益列表

```json
// Response 200
{
    "code": 200,
    "data": [
        {"level": 1, "name": "普通会员", "condition": "注册即得", "benefits": ["基础服务"]},
        {"level": 2, "name": "银卡会员", "condition": "消费≥500元或游玩≥3次", "benefits": ["9.5折购票","生日礼品"]},
        {"level": 3, "name": "金卡会员", "condition": "消费≥2000元或游玩≥10次", "benefits": ["9折购票","快速通道1次/月"]},
        {"level": 4, "name": "钻石会员", "condition": "消费≥5000元或游玩≥25次", "benefits": ["8.5折购票","快速通道3次/月","VIP休息室"]}
    ]
}
```

#### POST /member/recharge — 储值卡充值

```json
// Request
{
    "amount": 100.00
}

// Response 200
{
    "code": 200,
    "data": {
        "balance_before": 50.00,
        "amount": 100.00,
        "balance_after": 150.00,
        "points_earned": 100
    }
}
```

---

### 2.10 社区模块 `/api/v1/community`

#### GET /community/posts — 帖子列表

```json
// Query: ?type=travelogue&page=1&page_size=10&sort=latest

// Response 200
{
    "code": 200,
    "data": {
        "total": 56,
        "items": [
            {
                "id": 1,
                "title": "带3岁宝宝乐乐乐园一日游攻略",
                "content": "今天带宝宝去了乐乐乐园，分享一下我们的游玩经历...",
                "images": ["https://.../img1.jpg", "https://.../img2.jpg"],
                "post_type": "travelogue",
                "author": {
                    "id": 1001,
                    "nickname": "乐乐妈",
                    "avatar_url": "https://..."
                },
                "view_count": 230,
                "like_count": 45,
                "comment_count": 12,
                "is_featured": true,
                "created_at": "2026-06-05T18:00:00"
            }
        ]
    }
}
```

#### POST /community/posts — 发布帖子

```json
// Request
{
    "title": "周末带娃乐乐乐园亲子游",
    "content": "这个周末带宝宝去了乐乐乐园...",
    "images": ["base64_encoded_image..."],
    "post_type": "travelogue",
    "tags": ["亲子游", "3岁", "攻略"]
}

// Response 200
{
    "code": 200,
    "data": {
        "id": 57,
        "message": "发布成功，待审核",
        "status": "pending_review"
    }
}
```

#### GET /community/posts/{id} — 帖子详情

```json
// Response 200
{
    "code": 200,
    "data": {
        "id": 1,
        "title": "带3岁宝宝乐乐乐园一日游攻略",
        "content": "...(完整内容)...",
        "images": [...],
        "post_type": "travelogue",
        "author": {...},
        "comments": [
            {
                "id": 101,
                "content": "太棒了，收藏！",
                "author": {"id": 1002, "nickname": "宝爸"},
                "like_count": 3,
                "created_at": "2026-06-05T19:00:00",
                "replies": []
            }
        ],
        "view_count": 231,
        "like_count": 45,
        "is_liked_by_me": false,
        "created_at": "2026-06-05T18:00:00"
    }
}
```

#### POST /community/posts/{id}/like — 点赞

```json
// Response 200 (切换状态：未赞→赞，已赞→取消)
{
    "code": 200,
    "data": {
        "liked": true,
        "like_count": 46
    }
}
```

#### POST /community/posts/{id}/comments — 发表评论

```json
// Request
{
    "content": "感谢分享！请问旋转木马排队久吗？",
    "parent_id": null
}

// Response 200
{
    "code": 200,
    "data": {
        "id": 102,
        "content": "感谢分享！请问旋转木马排队久吗？",
        "created_at": "2026-06-05T20:00:00"
    }
}
```

---

### 2.11 天气模块 `/api/v1/weather`

#### GET /weather — 实时天气

```json
// Response 200
{
    "code": 200,
    "data": {
        "temperature": 28,
        "humidity": 65,
        "weather": "多云",
        "wind_level": 2,
        "uv_index": 5,
        "aqi": 45,
        "suggestion": "天气晴好，适合户外游玩，建议涂抹防晒霜"
    }
}
```

---

### 2.12 运营管理 `/api/v1/admin`

#### GET /admin/dashboard — 数据看板

```json
// Response 200
{
    "code": 200,
    "data": {
        "today": {
            "visitors": 1256,
            "revenue": 89320.00,
            "orders": 312,
            "ai_conversations": 876,
            "avg_satisfaction": 4.6
        },
        "realtime": {
            "in_park_count": 843,
            "top_projects": [
                {"name": "旋转木马", "queue_time": 15, "crowd_level": "适中"},
                {"name": "过山车·极速飞鹰", "queue_time": 45, "crowd_level": "拥挤"},
                {"name": "海洋动物表演", "queue_time": 0, "crowd_level": "空闲"}
            ]
        },
        "trends": {
            "weekly_visitors": [800, 920, 1100, 1256, 0, 0, 0],
            "weekly_revenue": [56000, 65000, 78000, 89320, 0, 0, 0]
        }
    }
}
```

#### GET /admin/chat-logs — 对话日志

```json
// Query: ?page=1&page_size=20&intent=recommend&date=2026-06-05

// Response 200
{
    "code": 200,
    "data": {
        "total": 876,
        "intent_distribution": {
            "recommend": 234,
            "queue": 189,
            "route_plan": 156,
            "facility": 134,
            "event": 89,
            "ticket": 45,
            "safety": 29
        },
        "items": [
            {
                "id": "log_001",
                "user_id": 1001,
                "user_message": "3岁宝宝能玩什么？",
                "intent": "recommend",
                "agent": "lele-travel-planner",
                "response_time_ms": 2340,
                "satisfaction": 5,
                "created_at": "2026-06-05T14:30:00"
            }
        ]
    }
}
```

#### POST /admin/knowledge/sync — 同步知识库到 Dify

```json
// Request
{
    "knowledge_ids": ["kb-projects", "kb-faq"],
    "force": false
}

// Response 200
{
    "code": 200,
    "data": {
        "synced": 2,
        "failed": 0,
        "details": [
            {"id": "kb-projects", "status": "success", "segments": 15},
            {"id": "kb-faq", "status": "success", "segments": 25}
        ]
    }
}
```

---

## 3. 接口总览

| 模块 | 接口数 | 主要功能 |
|------|:------:|----------|
| 认证 | 5 | 注册、登录、微信登录、刷新Token、短信 |
| 用户 | 3 | 个人信息、画像、偏好 |
| 项目 | 5 | 列表、详情、推荐、评价 |
| AI 对话 | 5 | 消息、WebSocket、历史、删除 |
| 票务 | 7 | 票价、下单、订单、退款、电子票 |
| 排队 | 5 | 取号、我的排队、查询、取消、实时 |
| 排期 | 3 | 列表、提醒、报名 |
| 设施 | 1 | 列表 |
| 会员 | 5 | 信息、积分、签到、权益、充值 |
| 社区 | 5 | 帖子CRUD、点赞、评论 |
| 天气 | 1 | 实时天气 |
| 运营管理 | 8 | 看板、项目管理、订单、用户、日志、同步 |
| **合计** | **54** | |
