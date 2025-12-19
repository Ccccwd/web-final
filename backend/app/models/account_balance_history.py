from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class BalanceChangeType(str, enum.Enum):
    INITIAL = "initial"          # 初始余额
    TRANSACTION = "transaction"  # 交易引起的余额变化
    TRANSFER_OUT = "transfer_out" # 转账出
    TRANSFER_IN = "transfer_in"   # 转账入
    ADJUSTMENT = "adjustment"     # 手动调整
    CORRECTION = "correction"     # 错误修正

class AccountBalanceHistory(Base):
    __tablename__ = "account_balance_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="历史记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, comment="账户ID")
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), comment="关联交易ID")

    # 余额变化信息
    change_type = Column(Enum(BalanceChangeType), nullable=False, comment="变化类型")
    amount_before = Column(Numeric(10, 2), nullable=False, comment="变化前余额")
    amount_after = Column(Numeric(10, 2), nullable=False, comment="变化后余额")
    change_amount = Column(Numeric(10, 2), nullable=False, comment="变化金额")

    # 备注信息
    description = Column(String(200), comment="变化描述")
    reference_id = Column(String(100), comment="参考ID（如导入批次号）")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    user = relationship("User", back_populates="balance_history")
    account = relationship("Account", back_populates="balance_history")
    transaction = relationship("Transaction", back_populates="balance_history")

    def __repr__(self):
        return f"<AccountBalanceHistory(id={self.id}, account_id={self.account_id}, change_type='{self.change_type}', change_amount={self.change_amount})>"