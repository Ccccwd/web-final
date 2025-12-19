from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
from datetime import datetime, time, date
from decimal import Decimal

from app.models.reminder import Reminder, ReminderType
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.core.exceptions import ValidationError, NotFoundError

class ReminderService:
    def __init__(self, db: Session):
        self.db = db

    def create_reminder(self, user_id: int, reminder_data: ReminderCreate) -> Reminder:
        """
        创建提醒

        Args:
            user_id: 用户ID
            reminder_data: 提醒数据

        Returns:
            创建的提醒
        """
        # 验证提醒类型和必填字段
        if reminder_data.type == ReminderType.DAILY and not reminder_data.remind_time:
            raise ValidationError("每日记账提醒必须设置提醒时间")

        if reminder_data.type == ReminderType.BUDGET:
            if not reminder_data.category_id:
                raise ValidationError("预算提醒必须指定分类")

        if reminder_data.type == ReminderType.RECURRING:
            if not reminder_data.remind_day or not reminder_data.remind_time:
                raise ValidationError("循环提醒必须设置提醒日期和时间")

        # 创建提醒
        reminder = Reminder(
            user_id=user_id,
            **reminder_data.model_dump(exclude_unset=True)
        )

        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def get_reminder(self, user_id: int, reminder_id: int) -> Reminder:
        """
        获取提醒详情

        Args:
            user_id: 用户ID
            reminder_id: 提醒ID

        Returns:
            提醒详情
        """
        reminder = self.db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()

        if not reminder:
            raise NotFoundError("提醒不存在")

        return reminder

    def get_reminders(
        self,
        user_id: int,
        reminder_type: Optional[ReminderType] = None,
        is_enabled: Optional[bool] = None
    ) -> List[Reminder]:
        """
        获取提醒列表

        Args:
            user_id: 用户ID
            reminder_type: 提醒类型
            is_enabled: 是否启用

        Returns:
            提醒列表
        """
        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)

        if reminder_type:
            query = query.filter(Reminder.type == reminder_type)

        if is_enabled is not None:
            query = query.filter(Reminder.is_enabled == is_enabled)

        return query.order_by(Reminder.type, Reminder.remind_time).all()

    def update_reminder(
        self,
        user_id: int,
        reminder_id: int,
        reminder_data: ReminderUpdate
    ) -> Reminder:
        """
        更新提醒

        Args:
            user_id: 用户ID
            reminder_id: 提醒ID
            reminder_data: 更新数据

        Returns:
            更新后的提醒
        """
        reminder = self.get_reminder(user_id, reminder_id)

        # 验证更新数据
        update_data = reminder_data.model_dump(exclude_unset=True)

        if reminder_data.type == ReminderType.DAILY and not reminder_data.remind_time:
            if not reminder.remind_time:
                raise ValidationError("每日记账提醒必须设置提醒时间")

        if reminder_data.type == ReminderType.BUDGET:
            if reminder_data.category_id is None and not reminder.category_id:
                raise ValidationError("预算提醒必须指定分类")

        if reminder_data.type == ReminderType.RECURRING:
            if (reminder_data.remind_day is None and not reminder.remind_day) or \
               (reminder_data.remind_time is None and not reminder.remind_time):
                raise ValidationError("循环提醒必须设置提醒日期和时间")

        # 更新字段
        for field, value in update_data.items():
            setattr(reminder, field, value)

        self.db.commit()
        self.db.refresh(reminder)

        return reminder

    def delete_reminder(self, user_id: int, reminder_id: int) -> bool:
        """
        删除提醒

        Args:
            user_id: 用户ID
            reminder_id: 提醒ID

        Returns:
            是否删除成功
        """
        reminder = self.get_reminder(user_id, reminder_id)

        self.db.delete(reminder)
        self.db.commit()

        return True

    def get_due_reminders(self) -> List[Reminder]:
        """
        获取到期的提醒（系统调用）

        Returns:
            到期的提醒列表
        """
        now = datetime.now()
        current_time = now.time()
        current_date = now.date()

        # 查询到期的提醒
        reminders = self.db.query(Reminder).filter(
            Reminder.is_enabled == True
        ).all()

        due_reminders = []

        for reminder in reminders:
            should_remind = False

            if reminder.type == ReminderType.DAILY:
                # 每日提醒：检查时间
                if reminder.remind_time:
                    # 简化处理：检查是否在提醒时间后的1小时内
                    target_time = reminder.remind_time
                    time_diff = abs((now.hour - target_time.hour) * 60 + (now.minute - target_time.minute))
                    if time_diff <= 60:  # 1小时内
                        # 检查今天是否已经提醒过
                        if not self._was_reminded_today(reminder, current_date):
                            should_remind = True

            elif reminder.type == ReminderType.BUDGET:
                # 预算提醒：检查预算使用情况
                if self._should_trigger_budget_reminder(reminder):
                    should_remind = True

            elif reminder.type == ReminderType.RECURRING:
                # 循环提醒：检查日期
                if reminder.remind_day == current_date.day and reminder.remind_time:
                    target_time = reminder.remind_time
                    time_diff = abs((now.hour - target_time.hour) * 60 + (now.minute - target_time.minute))
                    if time_diff <= 60:  # 1小时内
                        if not self._was_reminded_today(reminder, current_date):
                            should_remind = True

            elif reminder.type == ReminderType.REPORT:
                # 分析报告提醒：每月1号
                if current_date.day == 1:
                    if reminder.remind_time:
                        target_time = reminder.remind_time
                        time_diff = abs((now.hour - target_time.hour) * 60 + (now.minute - target_time.minute))
                        if time_diff <= 60:  # 1小时内
                            if not self._was_reminded_today(reminder, current_date):
                                should_remind = True

            if should_remind:
                due_reminders.append(reminder)

        return due_reminders

    def update_last_reminded(self, reminder_id: int) -> None:
        """
        更新最后提醒时间

        Args:
            reminder_id: 提醒ID
        """
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.last_reminded_at = datetime.now()
            self.db.commit()

    def check_and_create_daily_reminder(self, user_id: int) -> Optional[Reminder]:
        """
        检查并创建每日记账提醒（如果用户没有今日的记账记录）

        Args:
            user_id: 用户ID

        Returns:
            创建的提醒或None
        """
        # 检查用户今天是否有记账记录
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        transaction_count = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= today_start,
            Transaction.transaction_date <= today_end
        ).count()

        # 如果今天没有记账记录且用户没有每日提醒，创建一个
        if transaction_count == 0:
            existing_daily_reminder = self.db.query(Reminder).filter(
                Reminder.user_id == user_id,
                Reminder.type == ReminderType.DAILY,
                Reminder.is_enabled == True
            ).first()

            if not existing_daily_reminder:
                # 创建默认的每日记账提醒
                reminder_data = ReminderCreate(
                    type=ReminderType.DAILY,
                    title="每日记账提醒",
                    content="记得今天记账哦！保持良好的记账习惯有助于财务管理。",
                    remind_time=time(20, 0)  # 晚上8点提醒
                )
                return self.create_reminder(user_id, reminder_data)

        return None

    def get_reminder_statistics(self, user_id: int) -> dict:
        """
        获取提醒统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        reminders = self.get_reminders(user_id)

        stats = {
            "total_reminders": len(reminders),
            "enabled_reminders": len([r for r in reminders if r.is_enabled]),
            "type_stats": {}
        }

        for reminder_type in ReminderType:
            type_count = len([r for r in reminders if r.type == reminder_type])
            stats["type_stats"][reminder_type.value] = type_count

        return stats

    def _was_reminded_today(self, reminder: Reminder, current_date: date) -> bool:
        """
        检查今天是否已经提醒过

        Args:
            reminder: 提醒对象
            current_date: 当前日期

        Returns:
            是否今天已经提醒过
        """
        if not reminder.last_reminded_at:
            return False

        return reminder.last_reminded_at.date() == current_date

    def _should_trigger_budget_reminder(self, reminder: Reminder) -> bool:
        """
        检查是否应该触发预算提醒

        Args:
            reminder: 预算提醒

        Returns:
            是否应该触发提醒
        """
        if not reminder.category_id:
            return False

        # 获取当前月份该分类的预算
        current_month = datetime.now().month
        current_year = datetime.now().year

        budget = self.db.query(Budget).filter(
            Budget.user_id == reminder.user_id,
            Budget.category_id == reminder.category_id,
            func.extract('month', Budget.start_date) == current_month,
            func.extract('year', Budget.start_date) == current_year,
            Budget.is_active == True
        ).first()

        if not budget:
            return False

        # 计算当前支出
        month_start = datetime(current_year, current_month, 1)
        current_expense = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == reminder.user_id,
            Transaction.category_id == reminder.category_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= datetime.now()
        ).scalar() or Decimal('0')

        # 计算使用率
        usage_rate = float(current_expense) / float(budget.amount)

        # 使用率超过80%时提醒
        return usage_rate >= 0.8 and not self._was_reminded_today(reminder, datetime.now().date())