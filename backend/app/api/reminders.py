from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.reminder import ReminderType
from app.services.reminder_service import ReminderService
from app.schemas.reminder import (
    ReminderCreate, ReminderUpdate, ReminderResponse, ReminderListResponse,
    ReminderNotification, DailyReminderCheck, ReminderStatistics
)
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_reminder_service(db: Session = Depends(get_db)) -> ReminderService:
    """获取提醒服务实例"""
    return ReminderService(db)

@router.get("/", response_model=ReminderListResponse)
@router.get("", response_model=ReminderListResponse)  # 同时支持不带斜杠的路径
async def get_reminders(
    reminder_type: Optional[ReminderType] = Query(None, description="提醒类型"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """获取提醒列表"""
    try:
        reminders = reminder_service.get_reminders(
            user_id=current_user.id,
            reminder_type=reminder_type,
            is_enabled=is_enabled
        )

        # 转换为响应格式
        reminder_responses = []
        for reminder in reminders:
            reminder_dict = {
                "id": reminder.id,
                "user_id": reminder.user_id,
                "type": reminder.type,
                "title": reminder.title,
                "content": reminder.content,
                "remind_time": reminder.remind_time,
                "remind_day": reminder.remind_day,
                "category_id": reminder.category_id,
                "amount": float(reminder.amount) if reminder.amount else None,
                "is_enabled": reminder.is_enabled,
                "last_reminded_at": reminder.last_reminded_at,
                "created_at": reminder.created_at,
                "updated_at": reminder.updated_at,
            }
            reminder_responses.append(ReminderResponse(**reminder_dict))

        return ReminderListResponse(
            reminders=reminder_responses,
            total=len(reminder_responses)
        )

    except Exception as e:
        return error_response(500, f"获取提醒列表失败: {str(e)}")

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """获取提醒详情"""
    try:
        reminder = reminder_service.get_reminder(current_user.id, reminder_id)

        reminder_dict = {
            "id": reminder.id,
            "user_id": reminder.user_id,
            "type": reminder.type,
            "title": reminder.title,
            "content": reminder.content,
            "remind_time": reminder.remind_time,
            "remind_day": reminder.remind_day,
            "category_id": reminder.category_id,
            "amount": float(reminder.amount) if reminder.amount else None,
            "is_enabled": reminder.is_enabled,
            "last_reminded_at": reminder.last_reminded_at,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
        }

        return ReminderResponse(**reminder_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取提醒详情失败: {str(e)}")

@router.post("/", response_model=ReminderResponse)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """创建提醒"""
    try:
        reminder = reminder_service.create_reminder(
            user_id=current_user.id,
            reminder_data=reminder_data
        )

        reminder_dict = {
            "id": reminder.id,
            "user_id": reminder.user_id,
            "type": reminder.type,
            "title": reminder.title,
            "content": reminder.content,
            "remind_time": reminder.remind_time,
            "remind_day": reminder.remind_day,
            "category_id": reminder.category_id,
            "amount": float(reminder.amount) if reminder.amount else None,
            "is_enabled": reminder.is_enabled,
            "last_reminded_at": reminder.last_reminded_at,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
        }

        return ReminderResponse(**reminder_dict)

    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"创建提醒失败: {str(e)}")

@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """更新提醒"""
    try:
        reminder = reminder_service.update_reminder(
            user_id=current_user.id,
            reminder_id=reminder_id,
            reminder_data=reminder_data
        )

        reminder_dict = {
            "id": reminder.id,
            "user_id": reminder.user_id,
            "type": reminder.type,
            "title": reminder.title,
            "content": reminder.content,
            "remind_time": reminder.remind_time,
            "remind_day": reminder.remind_day,
            "category_id": reminder.category_id,
            "amount": float(reminder.amount) if reminder.amount else None,
            "is_enabled": reminder.is_enabled,
            "last_reminded_at": reminder.last_reminded_at,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
        }

        return ReminderResponse(**reminder_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"更新提醒失败: {str(e)}")

@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """删除提醒"""
    try:
        success = reminder_service.delete_reminder(
            user_id=current_user.id,
            reminder_id=reminder_id
        )

        if success:
            return success_response(message="删除成功")
        else:
            return error_response(500, "删除失败")

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"删除提醒失败: {str(e)}")

@router.get("/statistics/summary")
async def get_reminder_statistics(
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """获取提醒统计信息"""
    try:
        statistics = reminder_service.get_reminder_statistics(current_user.id)

        return success_response(data=statistics)

    except Exception as e:
        return error_response(500, f"获取提醒统计失败: {str(e)}")

@router.post("/check-daily-reminder")
async def check_daily_reminder(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """检查并创建每日记账提醒"""
    try:
        reminder = reminder_service.check_and_create_daily_reminder(current_user.id)

        if reminder:
            return success_response(
                message="已创建每日记账提醒",
                data={
                    "reminder_id": reminder.id,
                    "reminder_title": reminder.title,
                    "reminder_time": reminder.remind_time
                }
            )
        else:
            return success_response(
                message="已存在每日提醒或今日已有记账记录"
            )

    except Exception as e:
        return error_response(500, f"检查每日提醒失败: {str(e)}")

@router.post("/system/process-due-reminders")
async def process_due_reminders(
    background_tasks: BackgroundTasks,
    reminder_service: ReminderService = Depends(get_reminder_service)
):
    """处理到期提醒（系统接口）"""
    try:
        due_reminders = reminder_service.get_due_reminders()

        notifications = []
        for reminder in due_reminders:
            # 构建通知数据
            notification = ReminderNotification(
                id=reminder.id,
                type=reminder.type,
                title=reminder.title or f"{reminder.type.value}提醒",
                content=reminder.content or "您有待处理的提醒",
                user_id=reminder.user_id,
                category_name=reminder.category.name if reminder.category else None
            )
            notifications.append(notification.dict())

            # 更新最后提醒时间
            background_tasks.add_task(reminder_service.update_last_reminded, reminder.id)

        return success_response(
            message=f"处理了 {len(due_reminders)} 个到期提醒",
            data={
                "processed_count": len(due_reminders),
                "notifications": notifications
            }
        )

    except Exception as e:
        return error_response(500, f"处理到期提醒失败: {str(e)}")

@router.get("/templates/daily-reminder")
async def get_daily_reminder_template():
    """获取每日记账提醒模板"""
    template = {
        "type": "daily",
        "title": "每日记账提醒",
        "content": "记得今天记账哦！保持良好的记账习惯有助于财务管理。",
        "remind_time": "20:00:00",
        "is_enabled": True
    }

    return success_response(data=template)

@router.get("/templates/budget-reminder")
async def get_budget_reminder_template():
    """获取预算提醒模板"""
    template = {
        "type": "budget",
        "title": "预算使用提醒",
        "content": "您在某分类的预算使用率已超过80%，请注意控制支出。",
        "is_enabled": True
    }

    return success_response(data=template)

@router.get("/templates/monthly-report")
async def get_monthly_report_template():
    """获取月度报告提醒模板"""
    template = {
        "type": "report",
        "title": "月度财务报告",
        "content": "您的月度财务报告已生成，请查看详细分析。",
        "remind_day": 1,
        "remind_time": "09:00:00",
        "is_enabled": True
    }

    return success_response(data=template)