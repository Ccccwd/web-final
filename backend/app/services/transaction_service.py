from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.models.category import Category
from app.models.account import Account
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionFilter,
    TransactionSummary
)
from app.core.exceptions import ValidationError, NotFoundError

class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, user_id: int, transaction_data: TransactionCreate) -> Transaction:
        """
        创建交易记录

        Args:
            user_id: 用户ID
            transaction_data: 交易数据

        Returns:
            创建的交易记录
        """
        # 验证分类和账户是否存在且属于当前用户
        category = self.db.query(Category).filter(
            Category.id == transaction_data.category_id,
            Category.user_id == user_id
        ).first()
        if not category:
            raise ValidationError("分类不存在或无权访问")

        account = self.db.query(Account).filter(
            Account.id == transaction_data.account_id,
            Account.user_id == user_id
        ).first()
        if not account:
            raise ValidationError("账户不存在或无权访问")

        # 如果是转账，验证目标账户
        if transaction_data.type == TransactionType.TRANSFER:
            if not transaction_data.to_account_id:
                raise ValidationError("转账交易必须指定目标账户")

            to_account = self.db.query(Account).filter(
                Account.id == transaction_data.to_account_id,
                Account.user_id == user_id
            ).first()
            if not to_account:
                raise ValidationError("目标账户不存在或无权访问")

        # 检查微信交易ID是否重复（如果是微信导入）
        if transaction_data.wechat_transaction_id:
            existing_transaction = self.db.query(Transaction).filter(
                Transaction.wechat_transaction_id == transaction_data.wechat_transaction_id
            ).first()
            if existing_transaction:
                raise ValidationError("微信交易ID已存在，可能重复导入")

        # 创建交易记录
        transaction = Transaction(
            user_id=user_id,
            **transaction_data.model_dump(exclude_unset=True)
        )

        self.db.add(transaction)

        # 更新账户余额（这里简化处理，实际应该在交易服务中处理余额变化）
        # self._update_account_balance(account, transaction_data.type, transaction_data.amount)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_transaction(self, user_id: int, transaction_id: int) -> Transaction:
        """
        获取交易记录详情

        Args:
            user_id: 用户ID
            transaction_id: 交易ID

        Returns:
            交易记录
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not transaction:
            raise NotFoundError("交易记录不存在")

        return transaction

    def get_transactions(
        self,
        user_id: int,
        filter: Optional[TransactionFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Transaction], int]:
        """
        获取交易记录列表

        Args:
            user_id: 用户ID
            filter: 筛选条件
            page: 页码
            page_size: 每页数量

        Returns:
            交易记录列表和总数量
        """
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        # 应用筛选条件
        if filter:
            if filter.type:
                query = query.filter(Transaction.type == filter.type)

            if filter.category_id:
                query = query.filter(Transaction.category_id == filter.category_id)

            if filter.account_id:
                query = query.filter(
                    or_(
                        Transaction.account_id == filter.account_id,
                        Transaction.to_account_id == filter.account_id
                    )
                )

            if filter.start_date:
                query = query.filter(Transaction.transaction_date >= filter.start_date)

            if filter.end_date:
                query = query.filter(Transaction.transaction_date <= filter.end_date)

            if filter.keyword:
                keyword = f"%{filter.keyword}%"
                query = query.filter(
                    or_(
                        Transaction.remark.ilike(keyword),
                        Transaction.merchant_name.ilike(keyword),
                        Transaction.tags.ilike(keyword)
                    )
                )

            if filter.min_amount:
                query = query.filter(Transaction.amount >= filter.min_amount)

            if filter.max_amount:
                query = query.filter(Transaction.amount <= filter.max_amount)

            if filter.source:
                query = query.filter(Transaction.source == filter.source)

            if filter.is_repeated is not None:
                query = query.filter(Transaction.is_repeated == filter.is_repeated)

        # 获取总数量
        total = query.count()

        # 分页和排序
        transactions = query.order_by(desc(Transaction.transaction_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return transactions, total

    def update_transaction(
        self,
        user_id: int,
        transaction_id: int,
        transaction_data: TransactionUpdate
    ) -> Transaction:
        """
        更新交易记录

        Args:
            user_id: 用户ID
            transaction_id: 交易ID
            transaction_data: 更新数据

        Returns:
            更新后的交易记录
        """
        transaction = self.get_transaction(user_id, transaction_id)

        # 验证分类和账户（如果更新了这些字段）
        update_data = transaction_data.model_dump(exclude_unset=True)

        if 'category_id' in update_data:
            category = self.db.query(Category).filter(
                Category.id == update_data['category_id'],
                Category.user_id == user_id
            ).first()
            if not category:
                raise ValidationError("分类不存在或无权访问")

        if 'account_id' in update_data:
            account = self.db.query(Account).filter(
                Account.id == update_data['account_id'],
                Account.user_id == user_id
            ).first()
            if not account:
                raise ValidationError("账户不存在或无权访问")

        # 更新字段
        for field, value in update_data.items():
            setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def delete_transaction(self, user_id: int, transaction_id: int) -> bool:
        """
        删除交易记录

        Args:
            user_id: 用户ID
            transaction_id: 交易ID

        Returns:
            是否删除成功
        """
        transaction = self.get_transaction(user_id, transaction_id)

        self.db.delete(transaction)
        self.db.commit()

        return True

    def get_transaction_summary(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TransactionSummary:
        """
        获取交易统计摘要

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易统计摘要
        """
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        # 统计各类交易总额
        income_sum = query.filter(
            Transaction.type == TransactionType.INCOME
        ).with_entities(func.sum(Transaction.amount)).scalar() or Decimal('0')

        expense_sum = query.filter(
            Transaction.type == TransactionType.EXPENSE
        ).with_entities(func.sum(Transaction.amount)).scalar() or Decimal('0')

        transfer_sum = query.filter(
            Transaction.type == TransactionType.TRANSFER
        ).with_entities(func.sum(Transaction.amount)).scalar() or Decimal('0')

        transaction_count = query.count()

        return TransactionSummary(
            total_income=income_sum,
            total_expense=expense_sum,
            total_transfer=transfer_sum,
            net_income=income_sum - expense_sum,
            transaction_count=transaction_count
        )

    def get_transactions_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """
        获取指定日期范围的交易记录

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            transaction_type: 交易类型

        Returns:
            交易记录列表
        """
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )

        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)

        return query.order_by(desc(Transaction.transaction_date)).all()

    def mark_as_repeated(self, transaction_id: int) -> Transaction:
        """
        标记交易为重复

        Args:
            transaction_id: 交易ID

        Returns:
            更新后的交易记录
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            raise NotFoundError("交易记录不存在")

        transaction.is_repeated = True
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def search_transactions(
        self,
        user_id: int,
        keyword: str,
        limit: int = 50
    ) -> List[Transaction]:
        """
        搜索交易记录

        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            limit: 结果数量限制

        Returns:
            交易记录列表
        """
        keyword = f"%{keyword}%"

        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            or_(
                Transaction.remark.ilike(keyword),
                Transaction.merchant_name.ilike(keyword),
                Transaction.original_category.ilike(keyword),
                Transaction.tags.ilike(keyword)
            )
        ).order_by(desc(Transaction.transaction_date)).limit(limit).all()

        return transactions