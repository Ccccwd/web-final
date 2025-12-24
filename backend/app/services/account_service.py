from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
from decimal import Decimal

from app.models.account import Account, AccountType
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.schemas.account import AccountCreate, AccountUpdate, AccountTransfer, AccountWithStats
from app.core.exceptions import ValidationError, NotFoundError
from app.services.account_balance_history_service import AccountBalanceHistoryService

class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, user_id: int, account_data: AccountCreate) -> Account:
        """
        创建账户

        Args:
            user_id: 用户ID
            account_data: 账户数据

        Returns:
            创建的账户
        """
        # 检查账户名称是否已存在
        existing_account = self.db.query(Account).filter(
            Account.user_id == user_id,
            Account.name == account_data.name
        ).first()

        if existing_account:
            raise ValidationError("账户名称已存在")

        # 如果设置为默认账户，取消其他默认账户
        if account_data.is_default:
            self.db.query(Account).filter(
                Account.user_id == user_id,
                Account.is_default == True
            ).update({"is_default": False})

        # 创建账户
        account = Account(
            user_id=user_id,
            balance=account_data.initial_balance,
            **account_data.model_dump(exclude={"is_default"})
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        # 记录初始余额历史
        if float(account.balance) > 0:
            balance_service = AccountBalanceHistoryService(self.db)
            try:
                balance_service.record_initial_balance(account.id)
            except Exception:
                # 如果记录历史失败，不影响账户创建
                pass

        return account

    def get_account(self, user_id: int, account_id: int) -> Account:
        """
        获取账户详情

        Args:
            user_id: 用户ID
            account_id: 账户ID

        Returns:
            账户信息
        """
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()

        if not account:
            raise NotFoundError("账户不存在")

        return account

    def get_accounts(
        self,
        user_id: int,
        account_type: Optional[AccountType] = None,
        is_enabled: Optional[bool] = None
    ) -> List[Account]:
        """
        获取账户列表

        Args:
            user_id: 用户ID
            account_type: 账户类型
            is_enabled: 是否启用

        Returns:
            账户列表
        """
        query = self.db.query(Account).filter(Account.user_id == user_id)

        if account_type:
            query = query.filter(Account.type == account_type)

        if is_enabled is not None:
            query = query.filter(Account.is_enabled == is_enabled)

        return query.order_by(
            Account.is_default.desc(),
            Account.name.asc()
        ).all()

    def update_account(
        self,
        user_id: int,
        account_id: int,
        account_data: AccountUpdate
    ) -> Account:
        """
        更新账户

        Args:
            user_id: 用户ID
            account_id: 账户ID
            account_data: 更新数据

        Returns:
            更新后的账户
        """
        account = self.get_account(user_id, account_id)

        # 检查名称是否与其他账户重复
        if account_data.name:
            existing_account = self.db.query(Account).filter(
                Account.id != account_id,
                Account.user_id == user_id,
                Account.name == account_data.name
            ).first()

            if existing_account:
                raise ValidationError("账户名称已存在")

        # 如果设置为默认账户，取消其他默认账户
        if account_data.is_default and not account.is_default:
            self.db.query(Account).filter(
                Account.user_id == user_id,
                Account.is_default == True
            ).update({"is_default": False})

        # 更新字段
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        self.db.commit()
        self.db.refresh(account)

        return account

    def delete_account(self, user_id: int, account_id: int) -> bool:
        """
        删除账户

        Args:
            user_id: 用户ID
            account_id: 账户ID

        Returns:
            是否删除成功
        """
        account = self.get_account(user_id, account_id)

        # 检查是否有关联的交易
        transaction_count = self.db.query(Transaction).filter(
            or_(
                Transaction.account_id == account_id,
                Transaction.to_account_id == account_id
            )
        ).count()

        if transaction_count > 0:
            raise ValidationError("存在关联交易，不能删除")

        self.db.delete(account)
        self.db.commit()

        return True

    def get_account_with_stats(self, user_id: int, account_id: int) -> AccountWithStats:
        """
        获取带统计信息的账户

        Args:
            user_id: 用户ID
            account_id: 账户ID

        Returns:
            带统计信息的账户
        """
        account = self.get_account(user_id, account_id)

        # 统计交易信息
        expense_stats = self.db.query(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.account_id == account_id,
            Transaction.type == TransactionType.EXPENSE
        ).first()

        income_stats = self.db.query(
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.account_id == account_id,
            Transaction.type == TransactionType.INCOME
        ).first()

        # 构建响应数据
        account_dict = {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "type": account.type,
            "balance": float(account.balance),
            "initial_balance": float(account.initial_balance),
            "icon": account.icon,
            "color": account.color,
            "is_default": account.is_default,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "transaction_count": (expense_stats.count or 0) + (income_stats.count or 0),
            "total_expense": float(expense_stats.total) if expense_stats and expense_stats.total else 0,
            "total_income": float(income_stats.total) if income_stats and income_stats.total else 0,
        }

        return AccountWithStats(**account_dict)

    def transfer_between_accounts(
        self,
        user_id: int,
        transfer_data: AccountTransfer
    ) -> tuple[Transaction, Transaction, Account, Account]:
        """
        账户间转账

        Args:
            user_id: 用户ID
            transfer_data: 转账数据

        Returns:
            转出交易、转入交易、转出账户、转入账户
        """
        # 验证账户存在
        from_account = self.get_account(user_id, transfer_data.from_account_id)
        to_account = self.get_account(user_id, transfer_data.to_account_id)

        # 不能转账到同一账户
        if transfer_data.from_account_id == transfer_data.to_account_id:
            raise ValidationError("不能转账到同一账户")

        # 检查转出账户余额
        if float(from_account.balance) < float(transfer_data.amount):
            raise ValidationError("转出账户余额不足")

        # 创建转出交易记录
        from_transaction = Transaction(
            user_id=user_id,
            type=TransactionType.TRANSFER,
            amount=transfer_data.amount,
            # 这里需要一个分类，通常转账会有专门的分类
            category_id=self._get_transfer_category_id(user_id),
            account_id=transfer_data.from_account_id,
            to_account_id=transfer_data.to_account_id,
            transaction_date=transfer_data.transaction_date or func.now(),
            remark=transfer_data.remark or f"转账至 {to_account.name}",
            source=TransactionSource.MANUAL
        )

        # 创建转入交易记录
        to_transaction = Transaction(
            user_id=user_id,
            type=TransactionType.TRANSFER,
            amount=transfer_data.amount,
            category_id=self._get_transfer_category_id(user_id),
            account_id=transfer_data.to_account_id,
            to_account_id=transfer_data.from_account_id,
            transaction_date=transfer_data.transaction_date or func.now(),
            remark=transfer_data.remark or f"从 {from_account.name} 转入",
            source=TransactionSource.MANUAL
        )

        # 更新账户余额
        from_account.balance -= transfer_data.amount
        to_account.balance += transfer_data.amount

        # 保存到数据库
        self.db.add(from_transaction)
        self.db.add(to_transaction)
        self.db.commit()

        self.db.refresh(from_transaction)
        self.db.refresh(to_transaction)
        self.db.refresh(from_account)
        self.db.refresh(to_account)

        # 记录余额变化历史
        balance_service = AccountBalanceHistoryService(self.db)
        try:
            # 记录转出和转入的余额变化
            balance_service.record_transfer_changes(
                from_account_id=transfer_data.from_account_id,
                to_account_id=transfer_data.to_account_id,
                amount=transfer_data.amount,
                transaction_id=from_transaction.id
            )
        except Exception:
            # 如果记录历史失败，不影响转账
            pass

        return from_transaction, to_transaction, from_account, to_account

    def get_account_summary(self, user_id: int) -> dict:
        """
        获取账户统计摘要

        Args:
            user_id: 用户ID

        Returns:
            账户统计摘要
        """
        accounts = self.get_accounts(user_id, is_enabled=True)

        total_balance = sum(float(account.balance) for account in accounts)

        # 按类型统计
        type_stats = {}
        for account in accounts:
            if account.type not in type_stats:
                type_stats[account.type] = {
                    "count": 0,
                    "balance": 0
                }
            type_stats[account.type]["count"] += 1
            type_stats[account.type]["balance"] += float(account.balance)

        return {
            "total_balance": total_balance,
            "account_count": len(accounts),
            "type_stats": type_stats
        }

    def _get_transfer_category_id(self, user_id: int) -> int:
        """
        获取转账分类ID

        Args:
            user_id: 用户ID

        Returns:
            转账分类ID
        """
        # 查找或创建转账专用分类
        from app.models.category import Category, CategoryType

        category = self.db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == "转账",
            Category.type == CategoryType.EXPENSE
        ).first()

        if not category:
            # 创建转账分类
            category = Category(
                user_id=user_id,
                name="转账",
                type=CategoryType.EXPENSE,
                icon="💱",
                color="#BDC3C7"
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        return category.id

    def get_default_account(self, user_id: int) -> Optional[Account]:
        """
        获取默认账户

        Args:
            user_id: 用户ID

        Returns:
            默认账户或None
        """
        return self.db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_default == True,
            Account.is_enabled == True
        ).first()

    def set_default_account(self, user_id: int, account_id: int) -> Account:
        """
        设置默认账户

        Args:
            user_id: 用户ID
            account_id: 账户ID

        Returns:
            设置为默认的账户
        """
        account = self.get_account(user_id, account_id)

        # 取消其他默认账户
        self.db.query(Account).filter(
            Account.user_id == user_id,
            Account.is_default == True
        ).update({"is_default": False})

        # 设置当前账户为默认
        account.is_default = True
        self.db.commit()
        self.db.refresh(account)

        return account