from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, ForeignKey, JSON, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class TransactionSource(str, enum.Enum):
    MANUAL = "manual"  # 手动输入
    WECHAT = "wechat"  # 微信导入
    IMPORT = "import"  # 其他导入

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="交易ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    type = Column(Enum(TransactionType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment="交易类型: 收入/支出/转账")
    amount = Column(Numeric(10, 2), nullable=False, comment="金额")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, comment="分类ID")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, comment="账户ID")
    to_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), comment="转入账户ID(转账时使用)")
    transaction_date = Column(DateTime(timezone=True), nullable=False, comment="交易时间")
    remark = Column(String(200), comment="备注")
    images = Column(JSON, comment="图片URL数组")
    tags = Column(String(200), comment="标签(逗号分隔)")
    location = Column(String(100), comment="地点")

    # 微信导入相关字段
    source = Column(Enum(TransactionSource, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=TransactionSource.MANUAL, comment="数据来源")
    wechat_transaction_id = Column(String(100), unique=True, comment="微信交易ID(防止重复导入)")
    original_category = Column(String(100), comment="原始分类(如微信分类)")
    merchant_name = Column(String(200), comment="商户名称")
    pay_method = Column(String(50), comment="支付方式")
    is_repeated = Column(Boolean, default=False, comment="是否重复交易")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    account = relationship("Account", foreign_keys=[account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
    balance_history = relationship("AccountBalanceHistory", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.type}', amount={self.amount}, category='{self.category.name if self.category else None}')>"