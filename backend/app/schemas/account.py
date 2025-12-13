from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from app.models.account import AccountType

class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="账户名称")
    type: AccountType = Field(..., description="账户类型")
    initial_balance: Decimal = Field(0, ge=0, description="初始余额")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    description: Optional[str] = Field(None, max_length=200, description="描述")

class AccountCreate(AccountBase):
    is_default: bool = Field(False, description="是否默认账户")

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="账户名称")
    type: Optional[AccountType] = Field(None, description="账户类型")
    initial_balance: Optional[Decimal] = Field(None, ge=0, description="初始余额")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    is_default: Optional[bool] = Field(None, description="是否默认账户")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, max_length=200, description="描述")

class AccountResponse(AccountBase):
    id: int = Field(..., description="账户ID")
    user_id: int = Field(..., description="用户ID")
    balance: Decimal = Field(..., description="当前余额")
    is_default: bool = Field(..., description="是否默认账户")
    is_enabled: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 统计信息
    transaction_count: Optional[int] = Field(None, description="交易次数")
    total_income: Optional[Decimal] = Field(None, description="总收入")
    total_expense: Optional[Decimal] = Field(None, description="总支出")

    class Config:
        from_attributes = True

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse] = Field(..., description="账户列表")
    total: int = Field(..., description="总数量")

class AccountSummary(BaseModel):
    """账户统计摘要"""
    total_balance: Decimal = Field(..., description="总余额")
    total_income: Decimal = Field(..., description="总收入")
    total_expense: Decimal = Field(..., description="总支出")
    account_count: int = Field(..., description="账户数量")

class AccountTransfer(BaseModel):
    """账户转账请求"""
    from_account_id: int = Field(..., description="转出账户ID")
    to_account_id: int = Field(..., description="转入账户ID")
    amount: Decimal = Field(..., gt=0, description="转账金额")
    remark: Optional[str] = Field(None, max_length=200, description="备注")
    transaction_date: Optional[datetime] = Field(None, description="交易时间")

class AccountWithStats(AccountResponse):
    """带统计信息的账户"""
    recent_transactions: Optional[int] = Field(None, description="最近交易次数")
    avg_transaction: Optional[Decimal] = Field(None, description="平均交易金额")