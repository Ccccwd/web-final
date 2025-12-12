from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base

class StatisticsCache(Base):
    __tablename__ = "statistics_cache"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="缓存ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    stat_type = Column(String(50), nullable=False, comment="统计类型: monthly_summary, category_summary等")
    period = Column(String(20), nullable=False, comment="周期: 2024-12, 2024等")
    data = Column(JSON, nullable=False, comment="统计数据(JSON格式)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'stat_type', 'period', name='uk_stat'),
    )

    def __repr__(self):
        return f"<StatisticsCache(user_id={self.user_id}, stat_type='{self.stat_type}', period='{self.period}')>"