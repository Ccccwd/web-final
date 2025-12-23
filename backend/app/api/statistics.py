from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.config.database import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.account import Account
from app.core.responses import success_response, error_response
from app.utils.export import export_statistics_to_excel

router = APIRouter()

@router.get("/overview")
async def get_overview(
    current_year: Optional[int] = Query(None, description="年份"),
    current_month: Optional[int] = Query(None, description="月份"),
    db: Session = Depends(get_db)
):
    """获取首页概览数据"""
    try:
        # 获取当前时间
        now = datetime.now()
        year = current_year or now.year
        month = current_month or now.month

        # 当月开始和结束时间
        month_start = datetime(year, month, 1)
        if month == 12:
            next_month_start = datetime(year + 1, 1, 1)
        else:
            next_month_start = datetime(year, month + 1, 1)

        # 上月开始和结束时间
        if month == 1:
            last_month_start = datetime(year - 1, 12, 1)
            last_month_end = datetime(year, 1, 1)
        else:
            last_month_start = datetime(year, month - 1, 1)
            last_month_end = datetime(year, month, 1)

        # 当月收支统计
        monthly_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month_start
            )
        ).scalar()

        monthly_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month_start
            )
        ).scalar()

        monthly_balance = float(monthly_income - monthly_expense)

        # 上月收支统计（用于计算环比）
        last_month_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= last_month_start,
                Transaction.transaction_date < last_month_end
            )
        ).scalar()

        last_month_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= last_month_start,
                Transaction.transaction_date < last_month_end
            )
        ).scalar()

        # 计算环比增长率
        income_growth = calculate_growth_rate(monthly_income, last_month_income)
        expense_growth = calculate_growth_rate(monthly_expense, last_month_expense)

        # 账户总余额
        total_balance = db.query(func.coalesce(func.sum(Account.balance), 0)).scalar()

        # 分类占比统计
        category_stats = db.query(
            Category.name,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label('total_amount')
        ).join(
            Transaction, Category.id == Transaction.category_id
        ).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month_start
            )
        ).group_by(
            Category.id, Category.name, Category.icon, Category.color
        ).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(6).all()

        # 格式化分类数据
        category_data = []
        for stat in category_stats:
            category_data.append({
                "name": stat.name,
                "icon": stat.icon,
                "color": stat.color,
                "amount": float(stat.total_amount),
                "percentage": round(float(stat.total_amount / monthly_expense * 100), 2) if monthly_expense > 0 else 0
            })

        # 最近7天支出趋势
        trend_data = []
        for i in range(7):
            day_start = (now - timedelta(days=6-i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                and_(
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.transaction_date >= day_start,
                    Transaction.transaction_date < day_end
                )
            ).scalar()

            trend_data.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "amount": float(day_expense)
            })

        return success_response({
            "monthly_summary": {
                "income": float(monthly_income),
                "expense": float(monthly_expense),
                "balance": monthly_balance,
                "income_growth": income_growth,
                "expense_growth": expense_growth
            },
            "total_balance": float(total_balance),
            "category_distribution": category_data,
            "trend_data": trend_data,
            "period": f"{year}年{month}月"
        })

    except Exception as e:
        return error_response(500, f"获取概览数据失败: {str(e)}")

