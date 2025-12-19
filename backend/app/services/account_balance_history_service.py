from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.account_balance_history import AccountBalanceHistory, BalanceChangeType
from app.core.exceptions import NotFoundError, ValidationError

class AccountBalanceHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def record_balance_change(
        self,
        account_id: int,
        change_type: BalanceChangeType,
        amount_before: Decimal,
        amount_after: Decimal,
        change_amount: Decimal,
        description: Optional[str] = None,
        transaction_id: Optional[int] = None,
        reference_id: Optional[str] = None
    ) -> AccountBalanceHistory:
        """
        记录账户余额变化

        Args:
            account_id: 账户ID
            change_type: 变化类型
            amount_before: 变化前余额
            amount_after: 变化后余额
            change_amount: 变化金额
            description: 描述
            transaction_id: 关联交易ID
            reference_id: 参考ID

        Returns:
            余额历史记录
        """
        # 验证账户存在
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise NotFoundError("账户不存在")

        # 验证余额变化是否一致
        if amount_after != amount_before + change_amount:
            raise ValidationError("余额变化不一致")

        # 创建余额历史记录
        history = AccountBalanceHistory(
            user_id=account.user_id,
            account_id=account_id,
            transaction_id=transaction_id,
            change_type=change_type,
            amount_before=amount_before,
            amount_after=amount_after,
            change_amount=change_amount,
            description=description,
            reference_id=reference_id
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def get_account_balance_history(
        self,
        user_id: int,
        account_id: int,
        limit: int = 50,
        offset: int = 0,
        change_type: Optional[BalanceChangeType] = None
    ) -> List[AccountBalanceHistory]:
        """
        获取账户余额历史

        Args:
            user_id: 用户ID
            account_id: 账户ID
            limit: 限制数量
            offset: 偏移量
            change_type: 变化类型过滤

        Returns:
            余额历史记录列表
        """
        # 验证账户存在且属于用户
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()

        if not account:
            raise NotFoundError("账户不存在")

        # 构建查询
        query = self.db.query(AccountBalanceHistory).filter(
            AccountBalanceHistory.account_id == account_id
        )

        if change_type:
            query = query.filter(AccountBalanceHistory.change_type == change_type)

        return query.order_by(desc(AccountBalanceHistory.created_at)).offset(offset).limit(limit).all()

    def get_user_balance_history(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        change_type: Optional[BalanceChangeType] = None
    ) -> List[AccountBalanceHistory]:
        """
        获取用户所有账户的余额历史

        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            change_type: 变化类型过滤

        Returns:
            余额历史记录列表
        """
        query = self.db.query(AccountBalanceHistory).filter(
            AccountBalanceHistory.user_id == user_id
        )

        if change_type:
            query = query.filter(AccountBalanceHistory.change_type == change_type)

        return query.order_by(desc(AccountBalanceHistory.created_at)).offset(offset).limit(limit).all()

    def record_initial_balance(self, account_id: int) -> AccountBalanceHistory:
        """
        记录账户初始余额

        Args:
            account_id: 账户ID

        Returns:
            余额历史记录
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise NotFoundError("账户不存在")

        return self.record_balance_change(
            account_id=account_id,
            change_type=BalanceChangeType.INITIAL,
            amount_before=Decimal('0'),
            amount_after=account.balance,
            change_amount=account.balance,
            description=f"账户 {account.name} 初始余额"
        )

    def record_transaction_change(self, transaction: Transaction) -> Optional[AccountBalanceHistory]:
        """
        记录交易引起的余额变化

        Args:
            transaction: 交易记录

        Returns:
            余额历史记录
        """
        account = transaction.account

        # 计算交易对账户余额的影响
        if transaction.type == TransactionType.INCOME:
            change_amount = transaction.amount
            description = f"收入: {transaction.remark or transaction.category.name}"
        elif transaction.type == TransactionType.EXPENSE:
            change_amount = -transaction.amount
            description = f"支出: {transaction.remark or transaction.category.name}"
        elif transaction.type == TransactionType.TRANSFER:
            # 转账会在transfer_between_accounts中特殊处理
            if transaction.to_account_id:
                change_amount = -transaction.amount  # 转出
                description = f"转出至: {transaction.to_account.name if transaction.to_account else '未知账户'}"
            else:
                return None
        else:
            return None

        # 记录余额变化
        return self.record_balance_change(
            account_id=account.id,
            change_type=BalanceChangeType.TRANSACTION,
            amount_before=account.balance - change_amount,
            amount_after=account.balance,
            change_amount=change_amount,
            description=description,
            transaction_id=transaction.id
        )

    def record_transfer_changes(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        transaction_id: Optional[int] = None,
        reference_id: Optional[str] = None
    ) -> tuple[AccountBalanceHistory, AccountBalanceHistory]:
        """
        记录转账的余额变化

        Args:
            from_account_id: 转出账户ID
            to_account_id: 转入账户ID
            amount: 转账金额
            transaction_id: 交易ID
            reference_id: 参考ID

        Returns:
            转出和转入的余额历史记录
        """
        from_account = self.db.query(Account).filter(Account.id == from_account_id).first()
        to_account = self.db.query(Account).filter(Account.id == to_account_id).first()

        if not from_account or not to_account:
            raise NotFoundError("账户不存在")

        # 记录转出账户余额变化
        from_history = self.record_balance_change(
            account_id=from_account_id,
            change_type=BalanceChangeType.TRANSFER_OUT,
            amount_before=from_account.balance + amount,
            amount_after=from_account.balance,
            change_amount=-amount,
            description=f"转账转出至 {to_account.name}",
            transaction_id=transaction_id,
            reference_id=reference_id
        )

        # 记录转入账户余额变化
        to_history = self.record_balance_change(
            account_id=to_account_id,
            change_type=BalanceChangeType.TRANSFER_IN,
            amount_before=to_account.balance - amount,
            amount_after=to_account.balance,
            change_amount=amount,
            description=f"从 {from_account.name} 转入",
            transaction_id=transaction_id,
            reference_id=reference_id
        )

        return from_history, to_history

    def get_balance_statistics(
        self,
        user_id: int,
        account_id: int,
        days: int = 30
    ) -> dict:
        """
        获取账户余额统计信息

        Args:
            user_id: 用户ID
            account_id: 账户ID
            days: 统计天数

        Returns:
            统计信息
        """
        # 验证账户存在且属于用户
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()

        if not account:
            raise NotFoundError("账户不存在")

        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        # 查询指定时间段内的余额变化
        histories = self.db.query(AccountBalanceHistory).filter(
            and_(
                AccountBalanceHistory.account_id == account_id,
                AccountBalanceHistory.created_at >= start_date
            )
        ).all()

        # 统计各类变化
        total_income = Decimal('0')
        total_expense = Decimal('0')
        transfer_in = Decimal('0')
        transfer_out = Decimal('0')

        for history in histories:
            if history.change_type == BalanceChangeType.TRANSACTION:
                if history.change_amount > 0:
                    total_income += history.change_amount
                else:
                    total_expense += abs(history.change_amount)
            elif history.change_type == BalanceChangeType.TRANSFER_IN:
                transfer_in += history.change_amount
            elif history.change_type == BalanceChangeType.TRANSFER_OUT:
                transfer_out += abs(history.change_amount)

        return {
            "current_balance": float(account.balance),
            "period_days": days,
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "transfer_in": float(transfer_in),
            "transfer_out": float(transfer_out),
            "net_change": float(total_income - total_expense),
            "change_count": len(histories)
        }