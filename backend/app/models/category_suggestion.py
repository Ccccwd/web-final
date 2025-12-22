from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base

class CategorySuggestion(Base):
    """分类建议表"""
    __tablename__ = "category_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="建议ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    merchant_name = Column(String(200), nullable=False, comment="商户名称")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, comment="建议分类ID")

    # 置信度和统计
    confidence = Column(Float, nullable=False, comment="置信度(0-1)")
    frequency = Column(Integer, default=1, comment="出现次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    failure_count = Column(Integer, default=0, comment="失败次数")

    # 学习信息
    based_on = Column(String(50), nullable=False, comment="基于：user_behavior/rules/machine_learning")
    last_confirmed_at = Column(DateTime(timezone=True), comment="最后确认时间")
    user_feedback = Column(Boolean, comment="用户反馈：True正确/False错误")
    user_notes = Column(Text, comment="用户备注")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User")
    category = relationship("Category")

    def __repr__(self):
        return f"<CategorySuggestion(id={self.id}, merchant='{self.merchant_name}', confidence={self.confidence})>"

class LearningRecord(Base):
    """学习记录表"""
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="学习记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, comment="交易ID")
    suggestion_id = Column(Integer, ForeignKey("category_suggestions.id", ondelete="SET NULL"), comment="建议ID")

    # 学习信息
    original_category_id = Column(Integer, comment="原始分类ID")
    correct_category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, comment="正确分类ID")
    feedback_type = Column(String(20), nullable=False, comment="反馈类型：confirm/correct")
    confidence_before = Column(Float, comment="学习前置信度")
    confidence_after = Column(Float, comment="学习后置信度")

    # 模型信息
    model_version = Column(String(20), comment="模型版本")
    learning_algorithm = Column(String(50), comment="学习算法")
    learning_accuracy = Column(Float, comment="学习准确度")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    user = relationship("User")
    transaction = relationship("Transaction")
    correct_category = relationship("Category", foreign_keys=[correct_category_id])
    suggestion = relationship("CategorySuggestion")

    def __repr__(self):
        return f"<LearningRecord(id={self.id}, type='{self.feedback_type}', accuracy={self.learning_accuracy})>"