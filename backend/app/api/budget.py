from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.config.database import get_db
from app.models.budget import Budget, PeriodType
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.core.responses import success_response, error_response

router = APIRouter()

@router.get("/")
async def get_budgets(
    year: int = Query(..., description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    period_type: Optional[str] = Query(None, description="周期类型: monthly, yearly"),
    db: Session = Depends(get_db)
):
    """获取预算列表"""
    try:
        # 构建查询条件
        query_conditions = [Budget.year == year]

        if month:
            query_conditions.append(Budget.month == month)
        else:
            query_conditions.append(Budget.month.is_(None))

        if period_type:
            query_conditions.append(Budget.period_type == period_type)

        # 查询预算
        budgets = db.query(Budget).join(Category).filter(
            and_(*query_conditions)
        ).all()

        # 获取预算执行情况
        budget_data = []
        for budget in budgets:
            # 计算实际支出
            actual_spending = get_actual_spending(db, budget)
            percentage = calculate_percentage(actual_spending, budget.amount)
            status = get_budget_status(percentage, budget.alert_threshold)

            budget_data.append({
                "id": budget.id,
                "category": {
                    "id": budget.category.id,
                    "name": budget.category.name,
                    "icon": budget.category.icon,
                    "color": budget.category.color
                } if budget.category else None,
                "amount": float(budget.amount),
                "actual_spending": float(actual_spending),
                "remaining": float(budget.amount - actual_spending),
                "percentage": percentage,
                "status": status,
                "period_type": budget.period_type.value,
                "year": budget.year,
                "month": budget.month,
                "alert_threshold": budget.alert_threshold,
                "is_enabled": budget.is_enabled,
                "created_at": budget.created_at.isoformat() if budget.created_at else None
            })

        return success_response({
            "year": year,
            "month": month,
            "period_type": period_type,
            "budgets": budget_data
        })

    except Exception as e:
        return error_response(500, f"获取预算列表失败: {str(e)}")

@router.post("/")
async def create_budget(
    budget_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """创建预算"""
    try:
        # 验证数据
        category_id = budget_data.get("category_id")
        amount = budget_data.get("amount")
        period_type = budget_data.get("period_type")
        year = budget_data.get("year")
        month = budget_data.get("month")

        if not amount or amount <= 0:
            raise ValueError("预算金额必须大于0")

        if not year or year < 1900 or year > 2100:
            raise ValueError("年份无效")

        if period_type == "monthly" and (not month or month < 1 or month > 12):
            raise ValueError("月份无效")

        # 检查是否已存在相同预算
        existing_budget = db.query(Budget).filter(
            and_(
                Budget.category_id == category_id,
                Budget.year == year,
                Budget.month == month,
                Budget.period_type == period_type
            )
        ).first()

        if existing_budget:
            raise ValueError("该预算已存在")

        # 验证分类是否存在
        if category_id:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise ValueError("分类不存在")

        # 创建预算
        budget = Budget(
            category_id=category_id,
            amount=Decimal(str(amount)),
            period_type=PeriodType(period_type),
            year=year,
            month=month,
            alert_threshold=budget_data.get("alert_threshold", 80),
            is_enabled=budget_data.get("is_enabled", True)
        )

        db.add(budget)
        db.commit()
        db.refresh(budget)

        return success_response({
            "id": budget.id,
            "message": "预算创建成功"
        })

    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"创建预算失败: {str(e)}")

@router.put("/{budget_id}")
async def update_budget(
    budget_id: int,
    budget_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新预算"""
    try:
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError("预算不存在")

        # 更新字段
        if "amount" in budget_data:
            amount = budget_data["amount"]
            if amount <= 0:
                raise ValueError("预算金额必须大于0")
            budget.amount = Decimal(str(amount))

        if "alert_threshold" in budget_data:
            threshold = budget_data["alert_threshold"]
            if threshold < 0 or threshold > 100:
                raise ValueError("预警阈值必须在0-100之间")
            budget.alert_threshold = threshold

        if "is_enabled" in budget_data:
            budget.is_enabled = budget_data["is_enabled"]

        db.commit()
        db.refresh(budget)

        return success_response({
            "message": "预算更新成功"
        })

    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"更新预算失败: {str(e)}")

@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """删除预算"""
    try:
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError("预算不存在")

        db.delete(budget)
        db.commit()

        return success_response({
            "message": "预算删除成功"
        })

    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"删除预算失败: {str(e)}")

@router.get("/summary")
async def get_budget_summary(
    year: int = Query(..., description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    db: Session = Depends(get_db)
):
    """获取预算汇总信息"""
    try:
        # 构建查询条件
        query_conditions = [
            Budget.year == year,
            Budget.is_enabled == True
        ]

        if month:
            query_conditions.append(Budget.month == month)
        else:
            query_conditions.append(Budget.month.is_(None))

        # 查询所有启用的预算
        budgets = db.query(Budget).join(Category).filter(
            and_(*query_conditions)
        ).all()

        total_budget = Decimal('0')
        total_spending = Decimal('0')
        budget_count = 0
        over_budget_count = 0
        warning_count = 0

        budget_details = []
        for budget in budgets:
            actual_spending = get_actual_spending(db, budget)
            percentage = calculate_percentage(actual_spending, budget.amount)
            status = get_budget_status(percentage, budget.alert_threshold)

            total_budget += budget.amount
            total_spending += actual_spending
            budget_count += 1

            if status == "exceeded":
                over_budget_count += 1
            elif status == "warning":
                warning_count += 1

            budget_details.append({
                "category_name": budget.category.name if budget.category else "总预算",
                "budget_amount": float(budget.amount),
                "actual_spending": float(actual_spending),
                "percentage": percentage,
                "status": status
            })

        total_remaining = float(total_budget - total_spending)
        total_percentage = calculate_percentage(total_spending, total_budget)
        overall_status = get_budget_status(total_percentage, 80)

        return success_response({
            "year": year,
            "month": month,
            "summary": {
                "total_budget": float(total_budget),
                "total_spending": float(total_spending),
                "total_remaining": total_remaining,
                "total_percentage": total_percentage,
                "overall_status": overall_status,
                "budget_count": budget_count,
                "over_budget_count": over_budget_count,
                "warning_count": warning_count
            },
            "details": budget_details
        })

    except Exception as e:
        return error_response(500, f"获取预算汇总失败: {str(e)}")

@router.get("/alerts")
async def get_budget_alerts(
    db: Session = Depends(get_db)
):
    """获取预算预警信息"""
    try:
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        # 查询当前月份的所有启用预算
        budgets = db.query(Budget).join(Category).filter(
            and_(
                Budget.year == current_year,
                or_(
                    and_(Budget.month == current_month, Budget.period_type == PeriodType.MONTHLY),
                    Budget.period_type == PeriodType.YEARLY
                ),
                Budget.is_enabled == True
            )
        ).all()

        alerts = []
        for budget in budgets:
            actual_spending = get_actual_spending(db, budget)
            percentage = calculate_percentage(actual_spending, budget.amount)
            status = get_budget_status(percentage, budget.alert_threshold)

            if status in ["warning", "exceeded"]:
                alerts.append({
                    "id": budget.id,
                    "category_name": budget.category.name if budget.category else "总预算",
                    "budget_amount": float(budget.amount),
                    "actual_spending": float(actual_spending),
                    "percentage": percentage,
                    "status": status,
                    "remaining": float(budget.amount - actual_spending),
                    "alert_threshold": budget.alert_threshold,
                    "period_type": budget.period_type.value
                })

        # 按百分比排序，超支的排在前面
        alerts.sort(key=lambda x: x["percentage"], reverse=True)

        return success_response({
            "alerts": alerts,
            "total_count": len(alerts),
            "warning_count": len([a for a in alerts if a["status"] == "warning"]),
            "exceeded_count": len([a for a in alerts if a["status"] == "exceeded"])
        })

    except Exception as e:
        return error_response(500, f"获取预算预警失败: {str(e)}")

def get_actual_spending(db: Session, budget: Budget) -> Decimal:
    """计算预算期间的实际支出"""
    query_conditions = [
        Transaction.type == TransactionType.EXPENSE
    ]

    # 时间范围
    if budget.period_type == PeriodType.MONTHLY and budget.month:
        start_date = datetime(budget.year, budget.month, 1)
        if budget.month == 12:
            end_date = datetime(budget.year + 1, 1, 1)
        else:
            end_date = datetime(budget.year, budget.month + 1, 1)
    else:  # YEARLY
        start_date = datetime(budget.year, 1, 1)
        end_date = datetime(budget.year + 1, 1, 1)

    query_conditions.extend([
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date < end_date
    ])

    # 分类筛选
    if budget.category_id:
        query_conditions.append(Transaction.category_id == budget.category_id)

    actual_spending = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        and_(*query_conditions)
    ).scalar()

    return actual_spending or Decimal('0')

def calculate_percentage(actual: Decimal, budget: Decimal) -> float:
    """计算预算使用百分比"""
    if budget == 0:
        return 0.0
    return round(float(actual / budget * 100), 2)

def get_budget_status(percentage: float, alert_threshold: int) -> str:
    """获取预算状态"""
    if percentage >= 100:
        return "exceeded"  # 超支
    elif percentage >= alert_threshold:
        return "warning"    # 预警
    else:
        return "normal"     # 正常