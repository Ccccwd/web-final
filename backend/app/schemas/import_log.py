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
    suggested_fix: Optional[str] = Field(None, description="建议的修复方法")
    can_retry: bool = Field(default=False, description="是否可以重试")

class ImportRetryRequest(BaseModel):
    """导入重试请求"""
    error_record_ids: List[int] = Field(..., description="要重试的错误记录ID")
    corrections: Optional[Dict[int, Dict[str, Any]]] = Field(None, description="修正数据")
    retry_all_fixable: bool = Field(default=False, description="是否重试所有可修复的记录")

class ImportStatistics(BaseModel):
    """导入统计"""
    total_imports: int = Field(..., description="总导入次数")
    successful_imports: int = Field(..., description="成功导入次数")
    failed_imports: int = Field(..., description="失败导入次数")
    total_records: int = Field(..., description="总记录数")
    success_records: int = Field(..., description="成功记录数")
    failed_records: int = Field(..., description="失败记录数")
    average_success_rate: float = Field(..., description="平均成功率")
    most_common_errors: List[Dict[str, Any]] = Field(default=[], description="最常见错误")
    recent_imports: List[ImportLogResponse] = Field(default=[], description="最近导入记录")

class WechatBillRecord(BaseModel):
    """微信账单记录"""
    transaction_time: datetime = Field(..., description="交易时间")
    transaction_type: str = Field(..., description="交易类型：收入/支出")
    amount: float = Field(..., description="金额")
    merchant_name: Optional[str] = Field(None, description="商户名称")
    category: Optional[str] = Field(None, description="微信分类")
    payment_method: Optional[str] = Field(None, description="支付方式")
    remark: Optional[str] = Field(None, description="备注")
    transaction_id: Optional[str] = Field(None, description="交易单号")
    out_trade_no: Optional[str] = Field(None, description="商户订单号")

class WechatImportPreview(BaseModel):
    """微信导入预览"""
    valid: bool = Field(..., description="文件是否有效")
    total_records: int = Field(..., description="总记录数")
    preview_records: List[WechatBillRecord] = Field(..., description="预览记录")
    summary: Optional[Dict[str, Any]] = Field(None, description="汇总信息")
    warnings: List[str] = Field(default=[], description="警告信息")
    errors: List[str] = Field(default=[], description="错误信息")
    suggested_categories: Dict[str, int] = Field(default={}, description="建议的分类映射")
    potential_duplicates: int = Field(default=0, description="潜在重复记录数")

class CategorySuggestion(BaseModel):
    """分类建议"""
    merchant_name: str = Field(..., description="商户名称")
    suggested_category_id: int = Field(..., description="建议的分类ID")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    based_on: str = Field(..., description="基于的数据：user_behavior/rules/machine_learning")
    frequency: int = Field(default=1, description="出现次数")
    last_updated: datetime

class BalanceVerification(BaseModel):
    """余额校验"""
    account_id: int = Field(..., description="账户ID")
    expected_balance: float = Field(..., description="预期余额")
    actual_balance: float = Field(..., description="实际余额")
    difference: float = Field(..., description="差异")
    verification_time: datetime = Field(..., description="校验时间")
    is_valid: bool = Field(..., description="是否通过验证")
    mismatch_details: Optional[List[Dict[str, Any]]] = Field(None, description="不匹配详情")

class SmartCategorizationResult(BaseModel):
    """智能分类结果"""
    original_category: str = Field(..., description="原始分类")
    suggested_category_id: int = Field(..., description="建议分类ID")
    suggested_category_name: str = Field(..., description="建议分类名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    reason: str = Field(..., description="分类原因")
    similar_transactions: int = Field(default=0, description="相似交易数量")
    user_feedback: Optional[bool] = Field(None, description="用户反馈")

class LearningRequest(BaseModel):
    """学习请求"""
    transaction_id: int = Field(..., description="交易ID")
    correct_category_id: int = Field(..., description="正确分类ID")
    original_suggestion_id: Optional[int] = Field(None, description="原始建议ID")
    feedback_type: str = Field(..., description="反馈类型：confirm/correct")
    user_notes: Optional[str] = Field(None, description="用户备注")

class LearningBatchRequest(BaseModel):
    """批量学习请求"""
    feedback_data: List[LearningRequest] = Field(..., description="反馈数据列表")
    update_model: bool = Field(default=True, description="是否更新模型")

class UserPreference(BaseModel):
    """用户偏好"""
    user_id: int
    auto_categorize_enabled: bool = Field(default=True)
    balance_verification_enabled: bool = Field(default=True)
    duplicate_threshold_days: int = Field(default=7)
    learning_enabled: bool = Field(default=True)
    custom_category_mappings: Dict[str, int] = Field(default={})
    notification_preferences: Dict[str, bool] = Field(default={})