from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.import_log import ImportStatus

class ImportLogBase(BaseModel):
    source: str = Field(..., description="数据来源")
    file_name: Optional[str] = Field(None, max_length=200, description="导入文件名")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小(字节)")
    total_records: int = Field(0, ge=0, description="总记录数")
    success_records: int = Field(0, ge=0, description="成功记录数")
    failed_records: int = Field(0, ge=0, description="失败记录数")
    skipped_records: int = Field(0, ge=0, description="跳过记录数")

class ImportLogCreate(ImportLogBase):
    error_details: Optional[List[Dict[str, Any]]] = Field(None, description="错误详情")
    import_summary: Optional[str] = Field(None, description="导入摘要")

class ImportLogUpdate(BaseModel):
    status: Optional[ImportStatus] = Field(None, description="导入状态")
    total_records: Optional[int] = Field(None, ge=0, description="总记录数")
    success_records: Optional[int] = Field(None, ge=0, description="成功记录数")
    failed_records: Optional[int] = Field(None, ge=0, description="失败记录数")
    skipped_records: Optional[int] = Field(None, ge=0, description="跳过记录数")
    error_details: Optional[List[Dict[str, Any]]] = Field(None, description="错误详情")
    import_summary: Optional[str] = Field(None, description="导入摘要")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

class ImportLogResponse(ImportLogBase):
    id: int = Field(..., description="导入日志ID")
    user_id: int = Field(..., description="用户ID")
    status: ImportStatus = Field(..., description="导入状态")
    error_details: Optional[List[Dict[str, Any]]] = Field(None, description="错误详情")
    import_summary: Optional[str] = Field(None, description="导入摘要")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

class ImportLogListResponse(BaseModel):
    import_logs: List[ImportLogResponse] = Field(..., description="导入日志列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

class ImportPreview(BaseModel):
    filename: str = Field(..., description="文件名")
    total_records: int = Field(..., description="总记录数")
    preview_data: List[Dict[str, Any]] = Field(..., description="预览数据")
    detected_format: str = Field(..., description="检测到的格式")
    potential_duplicates: int = Field(..., description="潜在重复记录数")

class ImportRequest(BaseModel):
    file_content: str = Field(..., description="CSV文件内容(Base64编码)")
    filename: str = Field(..., description="文件名")
    source: str = Field(..., description="数据来源")
    skip_duplicates: bool = Field(True, description="是否跳过重复记录")
    auto_categorize: bool = Field(True, description="是否自动分类")
    default_account_id: Optional[int] = Field(None, description="默认账户ID")

class ImportResponse(BaseModel):
    import_log_id: int = Field(..., description="导入日志ID")
    status: ImportStatus = Field(..., description="导入状态")
    message: str = Field(..., description="状态消息")
    total_records: int = Field(..., description="总记录数")
    processed_records: int = Field(..., description="已处理记录数")

class ImportErrorDetail(BaseModel):
    row_number: int = Field(..., description="行号")
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误消息")
    row_data: Dict[str, Any] = Field(..., description="行数据")