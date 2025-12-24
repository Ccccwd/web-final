from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class ImportStatus(str, enum.Enum):
    PENDING = "pending"  # 等待处理
    PROCESSING = "processing"  # 正在处理
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    PARTIAL = "partial"  # 部分成功

class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="导入日志ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    source = Column(String(50), nullable=False, comment="数据来源(wechat/alipay/manual)")
    file_name = Column(String(200), comment="导入文件名")
    file_size = Column(Integer, comment="文件大小(字节)")
    status = Column(Enum(ImportStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=ImportStatus.PENDING, comment="导入状态")

    # 统计信息
    total_records = Column(Integer, default=0, comment="总记录数")
    success_records = Column(Integer, default=0, comment="成功记录数")
    failed_records = Column(Integer, default=0, comment="失败记录数")
    skipped_records = Column(Integer, default=0, comment="跳过记录数")

    # 详细信息
    error_details = Column(JSON, comment="错误详情")
    import_summary = Column(Text, comment="导入摘要")

    # 时间信息
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="开始时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    user = relationship("User", back_populates="import_logs")
    error_records = relationship("ImportErrorRecord", back_populates="import_log", cascade="all, delete-orphan")
    balance_verifications = relationship("BalanceVerification", back_populates="import_log", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ImportLog(id={self.id}, source='{self.source}', status='{self.status}', success={self.success_records}/{self.total_records})>"