from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.account import Account
from app.models.budget import Budget
from app.core.exceptions import NotFoundError

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_monthly_report(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """
        生成月度财务报告

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            月度报告数据
        """
        # 计算月份的起止日期
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1) - timedelta(days=1)
        month_end = month_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 基础统计
        basic_stats = self._get_basic_stats(user_id, month_start, month_end)

        # 分类统计
        category_stats = self._get_category_stats(user_id, month_start, month_end)

        # 账户统计
        account_stats = self._get_account_stats(user_id, month_start, month_end)

        # 预算分析
        budget_analysis = self._get_budget_analysis(user_id, year, month)

        # 趋势分析（与上月对比）
        trend_analysis = self._get_trend_analysis(user_id, year, month)

        # 消费建议
        suggestions = self._generate_suggestions(basic_stats, category_stats, budget_analysis)

        report = {
            "report_period": {
                "year": year,
                "month": month,
                "start_date": month_start.isoformat(),
                "end_date": month_end.isoformat()
            },
            "basic_statistics": basic_stats,
            "category_analysis": category_stats,
            "account_analysis": account_stats,
            "budget_analysis": budget_analysis,
            "trend_analysis": trend_analysis,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }

        return report

    def generate_yearly_report(self, user_id: int, year: int) -> Dict[str, Any]:
        """
        生成年度财务报告

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            年度报告数据
        """
        # 计算年度的起止日期
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31, 23, 59, 59, 999999)

        # 年度基础统计
        basic_stats = self._get_basic_stats(user_id, year_start, year_end)

        # 月度趋势
        monthly_trends = self._get_monthly_trends(user_id, year)

        # 年度分类统计
        category_stats = self._get_category_stats(user_id, year_start, year_end)

        # 年度账户统计
        account_stats = self._get_account_stats(user_id, year_start, year_end)

        # 消费峰值分析
        peak_analysis = self._get_peak_analysis(user_id, year)

        # 年度总结和建议
        summary = self._generate_yearly_summary(basic_stats, monthly_trends, category_stats)

        report = {
            "report_period": {
                "year": year,
                "start_date": year_start.isoformat(),
                "end_date": year_end.isoformat()
            },
            "basic_statistics": basic_stats,
            "monthly_trends": monthly_trends,
            "category_analysis": category_stats,
            "account_analysis": account_stats,
            "peak_analysis": peak_analysis,
            "yearly_summary": summary,
            "generated_at": datetime.now().isoformat()
        }

        return report

    def generate_category_report(self, user_id: int, category_id: int, days: int = 30) -> Dict[str, Any]:
        """
        生成分类分析报告

        Args:
            user_id: 用户ID
            category_id: 分类ID
            days: 分析天数

        Returns:
            分类报告数据
        """
        # 验证分类存在
        category = self.db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise NotFoundError("分类不存在")

        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 分类统计
        stats = self.db.query(
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.max(Transaction.amount).label('max_amount'),
            func.min(Transaction.amount).label('min_amount')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).first()

        # 时间趋势
        daily_trends = self._get_category_daily_trends(user_id, category_id, days)

        # 商户分析
        merchant_analysis = self._get_merchant_analysis(user_id, category_id, days)

        report = {
            "category_info": {
                "id": category.id,
                "name": category.name,
                "type": category.type,
                "icon": category.icon,
                "color": category.color
            },
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "statistics": {
                "transaction_count": stats.transaction_count or 0,
                "total_amount": float(stats.total_amount) if stats.total_amount else 0,
                "average_amount": float(stats.avg_amount) if stats.avg_amount else 0,
                "max_amount": float(stats.max_amount) if stats.max_amount else 0,
                "min_amount": float(stats.min_amount) if stats.min_amount else 0,
                "daily_average": float(stats.total_amount) / days if stats.total_amount else 0
            },
            "daily_trends": daily_trends,
            "merchant_analysis": merchant_analysis,
            "generated_at": datetime.now().isoformat()
        }

        return report

    def _get_basic_stats(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """获取基础统计数据"""
        # 总收入
        total_income = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).scalar() or Decimal('0')

        # 总支出
        total_expense = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).scalar() or Decimal('0')

        # 交易次数
        transaction_count = self.db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).scalar() or 0

        # 净收入
        net_income = total_income - total_expense

        return {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_income": float(net_income),
            "transaction_count": transaction_count,
            "savings_rate": float(net_income / total_income) if total_income > 0 else 0
        }

    def _get_category_stats(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取分类统计数据"""
        # 支出分类统计
        expense_categories = self.db.query(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction, Transaction.category_id == Category.id
        ).filter(
            Category.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).group_by(
            Category.id, Category.name, Category.icon, Category.color
        ).order_by(
            desc('total_amount')
        ).all()

        category_stats = []
        for cat in expense_categories:
            category_stats.append({
                "id": cat.id,
                "name": cat.name,
                "icon": cat.icon,
                "color": cat.color,
                "total_amount": float(cat.total_amount),
                "transaction_count": cat.transaction_count,
                "average_amount": float(cat.total_amount / cat.transaction_count) if cat.transaction_count > 0 else 0
            })

        return category_stats

    def _get_account_stats(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取账户统计数据"""
        account_stats = self.db.query(
            Account.id,
            Account.name,
            Account.type,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction, Transaction.account_id == Account.id
        ).filter(
            Account.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).group_by(
            Account.id, Account.name, Account.type
        ).all()

        result = []
        for stat in account_stats:
            result.append({
                "id": stat.id,
                "name": stat.name,
                "type": stat.type,
                "total_amount": float(stat.total_amount) if stat.total_amount else 0,
                "transaction_count": stat.transaction_count
            })

        return result

    def _get_budget_analysis(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """获取预算分析"""
        budgets = self.db.query(Budget).filter(
            Budget.user_id == user_id,
            func.extract('year', Budget.start_date) == year,
            func.extract('month', Budget.start_date) == month,
            Budget.is_active == True
        ).all()

        budget_analysis = {
            "total_budgets": len(budgets),
            "active_budgets": 0,
            "over_budget_categories": [],
            "near_limit_categories": [],
            "budget_performance": []
        }

        for budget in budgets:
            # 计算当前支出
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)

            current_expense = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            ).scalar() or Decimal('0')

            usage_rate = float(current_expense) / float(budget.amount)

            budget_performance = {
                "category_id": budget.category_id,
                "category_name": budget.category.name if budget.category else "未知分类",
                "budget_amount": float(budget.amount),
                "current_expense": float(current_expense),
                "usage_rate": usage_rate,
                "remaining": float(budget.amount - current_expense)
            }

            budget_analysis["budget_performance"].append(budget_performance)

            if usage_rate >= 1.0:
                budget_analysis["over_budget_categories"].append(budget_performance)
            elif usage_rate >= 0.8:
                budget_analysis["near_limit_categories"].append(budget_performance)

            if usage_rate > 0:
                budget_analysis["active_budgets"] += 1

        return budget_analysis

    def _get_trend_analysis(self, user_id: int, year: int, month: int) -> Dict[str, Any]:
        """获取趋势分析（与上月对比）"""
        # 计算上月
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        current_month_stats = self._get_basic_stats(
            user_id,
            datetime(year, month, 1),
            datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
        )

        prev_month_stats = self._get_basic_stats(
            user_id,
            datetime(prev_year, prev_month, 1),
            datetime(prev_year, prev_month + 1, 1) - timedelta(days=1) if prev_month < 12 else datetime(prev_year + 1, 1, 1) - timedelta(days=1)
        )

        # 计算变化率
        income_change = ((current_month_stats["total_income"] - prev_month_stats["total_income"]) /
                        prev_month_stats["total_income"] * 100) if prev_month_stats["total_income"] > 0 else 0

        expense_change = ((current_month_stats["total_expense"] - prev_month_stats["total_expense"]) /
                         prev_month_stats["total_expense"] * 100) if prev_month_stats["total_expense"] > 0 else 0

        return {
            "income_change_rate": round(income_change, 2),
            "expense_change_rate": round(expense_change, 2),
            "current_month": current_month_stats,
            "previous_month": prev_month_stats
        }

    def _get_monthly_trends(self, user_id: int, year: int) -> List[Dict[str, Any]]:
        """获取月度趋势数据"""
        monthly_data = []

        for month in range(1, 13):
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month + 1, 1) - timedelta(days=1) if month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)

            stats = self._get_basic_stats(user_id, month_start, month_end)

            monthly_data.append({
                "month": month,
                "month_name": f"{year}年{month}月",
                "total_income": stats["total_income"],
                "total_expense": stats["total_expense"],
                "net_income": stats["net_income"],
                "transaction_count": stats["transaction_count"]
            })

        return monthly_data

    def _get_peak_analysis(self, user_id: int, year: int) -> Dict[str, Any]:
        """获取消费峰值分析"""
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31, 23, 59, 59, 999999)

        # 找出最大单笔支出
        max_expense = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= year_start,
            Transaction.transaction_date <= year_end
        ).order_by(desc(Transaction.amount)).first()

        # 找出消费最多的月份
        monthly_expenses = self.db.query(
            func.extract('month', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('total_expense')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= year_start,
            Transaction.transaction_date <= year_end
        ).group_by(
            func.extract('month', Transaction.transaction_date)
        ).order_by(desc('total_expense')).first()

        return {
            "largest_single_expense": {
                "amount": float(max_expense.amount) if max_expense else 0,
                "date": max_expense.transaction_date.isoformat() if max_expense else None,
                "category": max_expense.category.name if max_expense and max_expense.category else None,
                "remark": max_expense.remark if max_expense else None
            },
            "highest_expense_month": {
                "month": int(monthly_expenses.month) if monthly_expenses else None,
                "total_expense": float(monthly_expenses.total_expense) if monthly_expenses else 0
            }
        }

    def _get_category_daily_trends(self, user_id: int, category_id: int, days: int) -> List[Dict[str, Any]]:
        """获取分类每日趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 这里简化处理，实际可以按日期分组统计
        return []

    def _get_merchant_analysis(self, user_id: int, category_id: int, days: int) -> List[Dict[str, Any]]:
        """获取商户分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        merchants = self.db.query(
            Transaction.merchant_name,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.merchant_name.isnot(None)
        ).group_by(
            Transaction.merchant_name
        ).order_by(
            desc('total_amount')
        ).limit(10).all()

        result = []
        for merchant in merchants:
            result.append({
                "merchant_name": merchant.merchant_name,
                "total_amount": float(merchant.total_amount),
                "transaction_count": merchant.transaction_count
            })

        return result

    def _generate_suggestions(self, basic_stats: Dict, category_stats: List, budget_analysis: Dict) -> List[str]:
        """生成消费建议"""
        suggestions = []

        # 基于储蓄率的建议
        if basic_stats["savings_rate"] < 0.2:
            suggestions.append("您的储蓄率较低，建议控制支出，增加储蓄比例至20%以上。")
        elif basic_stats["savings_rate"] > 0.5:
            suggestions.append("您的储蓄率很高，可以考虑适当投资理财，让资金保值增值。")

        # 基于预算的建议
        if budget_analysis["over_budget_categories"]:
            suggestions.append(f"您有{len(budget_analysis['over_budget_categories'])}个分类超出预算，建议查看并控制相关支出。")

        if budget_analysis["near_limit_categories"]:
            suggestions.append(f"您有{len(budget_analysis['near_limit_categories'])}个分类接近预算上限，请注意控制支出。")

        # 基于分类的建议
        if category_stats:
            top_category = max(category_stats, key=lambda x: x["total_amount"])
            if top_category["total_amount"] > basic_stats["total_expense"] * 0.4:
                suggestions.append(f"您的{top_category['name']}支出占比较高，建议分析该分类的具体消费项目。")

        return suggestions

    def _generate_yearly_summary(self, basic_stats: Dict, monthly_trends: List, category_stats: List) -> Dict[str, Any]:
        """生成年度总结"""
        # 找出收入和支出最多的月份
        max_income_month = max(monthly_trends, key=lambda x: x["total_income"])
        max_expense_month = max(monthly_trends, key=lambda x: x["total_expense"])

        # 找出主要消费分类
        top_categories = sorted(category_stats, key=lambda x: x["total_amount"], reverse=True)[:3]

        summary = {
            "financial_health_score": min(100, max(0, basic_stats["savings_rate"] * 100)),
            "best_income_month": max_income_month["month_name"],
            "highest_expense_month": max_expense_month["month_name"],
            "top_expense_categories": top_categories,
            "total_months_with_surplus": len([m for m in monthly_trends if m["net_income"] > 0]),
            "average_monthly_income": sum(m["total_income"] for m in monthly_trends) / 12,
            "average_monthly_expense": sum(m["total_expense"] for m in monthly_trends) / 12
        }

        return summary