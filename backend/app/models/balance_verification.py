from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base

class BalanceVerification(Base):
    """余额校验表"""
    __tablename__ = "balance_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="校验ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    import_log_id = Column(Integer, ForeignKey("import_logs.id", ondelete="SET NULL"), comment="导入日志ID")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, comment="账户ID")

    # 校验数据
    expected_balance = Column(Float, nullable=False, comment="预期余额")
    actual_balance = Column(Float, nullable=False, comment="实际余额")
    difference = Column(Float, nullable=False, comment="差异")
    is_valid = Column(Boolean, nullable=False, comment="是否通过校验")
    tolerance = Column(Float, default=0.01, comment="容差范围")

    # 详细信息
    verification_method = Column(String(50), nullable=False, comment="校验方法")
    verification_details = Column(JSON, comment="校验详情")
    mismatch_details = Column(JSON, comment="不匹配详情")
    correction_suggestions = Column(Text, comment="修正建议")

    # 状态信息
    status = Column(String(20), default="pending", comment="状态：pending/resolved/ignored")
    resolved_at = Column(DateTime(timezone=True), comment="解决时间")
    resolved_by = Column(String(50), comment="解决人")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User")
    account = relationship("Account")
    import_log = relationship("ImportLog")

    def __repr__(self):
        return f"<BalanceVerification(id={self.id}, account_id={self.account_id}, valid={self.is_valid})>"

class UserPreference(Base):
    """用户偏好表"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="偏好ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, comment="用户ID")

    # 导入设置
    auto_categorize_enabled = Column(Boolean, default=True, comment="是否启用自动分类")
    balance_verification_enabled = Column(Boolean, default=True, comment="是否启用余额校验")
    duplicate_threshold_days = Column(Integer, default=7, comment="重复记录阈值天数")
    learning_enabled = Column(Boolean, default=True, comment="是否启用学习")

    # 分类设置
    confidence_threshold = Column(Float, default=0.7, comment="置信度阈值")
    auto_accept_confident = Column(Boolean, default=True, comment="是否自动接受高置信度建议")
    custom_category_mappings = Column(JSON, comment="自定义分类映射")

    # 通知设置
    notification_preferences = Column(JSON, comment="通知偏好")
    error_notification_enabled = Column(Boolean, default=True, comment="是否启用错误通知")
    success_notification_enabled = Column(Boolean, default=False, comment="是否启用成功通知")

    # 其他设置
    preferred_import_time = Column(String(20), comment="偏好导入时间")
    max_file_size = Column(Integer, default=10485760, comment="最大文件大小(bytes)")
    backup_enabled = Column(Boolean, default=True, comment="是否启用备份")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id})>"