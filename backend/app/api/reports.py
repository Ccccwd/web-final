from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.report_service import ReportService
from app.services.reminder_service import ReminderService
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """获取报告服务实例"""
    return ReportService(db)

def get_reminder_service(db: Session = Depends(get_db)) -> ReminderService:
    """获取提醒服务实例"""
    return ReminderService(db)

@router.get("/monthly")
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2030, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """获取月度财务报告"""
    try:
        report = report_service.generate_monthly_report(
            user_id=current_user.id,
            year=year,
            month=month
        )

        return success_response(data=report)

    except Exception as e:
        return error_response(500, f"生成月度报告失败: {str(e)}")

@router.get("/yearly")
async def get_yearly_report(
    year: int = Query(..., ge=2020, le=2030, description="年份"),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """获取年度财务报告"""
    try:
        report = report_service.generate_yearly_report(
            user_id=current_user.id,
            year=year
        )

        return success_response(data=report)

    except Exception as e:
        return error_response(500, f"生成年度报告失败: {str(e)}")

@router.get("/category/{category_id}")
async def get_category_report(
    category_id: int,
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """获取分类分析报告"""
    try:
        report = report_service.generate_category_report(
            user_id=current_user.id,
            category_id=category_id,
            days=days
        )

        return success_response(data=report)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"生成分类报告失败: {str(e)}")

@router.post("/monthly-auto-report")
async def generate_monthly_auto_report(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """生成并自动发送月度报告"""
    try:
        from datetime import datetime

        now = datetime.now()
        report = report_service.generate_monthly_report(
            user_id=current_user.id,
            year=now.year,
            month=now.month
        )

        # 生成报告摘要
        basic_stats = report.get("basic_statistics", {})
        suggestions = report.get("suggestions", [])

        summary = f"""
月度财务报告摘要 ({now.year}年{now.month}月):

📊 财务概况:
• 总收入: ¥{basic_stats.get('total_income', 0):,.2f}
• 总支出: ¥{basic_stats.get('total_expense', 0):,.2f}
• 净收入: ¥{basic_stats.get('net_income', 0):,.2f}
• 储蓄率: {basic_stats.get('savings_rate', 0):.1%}
• 交易次数: {basic_stats.get('transaction_count', 0)}

💡 理财建议:
{chr(10).join(f"• {suggestion}" for suggestion in suggestions) if suggestions else "• 继续保持良好的记账习惯！"}

详细的月度报告已在系统中生成，请登录查看完整分析。
        """

        return success_response(
            message="月度报告生成成功",
            data={
                "report": report,
                "summary": summary.strip(),
                "generated_at": now.isoformat()
            }
        )

    except Exception as e:
        return error_response(500, f"生成自动报告失败: {str(e)}")

@router.get("/overview")
async def get_financial_overview(
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """获取财务概览（最近7天）"""
    try:
        from datetime import datetime, timedelta

        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # 获取基础统计
        basic_stats = report_service._get_basic_stats(
            user_id=current_user.id,
            start_date=week_ago,
            end_date=now
        )

        # 获取分类统计（前5个）
        category_stats = report_service._get_category_stats(
            user_id=current_user.id,
            start_date=week_ago,
            end_date=now
        )[:5]

        overview = {
            "period": {
                "start_date": week_ago.isoformat(),
                "end_date": now.isoformat(),
                "days": 7
            },
            "basic_statistics": basic_stats,
            "top_categories": category_stats
        }

        return success_response(data=overview)

    except Exception as e:
        return error_response(500, f"获取财务概览失败: {str(e)}")

@router.get("/savings-goal")
async def get_savings_goal_analysis(
    target_amount: float = Query(..., gt=0, description="目标金额"),
    target_months: int = Query(12, ge=1, le=120, description="目标月数"),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """获取储蓄目标分析"""
    try:
        from datetime import datetime, timedelta

        # 计算最近6个月的平均净收入
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)

        basic_stats = report_service._get_basic_stats(
            user_id=current_user.id,
            start_date=six_months_ago,
            end_date=now
        )

        monthly_net_income = basic_stats.get('net_income', 0)
        monthly_avg_net_income = monthly_net_income / 6 if monthly_net_income > 0 else 0

        # 计算达成目标所需的时间和月储蓄
        required_monthly_saving = target_amount / target_months

        # 分析
        analysis = {
            "target": {
                "amount": target_amount,
                "months": target_months,
                "required_monthly_saving": required_monthly_saving
            },
            "current_performance": {
                "recent_monthly_net_income": monthly_avg_net_income,
                "savings_gap": max(0, required_monthly_saving - monthly_avg_net_income),
                "can_achieve": monthly_avg_net_income >= required_monthly_saving
            },
            "recommendations": []
        }

        # 生成建议
        if analysis["current_performance"]["can_achieve"]:
            analysis["recommendations"].append("以您目前的收支状况，可以达成这个储蓄目标！")
        else:
            analysis["recommendations"].append("建议增加收入或减少支出，以达成储蓄目标。")
            analysis["recommendations"].append(f"每月需要额外储蓄: ¥{analysis['current_performance']['savings_gap']:,.2f}")

        # 计算实际达成时间
        if monthly_avg_net_income > 0:
            actual_months = target_amount / monthly_avg_net_income
            analysis["estimated_time_to_goal"] = {
                "months": actual_months,
                "years": actual_months / 12
            }

        return success_response(data=analysis)

    except Exception as e:
        return error_response(500, f"储蓄目标分析失败: {str(e)}")