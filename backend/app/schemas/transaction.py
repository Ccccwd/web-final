from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from app.models.transaction import TransactionType, TransactionSource

class TransactionBase(BaseModel):
    type: TransactionType = Field(..., description="交易类型")
    amount: Decimal = Field(..., gt=0, description="金额")
    category_id: int = Field(..., gt=0, description="分类ID")
    account_id: int = Field(..., gt=0, description="账户ID")
    to_account_id: Optional[int] = Field(None, description="转入账户ID(转账时使用)")
    transaction_date: datetime = Field(..., description="交易时间")
    remark: Optional[str] = Field(None, max_length=200, description="备注")
    images: Optional[List[str]] = Field(None, description="图片URL数组")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")
    location: Optional[str] = Field(None, max_length=100, description="地点")

class TransactionCreate(TransactionBase):
    # 微信导入专用字段
    source: Optional[TransactionSource] = Field(TransactionSource.MANUAL, description="数据来源")
    wechat_transaction_id: Optional[str] = Field(None, max_length=100, description="微信交易ID")
    original_category: Optional[str] = Field(None, max_length=100, description="原始分类")
    merchant_name: Optional[str] = Field(None, max_length=200, description="商户名称")
    pay_method: Optional[str] = Field(None, max_length=50, description="支付方式")

class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = Field(None, description="交易类型")
    amount: Optional[Decimal] = Field(None, gt=0, description="金额")
    category_id: Optional[int] = Field(None, gt=0, description="分类ID")
    account_id: Optional[int] = Field(None, gt=0, description="账户ID")
    to_account_id: Optional[int] = Field(None, description="转入账户ID(转账时使用)")
    transaction_date: Optional[datetime] = Field(None, description="交易时间")
    remark: Optional[str] = Field(None, max_length=200, description="备注")
    images: Optional[List[str]] = Field(None, description="图片URL数组")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")
    location: Optional[str] = Field(None, max_length=100, description="地点")

class TransactionResponse(TransactionBase):
    id: int = Field(..., description="交易ID")
    user_id: int = Field(..., description="用户ID")
    source: TransactionSource = Field(..., description="数据来源")
    wechat_transaction_id: Optional[str] = Field(None, description="微信交易ID")
    original_category: Optional[str] = Field(None, description="原始分类")
    merchant_name: Optional[str] = Field(None, description="商户名称")
    pay_method: Optional[str] = Field(None, description="支付方式")
    is_repeated: bool = Field(..., description="是否重复交易")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 关联数据
    category_name: Optional[str] = Field(None, description="分类名称")
    account_name: Optional[str] = Field(None, description="账户名称")
    to_account_name: Optional[str] = Field(None, description="目标账户名称")
    category_icon: Optional[str] = Field(None, description="分类图标")
    category_color: Optional[str] = Field(None, description="分类颜色")

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse] = Field(..., description="交易记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

class TransactionFilter(BaseModel):
    type: Optional[TransactionType] = Field(None, description="交易类型")
    category_id: Optional[int] = Field(None, description="分类ID")
    account_id: Optional[int] = Field(None, description="账户ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="最小金额")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="最大金额")
    source: Optional[TransactionSource] = Field(None, description="数据来源")
    is_repeated: Optional[bool] = Field(None, description="是否重复交易")

class TransactionSummary(BaseModel):
    total_income: Decimal = Field(..., description="总收入")
    total_expense: Decimal = Field(..., description="总支出")
    total_transfer: Decimal = Field(..., description="总转账")
    net_income: Decimal = Field(..., description="净收入")
    transaction_count: int = Field(..., description="交易次数")