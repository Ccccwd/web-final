from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
from decimal import Decimal

from app.models.category import Category, CategoryType
from app.models.transaction import Transaction, TransactionType
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryWithStats
from app.core.exceptions import ValidationError, NotFoundError

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, user_id: int, category_data: CategoryCreate) -> Category:
        """
        创建分类

        Args:
            user_id: 用户ID
            category_data: 分类数据

        Returns:
            创建的分类
        """
        # 检查分类名称是否已存在
        existing_category = self.db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == category_data.name,
            Category.type == category_data.type
        ).first()

        if existing_category:
            raise ValidationError("相同类型的分类名称已存在")

        # 如果设置了父分类，验证父分类存在且属于同一用户
        if category_data.parent_id:
            parent_category = self.db.query(Category).filter(
                Category.id == category_data.parent_id,
                Category.user_id == user_id
            ).first()
            if not parent_category:
                raise ValidationError("父分类不存在或无权访问")

        # 创建分类
        category = Category(
            user_id=user_id,
            **category_data.model_dump()
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return category

    def get_category(self, user_id: int, category_id: int) -> Category:
        """
        获取分类详情

        Args:
            user_id: 用户ID
            category_id: 分类ID

        Returns:
            分类信息
        """
        category = self.db.query(Category).filter(
            Category.id == category_id,
            and_(
                or_(Category.user_id == user_id, Category.is_system == True)
            )
        ).first()

        if not category:
            raise NotFoundError("分类不存在")

        return category

    def get_categories(
        self,
        user_id: int,
        category_type: Optional[CategoryType] = None,
        include_system: bool = True,
        parent_id: Optional[int] = None
    ) -> List[Category]:
        """
        获取分类列表

        Args:
            user_id: 用户ID
            category_type: 分类类型
            include_system: 是否包含系统分类
            parent_id: 父分类ID

        Returns:
            分类列表
        """
        query = self.db.query(Category)

        # 用户分类或系统分类
        if include_system:
            query = query.filter(
                or_(Category.user_id == user_id, Category.is_system == True)
            )
        else:
            query = query.filter(Category.user_id == user_id)

        if category_type:
            query = query.filter(Category.type == category_type)

        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)

        # 按排序和名称排序
        categories = query.order_by(
            Category.sort_order.asc(),
            Category.name.asc()
        ).all()

        return categories

    def get_category_tree(
        self,
        user_id: int,
        category_type: Optional[CategoryType] = None,
        include_system: bool = True
    ) -> List[Category]:
        """
        获取分类树

        Args:
            user_id: 用户ID
            category_type: 分类类型
            include_system: 是否包含系统分类

        Returns:
            分类树列表
        """
        # 获取所有分类
        categories = self.get_categories(
            user_id=user_id,
            category_type=category_type,
            include_system=include_system
        )

        # 构建树形结构
        category_dict = {cat.id: cat for cat in categories}
        root_categories = []

        for category in categories:
            if category.parent_id and category.parent_id in category_dict:
                parent = category_dict[category.parent_id]
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(category)
            else:
                root_categories.append(category)

        return root_categories

    def update_category(
        self,
        user_id: int,
        category_id: int,
        category_data: CategoryUpdate
    ) -> Category:
        """
        更新分类

        Args:
            user_id: 用户ID
            category_id: 分类ID
            category_data: 更新数据

        Returns:
            更新后的分类
        """
        category = self.get_category(user_id, category_id)

        # 不能修改系统分类的核心信息
        if category.is_system:
            if category_data.type and category_data.type != category.type:
                raise ValidationError("不能修改系统分类的类型")

        # 检查名称是否与其他分类重复
        if category_data.name:
            existing_category = self.db.query(Category).filter(
                Category.id != category_id,
                Category.user_id == user_id,
                Category.name == category_data.name,
                Category.type == (category_data.type or category.type)
            ).first()

            if existing_category:
                raise ValidationError("相同类型的分类名称已存在")

        # 更新字段
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)

        return category

    def delete_category(self, user_id: int, category_id: int) -> bool:
        """
        删除分类

        Args:
            user_id: 用户ID
            category_id: 分类ID

        Returns:
            是否删除成功
        """
        category = self.get_category(user_id, category_id)

        # 不能删除系统分类
        if category.is_system:
            raise ValidationError("不能删除系统分类")

        # 检查是否有子分类
        child_categories = self.db.query(Category).filter(
            Category.parent_id == category_id
        ).count()

        if child_categories > 0:
            raise ValidationError("存在子分类，不能删除")

        # 检查是否有关联的交易
        transaction_count = self.db.query(Transaction).filter(
            Transaction.category_id == category_id
        ).count()

        if transaction_count > 0:
            raise ValidationError("存在关联交易，不能删除")

        self.db.delete(category)
        self.db.commit()

        return True

    def get_category_with_stats(self, user_id: int, category_id: int) -> CategoryWithStats:
        """
        获取带统计信息的分类

        Args:
            user_id: 用户ID
            category_id: 分类ID

        Returns:
            带统计信息的分类
        """
        category = self.get_category(user_id, category_id)

        # 统计交易信息
        expense_stats = self.db.query(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.category_id == category_id,
            Transaction.type == TransactionType.EXPENSE
        ).first()

        income_stats = self.db.query(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.category_id == category_id,
            Transaction.type == TransactionType.INCOME
        ).first()

        # 构建响应数据
        category_dict = {
            "id": category.id,
            "user_id": category.user_id,
            "name": category.name,
            "type": category.type,
            "icon": category.icon,
            "color": category.color,
            "parent_id": category.parent_id,
            "sort_order": category.sort_order,
            "is_system": category.is_system,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "expense_count": expense_stats.count if expense_stats else 0,
            "expense_amount": float(expense_stats.total) if expense_stats and expense_stats.total else 0,
            "income_count": income_stats.count if income_stats else 0,
            "income_amount": float(income_stats.total) if income_stats and income_stats.total else 0,
        }

        return CategoryWithStats(**category_dict)

    def get_categories_with_usage_stats(
        self,
        user_id: int,
        category_type: Optional[CategoryType] = None,
        limit: int = 10
    ) -> List[CategoryWithStats]:
        """
        获取带使用统计的分类列表

        Args:
            user_id: 用户ID
            category_type: 分类类型
            limit: 返回数量限制

        Returns:
            带统计信息的分类列表
        """
        categories = self.get_categories(user_id, category_type)

        categories_with_stats = []
        for category in categories:
            stats = self.get_category_with_stats(user_id, category.id)
            categories_with_stats.append(stats)

        # 按使用频率排序
        categories_with_stats.sort(
            key=lambda x: (x.expense_count + x.income_count),
            reverse=True
        )

        return categories_with_stats[:limit]

    def init_system_categories(self, user_id: int) -> List[Category]:
        """
        初始化系统分类

        Args:
            user_id: 用户ID

        Returns:
            创建的系统分类列表
        """
        # 系统预设分类
        system_categories = [
            # 支出分类
            {"name": "餐饮", "type": CategoryType.EXPENSE, "icon": "🍔", "color": "#FF6B6B"},
            {"name": "交通", "type": CategoryType.EXPENSE, "icon": "🚗", "color": "#4ECDC4"},
            {"name": "购物", "type": CategoryType.EXPENSE, "icon": "🛍️", "color": "#FFB6C1"},
            {"name": "娱乐", "type": CategoryType.EXPENSE, "icon": "🎮", "color": "#98D8C8"},
            {"name": "医疗", "type": CategoryType.EXPENSE, "icon": "🏥", "color": "#F7DC6F"},
            {"name": "教育", "type": CategoryType.EXPENSE, "icon": "📚", "color": "#85C1E9"},
            {"name": "居住", "type": CategoryType.EXPENSE, "icon": "🏠", "color": "#D5A6BD"},
            {"name": "通讯", "type": CategoryType.EXPENSE, "icon": "📱", "color": "#A9DFBF"},
            {"name": "人情往来", "type": CategoryType.EXPENSE, "icon": "🎁", "color": "#F8B739"},
            {"name": "其他支出", "type": CategoryType.EXPENSE, "icon": "💸", "color": "#BDC3C7"},

            # 收入分类
            {"name": "工资", "type": CategoryType.INCOME, "icon": "💰", "color": "#52C41A"},
            {"name": "奖金", "type": CategoryType.INCOME, "icon": "🎉", "color": "#FF4D4F"},
            {"name": "投资收益", "type": CategoryType.INCOME, "icon": "📈", "color": "#1890FF"},
            {"name": "兼职", "type": CategoryType.INCOME, "icon": "💼", "color": "#722ED1"},
            {"name": "礼金", "type": CategoryType.INCOME, "icon": "🧧", "color": "#FA8C16"},
            {"name": "退款", "type": CategoryType.INCOME, "icon": "↩️", "color": "#13C2C2"},
            {"name": "其他收入", "type": CategoryType.INCOME, "icon": "💵", "color": "#BDC3C7"},
        ]

        created_categories = []
        for cat_data in system_categories:
            # 检查是否已存在
            existing = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.name == cat_data["name"],
                Category.type == cat_data["type"]
            ).first()

            if not existing:
                category = Category(
                    user_id=user_id,
                    is_system=True,
                    **cat_data
                )
                self.db.add(category)
                created_categories.append(category)

        if created_categories:
            self.db.commit()
            for category in created_categories:
                self.db.refresh(category)

        return created_categories