@router.get("/trend")
async def get_trend(
    period: str = Query("monthly", description="周期类型: daily, weekly, monthly, yearly"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取趋势数据"""
    try:
        # 解析日期参数
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # 默认最近6个月
            start_dt = datetime.now() - timedelta(days=180)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()

        # 根据周期类型查询数据
        if period == "daily":
            trend_data = get_daily_trend(db, start_dt, end_dt)
        elif period == "weekly":
            trend_data = get_weekly_trend(db, start_dt, end_dt)
        elif period == "monthly":
            trend_data = get_monthly_trend(db, start_dt, end_dt)
        elif period == "yearly":
            trend_data = get_yearly_trend(db, start_dt, end_dt)
        else:
            raise ValueError("不支持的周期类型")

        return success_response({
            "period": period,
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "trend": trend_data
        })

    except Exception as e:
        return error_response(500, f"获取趋势数据失败: {str(e)}")

@router.get("/category")
async def get_category_statistics(
    transaction_type: str = Query("expense", description="交易类型: income, expense"),
    period: str = Query("monthly", description="周期: monthly, yearly"),
    year: int = Query(..., description="年份"),
    month: Optional[int] = Query(None, description="月份，当period为monthly时必需"),
    db: Session = Depends(get_db)
):
    """获取分类统计"""
    try:
        # 确定时间范围
        if period == "monthly" and month:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
        elif period == "yearly":
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
        else:
            raise ValueError("无效的周期参数")

        # 确定交易类型
        trans_type = TransactionType.INCOME if transaction_type == "income" else TransactionType.EXPENSE

        # 查询分类统计数据
        category_stats = db.query(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount), 0).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction, Category.id == Transaction.category_id
        ).filter(
            and_(
                Transaction.type == trans_type,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < end_date
            )
        ).group_by(
            Category.id, Category.name, Category.icon, Category.color
        ).order_by(
            func.sum(Transaction.amount).desc()
        ).all()

        # 计算总金额
        total_amount = sum(float(stat.total_amount) for stat in category_stats)

        # 格式化数据
        result = []
        for stat in category_stats:
            result.append({
                "id": stat.id,
                "name": stat.name,
                "icon": stat.icon,
                "color": stat.color,
                "amount": float(stat.total_amount),
                "count": stat.transaction_count,
                "percentage": round(float(stat.total_amount / total_amount * 100), 2) if total_amount > 0 else 0
            })

        return success_response({
            "transaction_type": transaction_type,
            "period": period,
            "year": year,
            "month": month,
            "total_amount": total_amount,
            "categories": result
        })

    except Exception as e:
        return error_response(500, f"获取分类统计失败: {str(e)}")

@router.get("/export/excel")
async def export_excel(
    transaction_type: str = Query("all", description="交易类型: income, expense, all"),
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """导出Excel"""
    try:
        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        # 构建查询条件
        query_conditions = [
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date < end_dt
        ]

        if transaction_type != "all":
            trans_type = TransactionType.INCOME if transaction_type == "income" else TransactionType.EXPENSE
            query_conditions.append(Transaction.type == trans_type)

        # 查询数据
        transactions = db.query(Transaction).join(Category).filter(
            and_(*query_conditions)
        ).order_by(Transaction.transaction_date.desc()).all()

        # 导出Excel
        file_path = export_statistics_to_excel(transactions, transaction_type, start_dt, end_dt)

        return success_response({
            "message": "导出成功",
            "file_path": file_path,
            "filename": f"财务报表_{start_date}_{end_date}.xlsx"
        })

    except Exception as e:
        return error_response(500, f"导出Excel失败: {str(e)}")

def calculate_growth_rate(current: Decimal, previous: Decimal) -> float:
    """计算增长率"""
    if previous == 0:
        return 0.0
    return round(float((current - previous) / previous * 100), 2)

def get_daily_trend(db: Session, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """获取日趋势数据"""
    trend_data = []
    current_dt = start_dt

    while current_dt <= end_dt:
        next_dt = current_dt + timedelta(days=1)

        income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= current_dt,
                Transaction.transaction_date < next_dt
            )
        ).scalar()

        expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= current_dt,
                Transaction.transaction_date < next_dt
            )
        ).scalar()

        trend_data.append({
            "date": current_dt.strftime("%Y-%m-%d"),
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense)
        })

        current_dt = next_dt

    return trend_data

def get_weekly_trend(db: Session, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """获取周趋势数据"""
    trend_data = []
    current_dt = start_dt

    while current_dt <= end_dt:
        week_end = min(current_dt + timedelta(days=7), end_dt + timedelta(days=1))

        income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= current_dt,
                Transaction.transaction_date < week_end
            )
        ).scalar()

        expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= current_dt,
                Transaction.transaction_date < week_end
            )
        ).scalar()

        trend_data.append({
            "date": f"{current_dt.strftime('%Y-%m-%d')}至{(week_end - timedelta(days=1)).strftime('%m-%d')}",
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense)
        })

        current_dt = week_end

    return trend_data

def get_monthly_trend(db: Session, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """获取月趋势数据"""
    trend_data = []
    current_year = start_dt.year
    current_month = start_dt.month

    while (current_year < end_dt.year) or (current_year == end_dt.year and current_month <= end_dt.month):
        month_start = datetime(current_year, current_month, 1)
        if current_month == 12:
            next_month_start = datetime(current_year + 1, 1, 1)
            next_year = current_year + 1
            next_month = 1
        else:
            next_month_start = datetime(current_year, current_month + 1, 1)
            next_year = current_year
            next_month = current_month + 1

        income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month_start
            )
        ).scalar()

        expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < next_month_start
            )
        ).scalar()

        trend_data.append({
            "date": f"{current_year}年{current_month}月",
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense)
        })

        current_year = next_year
        current_month = next_month

    return trend_data

def get_yearly_trend(db: Session, start_dt: datetime, end_dt: datetime) -> List[Dict]:
    """获取年趋势数据"""
    trend_data = []
    start_year = start_dt.year
    end_year = end_dt.year

    for year in range(start_year, end_year + 1):
        year_start = datetime(year, 1, 1)
        year_end = datetime(year + 1, 1, 1)

        income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.INCOME,
                Transaction.transaction_date >= year_start,
                Transaction.transaction_date < year_end
            )
        ).scalar()

        expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.transaction_date >= year_start,
                Transaction.transaction_date < year_end
            )
        ).scalar()

        trend_data.append({
            "date": f"{year}年",
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense)
        })

    return trend_data