from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class AccountType(str, enum.Enum):
    CASH = "cash"
    BANK = "bank"
    WECHAT = "wechat"
    ALIPAY = "alipay"
    MEAL_CARD = "meal_card"
    CREDIT_CARD = "credit_card"
    OTHER = "other"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="账户ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    name = Column(String(50), nullable=False, comment="账户名称")
    type = Column(Enum(AccountType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment="账户类型")
    balance = Column(Numeric(10, 2), default=0, comment="当前余额")
    initial_balance = Column(Numeric(10, 2), default=0, comment="初始余额")
    icon = Column(String(50), comment="图标")
    color = Column(String(20), comment="颜色")
    is_default = Column(Boolean, default=False, comment="是否默认账户")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    description = Column(String(200), comment="描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.account_id", back_populates="account")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")
    balance_history = relationship("AccountBalanceHistory", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.type}', balance={self.balance})>"