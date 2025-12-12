from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Numeric, Text, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class ReminderType(str, enum.Enum):
    DAILY = "daily"
    BUDGET = "budget"
    RECURRING = "recurring"
    REPORT = "report"

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="提醒ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    type = Column(Enum(ReminderType), nullable=False, comment="提醒类型: 每日记账/预算预警/循环提醒/分析报告")
    title = Column(String(100), comment="标题")
    content = Column(Text, comment="内容")
    remind_time = Column(Time, comment="提醒时间")
    remind_day = Column(Integer, comment="每月第几天(循环提醒)")
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), comment="关联分类ID(预算提醒)")
    amount = Column(Numeric(10, 2), comment="固定金额提醒")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    last_reminded_at = Column(DateTime(timezone=True), comment="最后提醒时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="reminders")
    category = relationship("Category")

    def __repr__(self):
        return f"<Reminder(id={self.id}, type='{self.type}', title='{self.title}', is_enabled={self.is_enabled})>"