from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base

class ImportErrorRecord(Base):
    """导入错误记录表"""
    __tablename__ = "import_error_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="错误记录ID")
    import_log_id = Column(Integer, ForeignKey("import_logs.id", ondelete="CASCADE"), nullable=False, comment="导入日志ID")

    # 错误信息
    row_number = Column(Integer, nullable=False, comment="行号")
    error_type = Column(String(50), nullable=False, comment="错误类型")
    error_message = Column(Text, nullable=False, comment="错误消息")
    raw_data = Column(JSON, comment="原始数据")
    suggested_fix = Column(Text, comment="建议的修复方法")
    can_retry = Column(Boolean, default=False, comment="是否可以重试")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 处理状态
    status = Column(String(20), default="pending", comment="状态：pending/resolved/ignored")
    resolved_at = Column(DateTime(timezone=True), comment="解决时间")
    resolution_method = Column(String(50), comment="解决方法")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    import_log = relationship("ImportLog", back_populates="error_records")

    def __repr__(self):
        return f"<ImportErrorRecord(id={self.id}, type='{self.error_type}', row={self.row_number})>"