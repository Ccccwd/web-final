from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # 开发环境下打印SQL语句
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,   # 连接回收时间（秒）
    max_overflow=20,     # 最大溢出连接数
    pool_size=20         # 连接池大小
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    """
    获取数据库会话的依赖注入函数
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_tables():
    """创建所有表"""
    # 导入所有模型以确保它们被注册
    from app.models import user, category, transaction, account, budget, reminder, statistics
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """删除所有表（仅用于测试）"""
    # 导入所有模型以确保它们被注册
    from app.models import user, category, transaction, account, budget, reminder, statistics
    Base.metadata.drop_all(bind=engine)

def init_database():
    """初始化数据库"""
    # 创建表
    create_tables()

    # 插入初始数据
    insert_default_data()

def insert_default_data():
    """插入默认数据"""
    from app.models.category import Category, CategoryType

    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_count = db.query(Category).filter(Category.is_system.is_(True)).count()
        if existing_count > 0:
            return

        # 插入系统预设分类
        categories = [
            # 支出分类
            {"name": "餐饮", "type": CategoryType.EXPENSE, "icon": "🍔", "color": "#FF6B6B", "is_system": True, "sort_order": 1},
            {"name": "交通", "type": CategoryType.EXPENSE, "icon": "🚇", "color": "#4ECDC4", "is_system": True, "sort_order": 2},
            {"name": "娱乐", "type": CategoryType.EXPENSE, "icon": "🎮", "color": "#45B7D1", "is_system": True, "sort_order": 3},
            {"name": "购物", "type": CategoryType.EXPENSE, "icon": "🛒", "color": "#96CEB4", "is_system": True, "sort_order": 4},
            {"name": "学习", "type": CategoryType.EXPENSE, "icon": "📚", "color": "#FFEAA7", "is_system": True, "sort_order": 5},
            {"name": "医疗", "type": CategoryType.EXPENSE, "icon": "🏥", "color": "#DFE6E9", "is_system": True, "sort_order": 6},
            {"name": "居住", "type": CategoryType.EXPENSE, "icon": "🏠", "color": "#74B9FF", "is_system": True, "sort_order": 7},
            {"name": "通讯", "type": CategoryType.EXPENSE, "icon": "📱", "color": "#A29BFE", "is_system": True, "sort_order": 8},
            {"name": "社交", "type": CategoryType.EXPENSE, "icon": "👥", "color": "#FD79A8", "is_system": True, "sort_order": 9},
            {"name": "美容", "type": CategoryType.EXPENSE, "icon": "💄", "color": "#FDCB6E", "is_system": True, "sort_order": 10},
            {"name": "运动", "type": CategoryType.EXPENSE, "icon": "🏃", "color": "#6C5CE7", "is_system": True, "sort_order": 11},
            {"name": "宠物", "type": CategoryType.EXPENSE, "icon": "🐕", "color": "#00B894", "is_system": True, "sort_order": 12},
            {"name": "其他", "type": CategoryType.EXPENSE, "icon": "📦", "color": "#636E72", "is_system": True, "sort_order": 13},

            # 收入分类
            {"name": "工资", "type": CategoryType.INCOME, "icon": "💰", "color": "#00B894", "is_system": True, "sort_order": 1},
            {"name": "奖金", "type": CategoryType.INCOME, "icon": "🎁", "color": "#00CEC9", "is_system": True, "sort_order": 2},
            {"name": "兼职", "type": CategoryType.INCOME, "icon": "💸", "color": "#0984E3", "is_system": True, "sort_order": 3},
            {"name": "投资收益", "type": CategoryType.INCOME, "icon": "📈", "color": "#6C5CE7", "is_system": True, "sort_order": 4},
            {"name": "红包", "type": CategoryType.INCOME, "icon": "🧧", "color": "#E17055", "is_system": True, "sort_order": 5},
            {"name": "退款", "type": CategoryType.INCOME, "icon": "💳", "color": "#FDCB6E", "is_system": True, "sort_order": 6},
            {"name": "其他", "type": CategoryType.INCOME, "icon": "📦", "color": "#636E72", "is_system": True, "sort_order": 7},
        ]

        for cat_data in categories:
            category = Category(**cat_data)
            db.add(category)

        db.commit()

        # 插入二级分类（餐饮子分类）
        food_category = db.query(Category).filter(Category.name == "餐饮").first()
        if food_category:
            subcategories = [
                {"name": "早餐", "icon": "☕", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 1},
                {"name": "午餐", "icon": "🍱", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 2},
                {"name": "晚餐", "icon": "🍽️", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 3},
                {"name": "夜宵", "icon": "🌙", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 4},
                {"name": "零食", "icon": "🍿", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 5},
                {"name": "饮料", "icon": "🥤", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 6},
                {"name": "聚餐", "icon": "🍻", "color": "#FF6B6B", "parent_id": food_category.id, "is_system": True, "sort_order": 7},
            ]

            for sub_cat_data in subcategories:
                subcategory = Category(**sub_cat_data)
                db.add(subcategory)

            db.commit()

        # 插入二级分类（交通子分类）
        traffic_category = db.query(Category).filter(Category.name == "交通").first()
        if traffic_category:
            subcategories = [
                {"name": "地铁", "icon": "🚇", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 1},
                {"name": "公交", "icon": "🚌", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 2},
                {"name": "打车", "icon": "🚕", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 3},
                {"name": "加油", "icon": "⛽", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 4},
                {"name": "停车", "icon": "🅿️", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 5},
                {"name": "高速", "icon": "🛣️", "color": "#4ECDC4", "parent_id": traffic_category.id, "is_system": True, "sort_order": 6},
            ]

            for sub_cat_data in subcategories:
                subcategory = Category(**sub_cat_data)
                db.add(subcategory)

            db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()