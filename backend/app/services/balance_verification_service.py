from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json

from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.import_log import ImportLog
from app.models.balance_verification import BalanceVerification, UserPreference
from app.models.user import User
from app.models.account_balance_history import AccountBalanceHistory
from app.core.exceptions import NotFoundError, ValidationError

class BalanceVerificationService:
    def __init__(self, db: Session):
        self.db = db

    def verify_balance_after_import(
        self,
        import_log_id: int,
        tolerance: float = 0.01
    ) -> Dict:
        """
        导入后验证账户余额

        Args:
            import_log_id: 导入日志ID
            tolerance: 容差范围

        Returns:
            验证结果
        """
        import_log = self.db.query(ImportLog).filter(
            ImportLog.id == import_log_id
        ).first()

        if not import_log:
            raise NotFoundError("导入日志不存在")

        # 获取导入期间影响的账户
        affected_accounts = self._get_affected_accounts(import_log_id)

        verification_results = []
        all_valid = True

        for account in affected_accounts:
            # 计算预期余额
            expected_balance = self._calculate_expected_balance(
                account.id, import_log.started_at
            )

            # 获取实际余额
            actual_balance = float(account.balance)

            # 计算差异
            difference = abs(expected_balance - actual_balance)
            is_valid = difference <= tolerance * max(abs(expected_balance), abs(actual_balance), 1)

            # 创建余额校验记录
            verification = BalanceVerification(
                user_id=import_log.user_id,
                import_log_id=import_log_id,
                account_id=account.id,
                expected_balance=expected_balance,
                actual_balance=actual_balance,
                difference=difference,
                is_valid=is_valid,
                tolerance=tolerance,
                verification_method="import_check",
                verification_details={
                    "import_time": import_log.started_at.isoformat(),
                    "tolerance": tolerance,
                    "expected_calculation": self._get_balance_calculation_details(
                        account.id, import_log.started_at
                    )
                }
            )

            self.db.add(verification)

            if not is_valid:
                all_valid = False
                # 添加不匹配详情
                verification.mismatch_details = self._analyze_mismatch(
                    account.id, expected_balance, actual_balance
                )

            verification_results.append({
                "account_id": account.id,
                "account_name": account.name,
                "expected_balance": expected_balance,
                "actual_balance": actual_balance,
                "difference": difference,
                "is_valid": is_valid
            })

        self.db.commit()

        return {
            "import_log_id": import_log_id,
            "verification_time": datetime.now().isoformat(),
            "tolerance": tolerance,
            "all_valid": all_valid,
            "affected_accounts": len(affected_accounts),
            "results": verification_results,
            "invalid_count": len([r for r in verification_results if not r["is_valid"]])
        }

    def _get_affected_accounts(self, import_log_id: int) -> List[Account]:
        """
        获取受导入影响的账户

        Args:
            import_log_id: 导入日志ID

        Returns:
            账户列表
        """
        # 这里简化处理，实际应该根据导入的交易记录来确定影响的账户
        # 返回所有启用账户作为默认
        return self.db.query(Account).filter(
            Account.is_enabled == True
        ).all()

    def _calculate_expected_balance(
        self,
        account_id: int,
        import_time: datetime
    ) -> float:
        """
        计算预期余额

        Args:
            account_id: 账户ID
            import_time: 导入时间

        Returns:
            预期余额
        """
        # 获取导入前的余额历史
        last_balance_before_import = self.db.query(func.max(
            AccountBalanceHistory.amount_after
        )).filter(
            AccountBalanceHistory.account_id == account_id,
            AccountBalanceHistory.created_at < import_time
        ).scalar()

        if last_balance_before_import is not None:
            return float(last_balance_before_import)

        # 如果没有历史记录，使用账户初始余额
        account = self.db.query(Account).filter(
            Account.id == account_id
        ).first()

        return float(account.initial_balance) if account else 0.0

    def _get_balance_calculation_details(
        self,
        account_id: int,
        import_time: datetime
    ) -> Dict:
        """
        获取余额计算详情

        Args:
            account_id: 账户ID
            import_time: 导入时间

        Returns:
            计算详情
        """
        # 获取导入时间点前的所有相关交易
        transactions = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.transaction_date < import_time
        ).order_by(
            Transaction.transaction_date.desc()
        ).all()

        income_total = sum(
            t.amount for t in transactions if t.type == TransactionType.INCOME
        )
        expense_total = sum(
            t.amount for t in transactions if t.type == TransactionType.EXPENSE
        )

        return {
            "transaction_count": len(transactions),
            "income_total": income_total,
            "expense_total": expense_total,
            "net_change": income_total - expense_total,
            "initial_balance": 0.0,  # 需要从账户历史中获取
            "calculated_at": datetime.now().isoformat()
        }

    def _analyze_mismatch(
        self,
        account_id: int,
        expected_balance: float,
        actual_balance: float
    ) -> List[Dict]:
        """
        分析余额不匹配的原因

        Args:
            account_id: 账户ID
            expected_balance: 预期余额
            actual_balance: 实际余额

        Returns:
            不匹配详情列表
        """
        mismatches = []
        difference = actual_balance - expected_balance

        if abs(difference) > 0:
            # 分析可能的原因
            if difference > 0:
                # 实际余额大于预期
                mismatches.append({
                    "type": "excess_balance",
                    "description": f"实际余额比预期多 {difference:.2f} 元",
                    "possible_causes": [
                        "有未记录的收入",
                        "转账记录遗漏",
                        "初始余额设置错误",
                        "手动调整余额未记录"
                    ]
                })
            else:
                # 实际余额小于预期
                mismatches.append({
                    "type": "deficit_balance",
                    "description": f"实际余额比预期少 {abs(difference):.2f} 元",
                    "possible_causes": [
                        "有未记录的支出",
                        "费用计算错误",
                        "转账记录重复",
                        "交易记录遗漏"
                    ]
                })

            # 检查最近的交易记录
            recent_transactions = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.transaction_date >= datetime.now() - timedelta(days=7)
            ).order_by(
                Transaction.transaction_date.desc()
            ).limit(10).all()

            if recent_transactions:
                mismatches.append({
                    "type": "recent_transactions_review",
                    "description": "建议检查最近7天的交易记录",
                    "recent_transactions": [
                        {
                            "date": t.transaction_date.isoformat(),
                            "type": t.type,
                            "amount": float(t.amount),
                            "merchant": t.merchant_name
                        } for t in recent_transactions
                    ]
                })

        return mismatches

    def get_user_preferences(self, user_id: int) -> UserPreference:
        """
        获取用户余额校验偏好

        Args:
            user_id: 用户ID

        Returns:
            用户偏好
        """
        preferences = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not preferences:
            # 创建默认偏好
            preferences = UserPreference(
                user_id=user_id,
                balance_verification_enabled=True,
                tolerance=0.01
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def update_user_preferences(
        self,
        user_id: int,
        preferences_data: Dict
    ) -> UserPreference:
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            preferences_data: 偏好数据

        Returns:
            更新后的偏好
        """
        preferences = self.get_user_preferences(user_id)

        # 更新字段
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    def get_verification_history(
        self,
        user_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        获取校验历史

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            校验历史记录
        """
        start_date = datetime.now() - timedelta(days=days)

        verifications = self.db.query(BalanceVerification).filter(
            BalanceVerification.user_id == user_id,
            BalanceVerification.created_at >= start_date
        ).order_by(
            BalanceVerification.created_at.desc()
        ).all()

        history = []
        for verification in verifications:
            account = self.db.query(Account).filter(
                Account.id == verification.account_id
            ).first()

            history.append({
                "id": verification.id,
                "account_name": account.name if account else "Unknown",
                "expected_balance": verification.expected_balance,
                "actual_balance": verification.actual_balance,
                "difference": verification.difference,
                "is_valid": verification.is_valid,
                "verification_time": verification.created_at.isoformat(),
                "status": verification.status
            })

        return history

    def get_verification_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict:
        """
        获取校验摘要

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            校验摘要
        """
        start_date = datetime.now() - timedelta(days=days)

        total_verifications = self.db.query(BalanceVerification).filter(
            BalanceVerification.user_id == user_id,
            BalanceVerification.created_at >= start_date
        ).count()

        valid_verifications = self.db.query(BalanceVerification).filter(
            BalanceVerification.user_id == user_id,
            BalanceVerification.is_valid == True,
            BalanceVerification.created_at >= start_date
        ).count()

        invalid_verifications = total_verifications - valid_verifications

        # 计算平均差异
        avg_difference = self.db.query(func.avg(
            func.abs(BalanceVerification.difference)
        )).filter(
            BalanceVerification.user_id == user_id,
            BalanceVerification.created_at >= start_date
        ).scalar() or 0

        # 最新的校验记录
        latest_verification = self.db.query(BalanceVerification).filter(
            BalanceVerification.user_id == user_id
        ).order_by(
            BalanceVerification.created_at.desc()
        ).first()

        return {
            "period_days": days,
            "total_verifications": total_verifications,
            "valid_verifications": valid_verifications,
            "invalid_verifications": invalid_verifications,
            "success_rate": (valid_verifications / total_verifications * 100) if total_verifications > 0 else 0,
            "average_difference": round(avg_difference, 2),
            "latest_verification": {
                "id": latest_verification.id if latest_verification else None,
                "is_valid": latest_verification.is_valid if latest_verification else None,
                "time": latest_verification.created_at.isoformat() if latest_verification else None,
                "difference": latest_verification.difference if latest_verification else 0
            }
        }

    def create_auto_verification_rule(
        self,
        user_id: int,
        rule_name: str,
        condition: Dict,
        action: Dict
    ) -> Dict:
        """
        创建自动校验规则（占位符方法）

        Args:
            user_id: 用户ID
            rule_name: 规则名称
            condition: 条件
            action: 操作

        Returns:
            创建结果
        """
        # 这里可以实现更复杂的自动校验规则
        # 比如定期校验、特定条件触发等
        return {
            "success": True,
            "message": "自动校验规则创建成功",
            "rule_name": rule_name
        }