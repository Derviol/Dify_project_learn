# -*- coding: utf-8 -*-
"""
数据库初始化脚本 — 乐乐亲子乐园智能服务系统
将所有虚拟乐园基础数据写入 MySQL

运行方式:
    cd Project
    python -m scripts.init_data

前置条件:
    1. MySQL 已启动，数据库 lele_park 已创建
    2. .env 文件中 DATABASE_URL 配置正确
    3. 依赖已安装: pip install sqlalchemy[asyncio] aiomysql passlib[bcrypt] python-dotenv
"""
import asyncio
import json
import os
import sys
from datetime import date, time, datetime
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# ============================================================
#  数据模型定义（简化版，仅用于初始化脚本）
#  正式项目中从 app.models 导入
# ============================================================
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Boolean, Float,
    Date, Time, DateTime, Enum, JSON, ForeignKey, Index,
    create_engine, text, func,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255))
    nickname = Column(String(50), nullable=False)
    avatar_url = Column(String(500))
    wechat_openid = Column(String(100), unique=True)
    wechat_unionid = Column(String(100))
    role = Column(String(10), server_default=text("'user'"))
    status = Column(String(10), server_default=text("'active'"))
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    child_age = Column(String(20))
    interests = Column(JSON)
    visit_count = Column(Integer, default=0)
    special_needs = Column(Text)
    preferred_zones = Column(JSON)
    last_visit_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Project(Base):
    __tablename__ = "projects"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    zone = Column(String(50), nullable=False)
    category = Column(String(10), nullable=False)
    description = Column(Text)
    suitable_age = Column(String(50))
    min_height = Column(Float)
    max_height = Column(Float)
    intensity = Column(String(10), server_default=text("'low'"))
    is_indoor = Column(Boolean, default=False)
    has_ac = Column(Boolean, default=False)
    stroller_friendly = Column(Boolean, default=True)
    duration_minutes = Column(Integer)
    capacity = Column(Integer)
    fast_pass = Column(Boolean, default=False)
    fast_pass_price = Column(Float)
    queue_enabled = Column(Boolean, default=True)
    cover_image = Column(String(500))
    location_desc = Column(String(200))
    tips = Column(Text)
    safety_notes = Column(Text)
    status = Column(String(10), server_default=text("'open'"))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Facility(Base):
    __tablename__ = "facilities"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(30), nullable=False)
    zone = Column(String(50))
    location_desc = Column(String(200))
    open_time = Column(String(10))
    close_time = Column(String(10))
    features = Column(JSON)
    price_info = Column(String(200))
    contact_phone = Column(String(20))
    status = Column(String(10), server_default=text("'open'"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SafetyRule(Base):
    __tablename__ = "safety_rules"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_code = Column(String(20), unique=True, nullable=False)
    project_type = Column(String(50))
    age_group = Column(String(20))
    weather = Column(String(20))
    rule_content = Column(Text, nullable=False)
    priority = Column(String(10), server_default=text("'medium'"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TicketType(Base):
    __tablename__ = "ticket_types"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    category = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    discount_price = Column(Float)
    description = Column(Text)
    includes = Column(JSON)
    valid_days = Column(Integer, default=1)
    usage_limit = Column(Integer, default=1)
    status = Column(String(10), server_default=text("'active'"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    event_name = Column(String(100), nullable=False)
    event_type = Column(String(15), nullable=False)
    event_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    location = Column(String(100))
    capacity = Column(Integer)
    enrolled_count = Column(Integer, default=0)
    theme = Column(String(100))
    description = Column(Text)
    notes = Column(Text)
    status = Column(String(15), server_default=text("'normal'"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ============================================================
#  初始数据定义
# ============================================================

# ---------- 项目数据（15 个项目） ----------
PROJECTS = [
    # P001 旋转木马
    {
        "project_code": "P001", "name": "旋转木马", "zone": "梦幻城堡区",
        "category": "ride",
        "description": "经典童话风格旋转木马，双层设计，配有主题音乐。上层为固定座骑（适合小宝宝），下层为上下起伏座骑（适合大儿童）。木马造型包括独角兽、天鹅、马车等童话角色，夜间灯光效果尤为梦幻。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 10, "capacity": 40, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/carousel.jpg",
        "location_desc": "梦幻城堡区中心位置",
        "tips": "适合低龄宝宝首次体验，家长可陪同乘坐。每匹马限坐1位儿童+1位家长陪同。上层马车座可坐2位家长+1位婴儿。建议排队前先让宝宝看一轮，确认不害怕再排队。",
        "safety_notes": "婴幼儿需家长陪同。",
        "status": "open", "sort_order": 1,
    },
    # P002 小火车
    {
        "project_code": "P002", "name": "小火车", "zone": "欢乐农场区",
        "category": "ride",
        "description": "环绕园区半周的观光小火车，途经梦幻城堡区、欢乐农场区、海洋探险区等主题区。列车为复古蒸汽火车造型，每节车厢配有遮阳棚，沿途有卡通人物挥手互动。",
        "suitable_age": "1-6岁", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 15, "capacity": 60, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/train.jpg",
        "location_desc": "欢乐农场区入口处",
        "tips": "适合全家一起乘坐，可欣赏园区全景。小火车不返回起点，终点在科普区附近。沿途经过动物互动区。建议作为入园第一个项目，轻松熟悉园区布局。",
        "safety_notes": None, "status": "open", "sort_order": 2,
    },
    # P003 泡泡海洋馆
    {
        "project_code": "P003", "name": "泡泡海洋馆", "zone": "海洋探险区",
        "category": "venue",
        "description": "室内恒温泡泡互动馆，设有婴幼儿专属戏水区、泡泡制造机、泡泡画板等互动设施。水温恒温32°C，即使冬季也能舒适玩耍。",
        "suitable_age": "0-5岁", "min_height": None, "intensity": "low",
        "is_indoor": True, "has_ac": True, "stroller_friendly": True,
        "duration_minutes": 30, "capacity": 80, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/bubble_ocean.jpg",
        "location_desc": "海洋探险区东侧（室内）",
        "tips": "有专门的婴幼儿区（水深20cm），安全温和。提供防水围兜和袖套。室内恒温，不受天气影响。建议给宝宝带一套备用衣物。",
        "safety_notes": "婴幼儿须穿戴防水纸尿裤+救生衣，单次玩水不超过15分钟。",
        "status": "open", "sort_order": 3,
    },
    # P004 过山车·极速飞鹰
    {
        "project_code": "P004", "name": "过山车·极速飞鹰", "zone": "冒险区",
        "category": "ride",
        "description": "园区最刺激的过山车，最高时速80km/h，轨道全长600米，含3个失重俯冲和1个360°回环。采用双人并排座椅，家长可与孩子同坐。",
        "suitable_age": "6-12岁", "min_height": 1.20, "intensity": "high",
        "is_indoor": False, "has_ac": False, "stroller_friendly": False,
        "duration_minutes": 3, "capacity": 24, "fast_pass": True, "fast_pass_price": 30.00,
        "queue_enabled": True,
        "cover_image": "/images/projects/roller_coaster.jpg",
        "location_desc": "冒险区中心位置",
        "tips": "建议使用快速通道避开高峰排队。乘坐前取下眼镜、手机、硬币等松散物品。全程保持坐姿，双手抓紧扶手。",
        "safety_notes": "身高不足1.2m严禁乘坐。心脏病、高血压、癫痫患者、孕妇禁止乘坐。近期有手术史或身体不适者请勿体验。建议饭后30分钟以上再乘坐。",
        "status": "open", "sort_order": 4,
    },
    # P005 碰碰车乐园
    {
        "project_code": "P005", "name": "碰碰车乐园", "zone": "冒险区",
        "category": "ride",
        "description": "亲子碰碰车乐园，配有儿童专用低速车型和成人标准车型。场地面积约200㎡，设有防撞护栏，安全系数高。",
        "suitable_age": "3-12岁", "min_height": 0.90, "intensity": "medium",
        "is_indoor": False, "has_ac": False, "stroller_friendly": False,
        "duration_minutes": 8, "capacity": 20, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/bumper_cars.jpg",
        "location_desc": "冒险区西侧",
        "tips": "3-6岁需家长陪同驾驶，6岁以上可独立驾驶。儿童低速车型最高时速5km/h。每场8分钟。建议穿运动鞋。",
        "safety_notes": "禁止故意高速正面碰撞、追撞停靠车辆。长发建议扎起，避免被卷入。",
        "status": "open", "sort_order": 5,
    },
    # P007 海洋动物表演
    {
        "project_code": "P007", "name": "海洋动物表演", "zone": "海洋探险区",
        "category": "show",
        "description": "海豚和海狮的精彩联合表演，包含高空跳跃、球类互动、人豚共舞等节目。表演结束后有互动环节，幸运观众可上台与海豚合影。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 30, "capacity": 800, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/dolphin_show.jpg",
        "location_desc": "海洋剧场（海洋探险区）",
        "tips": "建议提前15分钟入场，前排位置互动机会多。前排1-3排可能被水溅到（海狮拍水环节），可带一件备用外套。表演结束后可自费与海豚合影（30元/次）。每日3场：10:30/14:00/16:00。",
        "safety_notes": "关闭闪光灯，不要站立观看，控制音量。",
        "status": "open", "sort_order": 7,
    },
    # P008 海底隧道
    {
        "project_code": "P008", "name": "海底隧道", "zone": "海洋探险区",
        "category": "venue",
        "description": "全长100米的透明海底隧道，360°展示海洋生态。可近距离观察鲨鱼、海龟、鳐鱼、小丑鱼等50多种海洋生物。隧道内设有自动步道，站着不动也能缓缓前行。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": True, "has_ac": True, "stroller_friendly": True,
        "duration_minutes": 20, "capacity": 200, "fast_pass": False, "queue_enabled": False,
        "cover_image": "/images/projects/undersea_tunnel.jpg",
        "location_desc": "海洋探险区地下层",
        "tips": "推车可通行，无需抱娃。室内空调开放，夏季避暑首选。隧道内光线较暗，小月龄宝宝建议抱着安抚。有海底生物知识牌，边走边学。随到随进。",
        "safety_notes": None, "status": "open", "sort_order": 8,
    },
    # P009 恐龙科普馆
    {
        "project_code": "P009", "name": "恐龙科普馆", "zone": "科普区",
        "category": "venue",
        "description": "集4D恐龙电影、仿真恐龙模型和化石挖掘体验于一体的科普场馆。馆内有10多种1:1比例的仿真恐龙（可动、有声效）、化石挖掘沙池和互动科普屏。",
        "suitable_age": "3-12岁", "min_height": None, "intensity": "low",
        "is_indoor": True, "has_ac": True, "stroller_friendly": True,
        "duration_minutes": 30, "capacity": 150, "fast_pass": False, "queue_enabled": False,
        "cover_image": "/images/projects/dinosaur_museum.jpg",
        "location_desc": "科普区室内馆",
        "tips": "4D电影每半小时一场，建议提前看好场次。含3D眼镜和座椅震动效果，部分小龄宝宝可能害怕。化石挖掘区免费体验，挖到'化石'可拍照留念。建议3岁以上儿童体验。",
        "safety_notes": "含惊吓元素（突然出现的道具、炮声等），建议家长陪同。3-4岁家长全程陪同。",
        "status": "open", "sort_order": 9,
    },
    # P010 花车巡游
    {
        "project_code": "P010", "name": "花车巡游", "zone": "主干道全程",
        "category": "show",
        "description": "每日下午的主题花车巡游，6辆主题花车（海洋主题、童话主题、动物主题、太空主题等）+卡通人偶方队+舞蹈表演。巡游路线从欢乐农场区出发，沿主干道至梦幻城堡区。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 25, "capacity": 0, "fast_pass": False, "queue_enabled": False,
        "cover_image": "/images/projects/parade.jpg",
        "location_desc": "主干道全程",
        "tips": "沿途均可观赏，无需排队。中央广场区域视野最佳，建议提前10分钟找好位置。花车经过时工作人员会派发小礼品。结束前5分钟可提前离开，避开散场人流。每日16:30开始。",
        "safety_notes": "散场时注意人流安全，抱好小宝宝。",
        "status": "open", "sort_order": 10,
    },
    # P011 小丑互动秀
    {
        "project_code": "P011", "name": "小丑互动秀", "zone": "中央广场",
        "category": "show",
        "description": "小丑魔术表演+气球造型+互动游戏。小丑会用气球编出各种造型（小狗、宝剑、花朵等）送给小朋友，现场还会邀请小朋友上台互动做游戏。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 20, "capacity": 300, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/clown_show.jpg",
        "location_desc": "中央广场",
        "tips": "宝宝可参与互动游戏赢小奖品。气球造型免费赠送，每个小朋友限领一个。前排位置互动机会更多。每日3场：10:30/14:00/16:30。",
        "safety_notes": None, "status": "open", "sort_order": 11,
    },
    # P012 魔术秀
    {
        "project_code": "P012", "name": "魔术秀", "zone": "梦幻城堡区",
        "category": "show",
        "description": "专业魔术师的大型舞台魔术表演，包含大变活人、悬浮术、鸽子魔术、火焰魔术等经典节目。舞台效果华丽，音乐灯光配合精彩。",
        "suitable_age": "3岁以上", "min_height": None, "intensity": "low",
        "is_indoor": True, "has_ac": True, "stroller_friendly": True,
        "duration_minutes": 25, "capacity": 400, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/magic_show.jpg",
        "location_desc": "梦幻剧场（室内）",
        "tips": "含部分惊吓元素（突然出现的道具、炮声等），建议家长陪同。建议3岁以上儿童观看，胆小宝宝请家长评估。室内有空调，夏日避暑好选择。每日3场：11:00/15:00/17:00。",
        "safety_notes": "禁止闪光灯拍照。",
        "status": "open", "sort_order": 12,
    },
    # P013 摩天轮·梦幻之眼
    {
        "project_code": "P013", "name": "摩天轮·梦幻之眼", "zone": "梦幻城堡区",
        "category": "ride",
        "description": "园区地标性摩天轮，总高60米，共24个观景轿厢。每个轿厢可坐4人，配备独立空调和蓝牙音箱，可连接手机播放音乐。最高点可俯瞰全园及周边风景。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": True, "stroller_friendly": True,
        "duration_minutes": 20, "capacity": 96, "fast_pass": True, "fast_pass_price": 20.00,
        "queue_enabled": True,
        "cover_image": "/images/projects/ferris_wheel.jpg",
        "location_desc": "梦幻城堡区南侧",
        "tips": "每个轿厢最多4人。轿厢内带空调，夏天也很舒适。日落时段体验最佳，可欣赏晚霞。有恐高症的家长建议评估后再乘坐。",
        "safety_notes": "轿厢内禁止站立、跳跃、晃动。每厢限坐4人。轿厢门关闭后请勿自行打开。",
        "status": "open", "sort_order": 13,
    },
    # P014 水上乐园·浪花谷
    {
        "project_code": "P014", "name": "水上乐园·浪花谷", "zone": "水上乐园区",
        "category": "water",
        "description": "大型亲子水上乐园，含儿童滑梯区（3条不同坡度滑梯）、人工造浪池（定时造浪）、漂流河（全长200米）和婴幼儿戏水池（水深30cm）。",
        "suitable_age": "3-12岁", "min_height": 0.80, "intensity": "medium",
        "is_indoor": False, "has_ac": False, "stroller_friendly": False,
        "duration_minutes": 60, "capacity": 300, "fast_pass": False, "queue_enabled": True,
        "cover_image": "/images/projects/water_park.jpg",
        "location_desc": "水上乐园区",
        "tips": "需穿泳衣入场，建议自带泳衣。提供免费更衣室和收费储物柜。建议携带防晒霜和浴巾。",
        "safety_notes": "婴幼儿必须穿戴防水纸尿裤+救生衣。3-6岁儿童须家长全程陪同。当前状态：维护中，暂停开放。",
        "status": "maintenance", "sort_order": 14,
    },
    # P015 鸟语林
    {
        "project_code": "P015", "name": "鸟语林", "zone": "科普区",
        "category": "venue",
        "description": "大型鸟网保护区内漫步体验区，可观赏鹦鹉、孔雀、火烈鸟、天鹅等20多种鸟类。游客可购买鸟食（5元/份）喂鹦鹉，运气好还能看到孔雀开屏。",
        "suitable_age": "全年龄", "min_height": None, "intensity": "low",
        "is_indoor": False, "has_ac": False, "stroller_friendly": True,
        "duration_minutes": 30, "capacity": 150, "fast_pass": False, "queue_enabled": False,
        "cover_image": "/images/projects/bird_forest.jpg",
        "location_desc": "科普区东侧",
        "tips": "有遮阳棚步道，避免暴晒。鸟食售卖5元/份，性价比高。接触鸟类后请洗手（提供洗手池）。孔雀开屏一般在晴天上午9:00-11:00。",
        "safety_notes": "不追赶、惊吓、拉扯鸟类。",
        "status": "open", "sort_order": 15,
    },
]

# ---------- 设施数据 ----------
FACILITIES = [
    # ---- 母婴室 5 个 ----
    {"name": "梦幻城堡区母婴室", "type": "nursing", "zone": "梦幻城堡区",
     "location_desc": "旋转木马旁，步行约3分钟", "open_time": "09:00", "close_time": "18:00",
     "features": ["哺乳隔间", "换尿布台", "热水", "微波炉", "婴儿床"], "status": "open"},
    {"name": "海洋探险区母婴室", "type": "nursing", "zone": "海洋探险区",
     "location_desc": "海洋餐厅旁，步行约2分钟", "open_time": "09:00", "close_time": "18:00",
     "features": ["哺乳隔间", "换尿布台", "热水", "微波炉"], "status": "open"},
    {"name": "欢乐农场区母婴室", "type": "nursing", "zone": "欢乐农场区",
     "location_desc": "动物互动区出口处", "open_time": "09:00", "close_time": "18:00",
     "features": ["哺乳隔间", "换尿布台", "热水", "婴儿秤"], "status": "open"},
    {"name": "科普区母婴室", "type": "nursing", "zone": "科普区",
     "location_desc": "恐龙科普馆入口旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["哺乳隔间", "换尿布台", "热水", "温奶器"], "status": "open"},
    {"name": "冒险区母婴室", "type": "nursing", "zone": "冒险区",
     "location_desc": "碰碰车乐园旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["哺乳隔间", "换尿布台", "热水"], "status": "open"},
    # ---- 主题餐厅 4 家 ----
    {"name": "海洋主题餐厅", "type": "restaurant", "zone": "海洋探险区",
     "location_desc": "海底隧道出口旁", "open_time": "10:00", "close_time": "18:00",
     "features": ["儿童套餐38元", "宝宝椅", "辅食加热", "鲜榨果汁"],
     "price_info": "人均60-80元", "status": "open"},
    {"name": "城堡主题餐厅", "type": "restaurant", "zone": "梦幻城堡区",
     "location_desc": "摩天轮下方", "open_time": "10:00", "close_time": "18:00",
     "features": ["儿童套餐35元", "宝宝椅", "辅食加热", "披萨意面"],
     "price_info": "人均50-70元", "status": "open"},
    {"name": "农场主题餐厅", "type": "restaurant", "zone": "欢乐农场区",
     "location_desc": "小火车终点旁", "open_time": "10:00", "close_time": "18:00",
     "features": ["儿童套餐30元", "宝宝椅", "辅食加热", "营养粥炖汤"],
     "price_info": "人均40-60元", "status": "open"},
    {"name": "科普主题餐厅", "type": "restaurant", "zone": "科普区",
     "location_desc": "恐龙科普馆旁", "open_time": "10:00", "close_time": "18:00",
     "features": ["儿童套餐28元", "轻食沙拉", "酸奶水果杯"],
     "price_info": "人均30-50元", "status": "open"},
    # ---- 小吃站 8 个 ----
    {"name": "梦幻热狗", "type": "snack", "zone": "梦幻城堡区",
     "location_desc": "旋转木马旁", "open_time": "09:30", "close_time": "18:00",
     "features": ["热狗", "烤肠", "爆米花"], "price_info": "¥10-25", "status": "open"},
    {"name": "海洋冰淇淋", "type": "snack", "zone": "海洋探险区",
     "location_desc": "海底隧道出口", "open_time": "09:30", "close_time": "18:00",
     "features": ["冰淇淋", "冰沙", "奶昔"], "price_info": "¥15-30", "status": "open"},
    {"name": "农场水饺", "type": "snack", "zone": "欢乐农场区",
     "location_desc": "动物互动区旁", "open_time": "09:30", "close_time": "18:00",
     "features": ["手工水饺", "馄饨", "蒸包"], "price_info": "¥15-25", "status": "open"},
    {"name": "科普果汁站", "type": "snack", "zone": "科普区",
     "location_desc": "恐龙科普馆入口", "open_time": "09:30", "close_time": "18:00",
     "features": ["鲜榨果汁", "水果杯", "酸奶"], "price_info": "¥12-25", "status": "open"},
    {"name": "城堡烤串", "type": "snack", "zone": "梦幻城堡区",
     "location_desc": "摩天轮下方", "open_time": "10:00", "close_time": "18:00",
     "features": ["鸡肉串", "牛肉串", "烤玉米"], "price_info": "¥10-20", "status": "open"},
    {"name": "冒险爆米花", "type": "snack", "zone": "冒险区",
     "location_desc": "过山车旁", "open_time": "09:30", "close_time": "18:00",
     "features": ["爆米花", "棉花糖"], "price_info": "¥10-15", "status": "open"},
    {"name": "水上小吃", "type": "snack", "zone": "水上乐园区",
     "location_desc": "水上乐园入口", "open_time": "10:00", "close_time": "17:00",
     "features": ["煎饺", "鱼丸", "关东煮"], "price_info": "¥10-20", "status": "closed"},
    {"name": "中央广场甜品站", "type": "snack", "zone": "中央广场",
     "location_desc": "中央广场东侧", "open_time": "09:30", "close_time": "18:00",
     "features": ["甜甜圈", "马卡龙", "咖啡"], "price_info": "¥10-30", "status": "open"},
    # ---- 卫生间 6 处 ----
    {"name": "梦幻城堡区卫生间", "type": "restroom", "zone": "梦幻城堡区",
     "location_desc": "旋转木马旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["家庭卫生间", "儿童便池", "无障碍"], "status": "open"},
    {"name": "海洋探险区卫生间", "type": "restroom", "zone": "海洋探险区",
     "location_desc": "海洋餐厅旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["家庭卫生间", "婴儿护理台"], "status": "open"},
    {"name": "欢乐农场区卫生间", "type": "restroom", "zone": "欢乐农场区",
     "location_desc": "动物互动区旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["儿童专用小便池", "儿童洗手池"], "status": "open"},
    {"name": "冒险区卫生间", "type": "restroom", "zone": "冒险区",
     "location_desc": "碰碰车乐园旁", "open_time": "09:00", "close_time": "18:00",
     "features": ["家庭卫生间"], "status": "open"},
    {"name": "科普区卫生间", "type": "restroom", "zone": "科普区",
     "location_desc": "恐龙科普馆内", "open_time": "09:00", "close_time": "18:00",
     "features": ["家庭卫生间", "婴儿护理台"], "status": "open"},
    {"name": "中央广场卫生间", "type": "restroom", "zone": "中央广场",
     "location_desc": "中央广场东侧", "open_time": "09:00", "close_time": "18:00",
     "features": ["母婴卫生间", "哺乳位"], "status": "open"},
    # ---- 其他设施 ----
    {"name": "园区医务室", "type": "medical", "zone": "梦幻城堡区",
     "location_desc": "旋转木马旁（靠近西门）", "open_time": "09:00", "close_time": "18:00",
     "features": ["急救处理", "常用药品", "轻微外伤包扎"],
     "contact_phone": "400-888-6666", "status": "open"},
    {"name": "信息服务中心", "type": "info", "zone": "正门入口",
     "location_desc": "园区正门入口处", "open_time": "08:30", "close_time": "18:30",
     "features": ["园区地图", "项目咨询", "寻人寻物", "投诉建议", "轮椅租赁"],
     "contact_phone": "400-888-6666", "status": "open"},
    {"name": "正门储物柜", "type": "locker", "zone": "正门入口",
     "location_desc": "正门入口处", "open_time": "07:30", "close_time": "20:00",
     "features": ["小柜10元/次", "大柜20元/次", "扫码支付"],
     "price_info": "小柜¥10/次，大柜¥20/次", "status": "open"},
    {"name": "西门储物柜", "type": "locker", "zone": "西门入口",
     "location_desc": "西门入口处", "open_time": "07:30", "close_time": "20:00",
     "features": ["小柜10元/次", "大柜20元/次", "扫码支付"],
     "price_info": "小柜¥10/次，大柜¥20/次", "status": "open"},
    {"name": "正门婴儿车租赁", "type": "stroller", "zone": "正门入口",
     "location_desc": "正门入口处", "open_time": "08:30", "close_time": "18:00",
     "features": ["免费租赁", "押金200元", "限重20kg", "可折叠伞车"],
     "price_info": "免费（押金¥200）", "status": "open"},
    {"name": "东门婴儿车租赁", "type": "stroller", "zone": "东门入口",
     "location_desc": "东门入口处", "open_time": "08:30", "close_time": "18:00",
     "features": ["免费租赁", "押金200元", "限重20kg"],
     "price_info": "免费（押金¥200）", "status": "open"},
    {"name": "正门充电宝租借", "type": "charging", "zone": "正门入口",
     "location_desc": "信息服务中心", "open_time": "08:30", "close_time": "18:30",
     "features": ["3元/小时", "封顶20元/天", "全园通借通还"],
     "price_info": "¥3/小时，封顶¥20/天", "status": "open"},
    {"name": "正门停车场", "type": "parking", "zone": "正门外",
     "location_desc": "园区正门外", "open_time": "07:30", "close_time": "20:00",
     "features": ["免费停车", "2000个车位"],
     "price_info": "免费", "status": "open"},
]

# ---------- 安全规则（10 条） ----------
SAFETY_RULES = [
    {"rule_code": "SR001", "project_type": "ride", "age_group": "0-3", "weather": None,
     "priority": "high",
     "rule_content": "0-3岁婴幼儿仅限乘坐旋转木马、小火车等低强度设施。必须有家长陪同。禁止乘坐过山车、碰碰车等刺激项目。"},
    {"rule_code": "SR002", "project_type": "water", "age_group": "0-3", "weather": None,
     "priority": "high",
     "rule_content": "0-3岁婴幼儿玩水必须穿戴防水纸尿裤+救生衣，家长全程手扶，单次玩水不超过15分钟，出水后立即擦干包裹保暖。水温需≥32°C。"},
    {"rule_code": "SR003", "project_type": "water", "age_group": "3-6", "weather": None,
     "priority": "high",
     "rule_content": "3-6岁儿童必须穿戴救生衣，家长全程陪同，不得进入水深>50cm区域，每30分钟上岸休息10分钟，及时补充水分。"},
    {"rule_code": "SR004", "project_type": "all", "age_group": "all", "weather": "高温",
     "priority": "high",
     "rule_content": "高温天(>35°C)避开11:00-15:00户外时段。每30分钟补水一次。涂抹SPF50+防晒霜。佩戴遮阳帽。穿着浅色透气衣物。中暑征兆（头晕、脸红、大量出汗后停止出汗、恶心）→立即到阴凉处休息补水。"},
    {"rule_code": "SR005", "project_type": "all", "age_group": "all", "weather": "雨天",
     "priority": "high",
     "rule_content": "雨天远离高大树木和金属设施（防雷击）。注意路面防滑，放慢脚步抱好小宝宝。雷暴时就近进入室内场馆躲避。避免接触户外电器设备。使用雨伞或雨衣（园区商店有售¥15/件）。"},
    {"rule_code": "SR006", "project_type": "animal", "age_group": "0-3", "weather": None,
     "priority": "high",
     "rule_content": "0-3岁接触动物时家长必须扶着宝宝的手，仅限触摸兔子、小羊等温顺小动物，禁止自行喂食（可由家长代喂展示），接触后立即洗手消毒。"},
    {"rule_code": "SR007", "project_type": "animal", "age_group": "3-6", "weather": None,
     "priority": "medium",
     "rule_content": "3-6岁在家长陪同下可喂食指定动物，使用园区提供的专用喂食工具（夹子或长勺），不得用手指直接喂食，只在指定区域喂食，接触后洗手消毒。"},
    {"rule_code": "SR008", "project_type": "show", "age_group": "all", "weather": None,
     "priority": "medium",
     "rule_content": "提前15分钟入场就座。演出期间不要站立在过道上。关闭闪光灯避免影响演员和动物。控制音量不要大声喧哗。宝宝哭闹请暂时离场安抚后再返回。魔术秀含惊吓元素，胆小宝宝家长请评估。"},
    {"rule_code": "SR009", "project_type": "ride", "age_group": "6-12", "weather": None,
     "priority": "high",
     "rule_content": "过山车身高不足1.2m严禁乘坐。心脏病/高血压/癫痫/孕妇/近期手术者禁止乘坐。乘坐前取下眼镜、手机、硬币等松散物品。全程保持坐姿双手抓紧扶手。如感严重不适向工作人员示意停车。"},
    {"rule_code": "SR010", "project_type": "all", "age_group": "all", "weather": None,
     "priority": "high",
     "rule_content": "家长全程看护，不要让孩子离开视线。体验受限项目前务必测量身高。身体不适立即停止游玩前往医务室。紧急情况保持冷静按工作人员指引疏散。孩子走失：原地等待5分钟→联系工作人员→信息台广播寻人。"},
]

# ---------- 票种（6 种） ----------
TICKET_TYPES = [
    {"name": "成人票", "code": "ADULT", "category": "adult",
     "price": 120.00, "discount_price": 108.00, "description": "身高≥1.5m",
     "valid_days": 1, "usage_limit": 1},
    {"name": "儿童票", "code": "CHILD", "category": "child",
     "price": 80.00, "discount_price": 72.00, "description": "身高0.8m-1.5m",
     "valid_days": 1, "usage_limit": 1},
    {"name": "免票", "code": "FREE", "category": "child",
     "price": 0, "discount_price": 0, "description": "身高<0.8m或年龄<1周岁（凭有效证件）",
     "valid_days": 1, "usage_limit": 1},
    {"name": "家庭套票(2大1小)", "code": "FAMILY_2A1C", "category": "family",
     "price": 280.00, "discount_price": 258.00, "description": "含2位成人+1位儿童",
     "includes": ["成人票×2", "儿童票×1"], "valid_days": 1, "usage_limit": 1},
    {"name": "家庭套票(2大2小)", "code": "FAMILY_2A2C", "category": "family",
     "price": 340.00, "discount_price": 318.00, "description": "含2位成人+2位儿童",
     "includes": ["成人票×2", "儿童票×2"], "valid_days": 1, "usage_limit": 1},
    {"name": "长者票", "code": "SENIOR", "category": "senior",
     "price": 60.00, "discount_price": 54.00, "description": "60岁以上凭有效证件",
     "valid_days": 1, "usage_limit": 1},
]

# ---------- 活动排期（当日示例） ----------
def make_schedules(target_date: date) -> list:
    """根据目标日期生成当天活动排期"""
    pid = lambda code: code  # 用 project_code 关联，后面查询替换
    return [
        {"project_code": "P007", "event_name": "海洋动物表演（上午场·海豚专场）", "event_type": "show",
         "event_date": target_date, "start_time": "10:30", "end_time": "11:00",
         "location": "海洋剧场", "capacity": 800, "theme": "海豚表演专场",
         "description": "海豚高空跳跃、球类杂技、人豚共舞", "status": "normal"},
        {"project_code": "P007", "event_name": "海洋动物表演（下午场·海狮互动）", "event_type": "show",
         "event_date": target_date, "start_time": "14:00", "end_time": "14:30",
         "location": "海洋剧场", "capacity": 800, "theme": "海狮互动专场",
         "description": "海狮鼓掌、投篮、套圈、模仿秀", "status": "normal"},
        {"project_code": "P007", "event_name": "海洋动物表演（傍晚场·综合表演）", "event_type": "show",
         "event_date": target_date, "start_time": "16:00", "end_time": "16:30",
         "location": "海洋剧场", "capacity": 800, "theme": "综合表演场",
         "description": "海豚海狮联合演出", "status": "normal"},
        {"project_code": "P011", "event_name": "小丑互动秀（上午场）", "event_type": "show",
         "event_date": target_date, "start_time": "10:30", "end_time": "10:50",
         "location": "中央广场", "capacity": 300, "theme": "上午互动秀",
         "description": "魔术+气球造型+互动游戏", "status": "normal"},
        {"project_code": "P011", "event_name": "小丑互动秀（下午场）", "event_type": "show",
         "event_date": target_date, "start_time": "14:00", "end_time": "14:20",
         "location": "中央广场", "capacity": 300, "theme": "下午互动秀",
         "description": "魔术+气球造型+互动游戏", "status": "normal"},
        {"project_code": "P011", "event_name": "小丑互动秀（傍晚场）", "event_type": "show",
         "event_date": target_date, "start_time": "16:30", "end_time": "16:50",
         "location": "中央广场", "capacity": 300, "theme": "傍晚互动秀",
         "description": "魔术+气球造型+互动游戏", "status": "normal"},
        {"project_code": "P012", "event_name": "魔术秀（上午场）", "event_type": "show",
         "event_date": target_date, "start_time": "11:00", "end_time": "11:25",
         "location": "梦幻剧场", "capacity": 400, "theme": "上午魔术秀",
         "description": "大变活人、悬浮术、鸽子魔术", "status": "normal"},
        {"project_code": "P012", "event_name": "魔术秀（下午场）", "event_type": "show",
         "event_date": target_date, "start_time": "15:00", "end_time": "15:25",
         "location": "梦幻剧场", "capacity": 400, "theme": "下午魔术秀",
         "description": "火焰魔术、互动魔术", "status": "normal"},
        {"project_code": "P012", "event_name": "魔术秀（傍晚场）", "event_type": "show",
         "event_date": target_date, "start_time": "17:00", "end_time": "17:25",
         "location": "梦幻剧场", "capacity": 400, "theme": "傍晚魔术秀",
         "description": "综合魔术表演", "status": "normal"},
        {"project_code": "P010", "event_name": "花车巡游", "event_type": "parade",
         "event_date": target_date, "start_time": "16:30", "end_time": "16:55",
         "location": "主干道全程", "capacity": 0, "theme": "主题花车巡游",
         "description": "6辆主题花车+卡通人偶方队+舞蹈表演", "status": "normal"},
    ]

# ============================================================
#  执行初始化
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:123456@localhost:3306/lele_park")
ADMIN_PHONE = "13800000000"
ADMIN_PASSWORD = "Admin@123"


async def init_all():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据表创建完成")

    async with async_session() as session:
        # ---------- 1. 管理员账号 ----------
        import hashlib, os
        def _hash_pw(pw):
            salt = os.urandom(16).hex()
            h = hashlib.sha256((salt + pw).encode()).hexdigest()
            return f"{salt}${h}"

        existing = await session.execute(
            __import__("sqlalchemy").select(User).where(User.phone == ADMIN_PHONE)
        )
        if existing.scalar_one_or_none():
            print("⏭️  管理员账号已存在，跳过")
        else:
            admin = User(
                phone=ADMIN_PHONE,
                nickname="系统管理员",
                password_hash=_hash_pw(ADMIN_PASSWORD),
                role="admin", status="active",
            )
            session.add(admin)
            await session.flush()
            session.add(UserProfile(
                user_id=admin.id, child_age="5岁",
                interests=["科普", "动物"],
            ))
            print(f"✅ 管理员创建成功: {ADMIN_PHONE} / {ADMIN_PASSWORD}")

        # ---------- 2. 项目数据 ----------
        for p in PROJECTS:
            session.add(Project(**p))
        print(f"✅ 项目数据: {len(PROJECTS)} 个")

        # ---------- 3. 设施数据 ----------
        for f in FACILITIES:
            session.add(Facility(**f))
        print(f"✅ 设施数据: {len(FACILITIES)} 个")

        # ---------- 4. 安全规则 ----------
        for r in SAFETY_RULES:
            session.add(SafetyRule(**r))
        print(f"✅ 安全规则: {len(SAFETY_RULES)} 条")

        # ---------- 5. 票种 ----------
        for t in TICKET_TYPES:
            session.add(TicketType(**t))
        print(f"✅ 票种数据: {len(TICKET_TYPES)} 种")

        await session.commit()

        # ---------- 6. 活动排期（今天 + 明天） ----------
        # 先查询 project_code → id 映射
        result = await session.execute(__import__("sqlalchemy").select(Project.project_code, Project.id))
        code_to_id = {row[0]: row[1] for row in result.all()}

        today = date.today()
        for delta in range(2):  # 今天和明天
            target = today + __import__("datetime").timedelta(days=delta)
            for s in make_schedules(target):
                pid = code_to_id.get(s.pop("project_code"))
                if pid:
                    session.add(Schedule(project_id=pid, **s))

        await session.commit()
        print(f"✅ 活动排期: {len(make_schedules(today)) * 2} 场（今天+明天）")

    await engine.dispose()

    print()
    print("=" * 50)
    print("  🎉 数据初始化全部完成！")
    print("=" * 50)
    print(f"  管理员: {ADMIN_PHONE} / {ADMIN_PASSWORD}")
    print(f"  项目:   {len(PROJECTS)} 个")
    print(f"  设施:   {len(FACILITIES)} 个")
    print(f"  安全规则: {len(SAFETY_RULES)} 条")
    print(f"  票种:   {len(TICKET_TYPES)} 种")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(init_all())
