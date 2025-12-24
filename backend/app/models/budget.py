from sqlalchemy import Column, Integer, Boolean, DateTime, Enum, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class PeriodType(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="预算ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), comment="分类ID(NULL表示总预算)")
    amount = Column(Numeric(10, 2), nullable=False, comment="预算金额")
    period_type = Column(Enum(PeriodType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment="周期类型: 月度/年度")
    year = Column(Integer, nullable=False, comment="年份")
    month = Column(Integer, comment="月份(月度预算时使用)")
    alert_threshold = Column(Integer, default=80, comment="预警阈值(百分比)")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', 'year', 'month', name='uk_budget'),
    )

    def __repr__(self):
        return f"<Budget(id={self.id}, amount={self.amount}, period_type='{self.period_type}', year={self.year}, month={self.month})>"