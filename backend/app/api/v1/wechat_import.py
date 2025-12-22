from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json
import io
import pandas as pd
from datetime import datetime

from app.config.database import get_db
from app.models.user import User
from app.models.import_log import ImportLog, ImportStatus
from app.models.transaction import Transaction, TransactionType
from app.schemas.import_log import (
    ImportLogResponse, ImportErrorDetail, ImportRetryRequest,
    ImportStatistics, WechatBillRecord, ImportPreview
)
from app.services.smart_categorization_service import SmartCategorizationService
from app.services.import_error_analysis_service import ImportErrorAnalysisService
from app.services.balance_verification_service import BalanceVerificationService
from app.core.auth import get_current_user
from app.core.exceptions import NotFoundError, ValidationError
from app.wechat_parser import parse_wechat_csv

router = APIRouter(prefix="/wechat", tags=["wechat-import"])

@router.post("/upload", response_model=Dict)
async def upload_wechat_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传微信账单文件
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV格式的微信账单文件")

    try:
        # 读取文件内容
        content = await file.read()
        file_stream = io.StringIO(content.decode('utf-8'))

        # 创建导入日志
        import_log = ImportLog(
            user_id=current_user.id,
            source="wechat",
            file_name=file.filename,
            file_size=len(content),
            status=ImportStatus.PROCESSING
        )
        db.add(import_log)
        db.commit()
        db.refresh(import_log)

        # 后台任务处理导入
        background_tasks.add_task(
            process_wechat_import,
            import_log.id,
            current_user.id,
            content,
            db
        )

        return {
            "import_log_id": import_log.id,
            "message": "文件上传成功，正在处理中",
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/preview", response_model=ImportPreview)
async def preview_wechat_bill(
    file: UploadFile = File(...),
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    预览微信账单数据
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV格式的微信账单文件")

    try:
        content = await file.read()
        file_stream = io.StringIO(content.decode('utf-8'))

        # 解析账单数据
        transactions = parse_wechat_csv(content)

        # 限制预览数量
        preview_transactions = transactions[:limit]

        # 统计信息
        income_count = len([t for t in transactions if t['transaction_type'] == TransactionType.INCOME])
        expense_count = len([t for t in transactions if t['transaction_type'] == TransactionType.EXPENSE])
        total_income = sum(t['amount'] for t in transactions if t['transaction_type'] == TransactionType.INCOME)
        total_expense = sum(t['amount'] for t in transactions if t['transaction_type'] == TransactionType.EXPENSE)

        # 获取智能分类建议
        smart_service = SmartCategorizationService(db)
        enriched_transactions = []

        for transaction in preview_transactions:
            if transaction.get('merchant_name'):
                suggestion = smart_service.suggest_category(
                    current_user.id,
                    transaction['merchant_name'],
                    transaction['amount'],
                    transaction['transaction_type']
                )
                transaction['category_suggestion'] = suggestion
            enriched_transactions.append(transaction)

        return ImportPreview(
            total_records=len(transactions),
            income_records=income_count,
            expense_records=expense_count,
            total_amount=total_income + total_expense,
            preview_records=preview_transactions,
            suggested_categories=[t['category_suggestion'] for t in enriched_transactions if t.get('category_suggestion')]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/import/{import_id}", response_model=ImportLogResponse)
async def get_import_log(
    import_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取导入日志详情
    """
    import_log = db.query(ImportLog).filter(
        ImportLog.id == import_id,
        ImportLog.user_id == current_user.id
    ).first()

    if not import_log:
        raise HTTPException(status_code=404, detail="导入记录不存在")

    return ImportLogResponse.from_orm(import_log)

@router.get("/imports", response_model=List[ImportLogResponse])
async def get_import_logs(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取导入记录列表
    """
    import_logs = db.query(ImportLog).filter(
        ImportLog.user_id == current_user.id
    ).order_by(
        ImportLog.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [ImportLogResponse.from_orm(log) for log in import_logs]

@router.get("/imports/{import_id}/errors", response_model=List[ImportErrorDetail])
async def get_import_errors(
    import_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取导入错误详情
    """
    import_log = db.query(ImportLog).filter(
        ImportLog.id == import_id,
        ImportLog.user_id == current_user.id
    ).first()

    if not import_log:
        raise HTTPException(status_code=404, detail="导入记录不存在")

    error_service = ImportErrorAnalysisService(db)
    error_analysis = error_service.analyze_import_errors(import_id)

    return [ImportErrorDetail(**error) for error in error_analysis['error_types']]

@router.post("/imports/{import_id}/retry", response_model=Dict)
async def retry_import_errors(
    import_id: int,
    retry_request: ImportRetryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重试导入错误记录
    """
    error_service = ImportErrorAnalysisService(db)

    try:
        result = error_service.retry_import_errors(
            current_user.id,
            import_id,
            retry_request
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/imports/{import_id}/verify-balance", response_model=Dict)
async def verify_import_balance(
    import_id: int,
    tolerance: float = 0.01,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    验证导入后的账户余额
    """
    import_log = db.query(ImportLog).filter(
        ImportLog.id == import_id,
        ImportLog.user_id == current_user.id
    ).first()

    if not import_log:
        raise HTTPException(status_code=404, detail="导入记录不存在")

    balance_service = BalanceVerificationService(db)

    try:
        result = balance_service.verify_balance_after_import(
            import_id,
            tolerance
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/statistics", response_model=ImportStatistics)
async def get_import_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取导入统计信息
    """
    from datetime import timedelta
    from sqlalchemy import func

    start_date = datetime.now() - timedelta(days=days)

    # 基础统计
    total_imports = db.query(ImportLog).filter(
        ImportLog.user_id == current_user.id,
        ImportLog.created_at >= start_date
    ).count()

    successful_imports = db.query(ImportLog).filter(
        ImportLog.user_id == current_user.id,
        ImportLog.status == ImportStatus.SUCCESS,
        ImportLog.created_at >= start_date
    ).count()

    total_records = db.query(func.sum(ImportLog.total_records)).filter(
        ImportLog.user_id == current_user.id,
        ImportLog.created_at >= start_date
    ).scalar() or 0

    success_records = db.query(func.sum(ImportLog.success_records)).filter(
        ImportLog.user_id == current_user.id,
        ImportLog.created_at >= start_date
    ).scalar() or 0

    failed_records = db.query(func.sum(ImportLog.failed_records)).filter(
        ImportLog.user_id == current_user.id,
        ImportLog.created_at >= start_date
    ).scalar() or 0

    # 错误分析
    error_service = ImportErrorAnalysisService(db)
    error_patterns = error_service.get_error_patterns(current_user.id, days)

    # 余额验证统计
    balance_service = BalanceVerificationService(db)
    balance_summary = balance_service.get_verification_summary(current_user.id, days)

    return ImportStatistics(
        period_days=days,
        total_imports=total_imports,
        successful_imports=successful_imports,
        total_records=total_records,
        success_records=success_records,
        failed_records=failed_records,
        success_rate=(successful_imports / total_imports * 100) if total_imports > 0 else 0,
        error_patterns=error_patterns['most_common_patterns'],
        balance_verification_summary=balance_summary
    )

@router.post("/smart-categorization/learn", response_model=Dict)
async def trigger_categorization_learning(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    触发智能分类学习
    """
    smart_service = SmartCategorizationService(db)

    try:
        learned_count = smart_service.batch_learn_from_transactions(current_user.id)
        return {
            "message": f"成功从 {learned_count} 条交易记录中学习",
            "learned_count": learned_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习失败: {str(e)}")

@router.get("/smart-categorization/suggestions", response_model=List[Dict])
async def get_category_suggestions(
    merchant_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 5
):
    """
    获取分类建议
    """
    smart_service = SmartCategorizationService(db)

    suggestions = smart_service.get_category_suggestions(
        current_user.id,
        merchant_name,
        limit
    )

    return [
        {
            "category_id": s.category_id,
            "merchant_name": s.merchant_name,
            "confidence": s.confidence,
            "frequency": s.frequency,
            "based_on": s.based_on
        }
        for s in suggestions
    ]

@router.post("/smart-categorization/feedback", response_model=Dict)
async def record_categorization_feedback(
    transaction_id: int,
    correct_category_id: int,
    suggestion_id: Optional[int] = None,
    feedback_type: str = "confirm",
    user_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录分类反馈
    """
    smart_service = SmartCategorizationService(db)

    try:
        learning_record = smart_service.record_feedback(
            current_user.id,
            transaction_id,
            correct_category_id,
            suggestion_id,
            feedback_type,
            user_notes
        )

        return {
            "message": "反馈记录成功",
            "learning_record_id": learning_record.id
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录反馈失败: {str(e)}")

@router.get("/smart-categorization/statistics", response_model=Dict)
async def get_categorization_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取智能分类统计信息
    """
    smart_service = SmartCategorizationService(db)

    try:
        stats = smart_service.get_learning_statistics(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/balance-verification/preferences", response_model=Dict)
async def update_balance_preferences(
    tolerance: float,
    auto_verify: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新余额验证偏好
    """
    balance_service = BalanceVerificationService(db)

    try:
        preferences = balance_service.update_user_preferences(
            current_user.id,
            {
                "balance_verification_enabled": auto_verify,
                "tolerance": tolerance
            }
        )

        return {
            "message": "偏好设置更新成功",
            "preferences": {
                "auto_verify": preferences.balance_verification_enabled,
                "tolerance": preferences.tolerance
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新偏好失败: {str(e)}")

@router.get("/balance-verification/history", response_model=List[Dict])
async def get_balance_verification_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取余额验证历史
    """
    balance_service = BalanceVerificationService(db)

    try:
        history = balance_service.get_verification_history(current_user.id, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验证历史失败: {str(e)}")

async def process_wechat_import(
    import_log_id: int,
    user_id: int,
    content: bytes,
    db: Session
):
    """
    后台任务：处理微信账单导入
    """
    try:
        # 解析账单数据
        transactions = parse_wechat_csv(content)

        import_log = db.query(ImportLog).filter(
            ImportLog.id == import_log_id
        ).first()

        if not import_log:
            return

        import_log.total_records = len(transactions)
        import_log.status = ImportStatus.PROCESSING
        db.commit()

        # 智能分类服务
        smart_service = SmartCategorizationService(db)
        error_service = ImportErrorAnalysisService(db)

        success_count = 0
        failed_count = 0
        error_records = []

        for index, transaction_data in enumerate(transactions):
            try:
                # 智能分类建议
                if transaction_data.get('merchant_name'):
                    suggestion = smart_service.suggest_category(
                        user_id,
                        transaction_data['merchant_name'],
                        transaction_data['amount'],
                        transaction_data['transaction_type']
                    )

                    if suggestion and suggestion.confidence >= 0.7:
                        transaction_data['category_id'] = suggestion.category_id

                # 创建交易记录
                transaction = Transaction(
                    user_id=user_id,
                    **transaction_data
                )

                db.add(transaction)
                success_count += 1

            except Exception as e:
                failed_count += 1
                # 记录错误
                error_record = {
                    'import_log_id': import_log_id,
                    'row_number': index + 1,
                    'error_type': 'VALIDATION_ERROR',
                    'error_message': str(e),
                    'raw_data': transaction_data
                }
                error_records.append(error_record)

        # 更新导入日志
        import_log.success_records = success_count
        import_log.failed_records = failed_count

        if failed_count == 0:
            import_log.status = ImportStatus.SUCCESS
        elif success_count > 0:
            import_log.status = ImportStatus.PARTIAL
        else:
            import_log.status = ImportStatus.FAILED

        import_log.completed_at = datetime.now()
        import_log.import_summary = f"导入完成：成功 {success_count} 条，失败 {failed_count} 条"

        db.commit()

        # 触发余额验证（如果启用）
        if success_count > 0:
            try:
                balance_service = BalanceVerificationService(db)
                user_preferences = balance_service.get_user_preferences(user_id)

                if user_preferences.balance_verification_enabled:
                    balance_service.verify_balance_after_import(
                        import_log_id,
                        user_preferences.tolerance
                    )
            except Exception as e:
                # 余额验证失败不影响导入状态
                print(f"余额验证失败: {str(e)}")

    except Exception as e:
        # 处理失败
        import_log = db.query(ImportLog).filter(
            ImportLog.id == import_log_id
        ).first()

        if import_log:
            import_log.status = ImportStatus.FAILED
            import_log.completed_at = datetime.now()
            import_log.error_details = {"error": str(e)}
            db.commit()