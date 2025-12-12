from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class CategoryType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(50), nullable=False, comment="分类名称")
    type = Column(Enum(CategoryType), nullable=False, comment="分类类型: 收入/支出")
    icon = Column(String(50), comment="图标(emoji)")
    color = Column(String(20), comment="颜色")
    parent_id = Column(Integer, comment="父分类ID(支持二级分类)")
    sort_order = Column(Integer, default=0, comment="排序")
    is_system = Column(Boolean, default=False, comment="是否系统预设分类")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
    children = relationship("Category", remote_side=[id])

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}')>"