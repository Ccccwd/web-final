from pydantic import BaseModel, Field
from typing import Optional
from datetime import time, datetime
from decimal import Decimal
from app.models.reminder import ReminderType

class ReminderBase(BaseModel):
    """提醒基础模型"""
    type: ReminderType = Field(..., description="提醒类型")
    title: Optional[str] = Field(None, max_length=100, description="标题")
    content: Optional[str] = Field(None, description="内容")
    remind_time: Optional[time] = Field(None, description="提醒时间")
    remind_day: Optional[int] = Field(None, ge=1, le=31, description="每月第几天(循环提醒)")
    category_id: Optional[int] = Field(None, description="关联分类ID(预算提醒)")
    amount: Optional[Decimal] = Field(None, ge=0, description="固定金额提醒")
    is_enabled: Optional[bool] = Field(True, description="是否启用")

class ReminderCreate(ReminderBase):
    """创建提醒"""
    pass

class ReminderUpdate(BaseModel):
    """更新提醒"""
    title: Optional[str] = Field(None, max_length=100, description="标题")
    content: Optional[str] = Field(None, description="内容")
    remind_time: Optional[time] = Field(None, description="提醒时间")
    remind_day: Optional[int] = Field(None, ge=1, le=31, description="每月第几天(循环提醒)")
    category_id: Optional[int] = Field(None, description="关联分类ID(预算提醒)")
    amount: Optional[Decimal] = Field(None, ge=0, description="固定金额提醒")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

class ReminderResponse(ReminderBase):
    """提醒响应模型"""
    id: int
    user_id: int
    last_reminded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReminderListResponse(BaseModel):
    """提醒列表响应"""
    reminders: list[ReminderResponse]
    total: int

class ReminderNotification(BaseModel):
    """提醒通知"""
    id: int
    type: ReminderType
    title: str
    content: str
    user_id: int
    category_name: Optional[str] = None

class DailyReminderCheck(BaseModel):
    """每日提醒检查响应"""
    has_transactions_today: bool
    reminder_created: bool
    reminder_id: Optional[int] = None

class ReminderStatistics(BaseModel):
    """提醒统计"""
    total_reminders: int
    enabled_reminders: int
    type_stats: dict[str, int]