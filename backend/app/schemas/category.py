from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.category import CategoryType

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    type: CategoryType = Field(..., description="分类类型")
    icon: Optional[str] = Field(None, max_length=50, description="图标(emoji)")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, ge=0, description="排序")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")

class CategoryResponse(CategoryBase):
    id: int = Field(..., description="分类ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    is_system: bool = Field(..., description="是否系统预设分类")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 统计信息
    transaction_count: Optional[int] = Field(None, description="交易次数")
    total_amount: Optional[float] = Field(None, description="总金额")

    # 子分类
    children: Optional[List['CategoryResponse']] = Field(None, description="子分类列表")

    class Config:
        from_attributes = True

class CategoryTreeResponse(CategoryResponse):
    """分类树响应格式"""
    pass

class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse] = Field(..., description="分类列表")
    total: int = Field(..., description="总数量")

class CategorySummary(BaseModel):
    """分类统计摘要"""
    type: CategoryType
    count: int
    total_amount: float

class CategoryWithStats(CategoryResponse):
    """带统计信息的分类"""
    expense_count: Optional[int] = Field(None, description="支出交易次数")
    expense_amount: Optional[float] = Field(None, description="支出总额")
    income_count: Optional[int] = Field(None, description="收入交易次数")
    income_amount: Optional[float] = Field(None, description="收入总额")