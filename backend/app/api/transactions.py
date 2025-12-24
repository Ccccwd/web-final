from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.transaction import TransactionType
from app.services.transaction_service import TransactionService
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionFilter,
    TransactionResponse, TransactionListResponse, TransactionSummary
)
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError

router = APIRouter()

def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """获取交易服务实例"""
    return TransactionService(db)

@router.get("/", response_model=TransactionListResponse)
@router.get("", response_model=TransactionListResponse)
async def get_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="交易类型"),
    category_id: Optional[int] = Query(None, ge=1, description="分类ID"),
    account_id: Optional[int] = Query(None, ge=1, description="账户ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    min_amount: Optional[float] = Query(None, ge=0, description="最小金额"),
    max_amount: Optional[float] = Query(None, ge=0, description="最大金额"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query(None, description="排序方向"),
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    获取交易记录列表

    支持多种筛选条件：
    - 交易类型筛选
    - 分类和账户筛选
    - 时间范围筛选
    - 关键词搜索
    - 金额范围筛选
    """
    try:
        # 构建筛选条件（过滤空字符串）
        filter_dict = {}
        if type and type.strip():
            filter_dict['type'] = TransactionType(type)
        if category_id:
            filter_dict['category_id'] = category_id
        if account_id:
            filter_dict['account_id'] = account_id
        if start_date and start_date.strip():
            filter_dict['start_date'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date and end_date.strip():
            filter_dict['end_date'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if keyword and keyword.strip():
            filter_dict['keyword'] = keyword
        if min_amount:
            filter_dict['min_amount'] = min_amount
        if max_amount:
            filter_dict['max_amount'] = max_amount

        filter_obj = TransactionFilter(**filter_dict) if filter_dict else None

        # 获取交易记录
        transactions, total = transaction_service.get_transactions(
            user_id=current_user.id,
            filter=filter_obj,
            page=page,
            page_size=page_size
        )

        # 转换为响应格式
        transaction_responses = []
        for transaction in transactions:
            transaction_dict = {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "type": transaction.type,
                "amount": float(transaction.amount),
                "category_id": transaction.category_id,
                "account_id": transaction.account_id,
                "to_account_id": transaction.to_account_id,
                "transaction_date": transaction.transaction_date,
                "remark": transaction.remark,
                "images": transaction.images,
                "tags": transaction.tags,
                "location": transaction.location,
                "source": transaction.source,
                "wechat_transaction_id": transaction.wechat_transaction_id,
                "original_category": transaction.original_category,
                "merchant_name": transaction.merchant_name,
                "pay_method": transaction.pay_method,
                "is_repeated": transaction.is_repeated,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                # 关联数据
                "category_name": transaction.category.name if transaction.category else None,
                "category_icon": transaction.category.icon if transaction.category else None,
                "category_color": transaction.category.color if transaction.category else None,
                "account_name": transaction.account.name if transaction.account else None,
                "to_account_name": transaction.to_account.name if transaction.to_account else None,
            }
            transaction_responses.append(TransactionResponse(**transaction_dict))

        total_pages = (total + page_size - 1) // page_size

        return TransactionListResponse(
            transactions=transaction_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        return error_response(500, f"获取交易记录失败: {str(e)}")

@router.get("/statistics")
@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    type: Optional[str] = Query(None, description="交易类型"),
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """获取交易统计摘要"""
    try:
        # 处理日期字符串（过滤空字符串）
        start_dt = None
        end_dt = None
        if start_date and start_date.strip():
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date and end_date.strip():
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        summary = transaction_service.get_transaction_summary(
            user_id=current_user.id,
            start_date=start_dt,
            end_date=end_dt
        )

        return TransactionSummary(
            total_income=float(summary.total_income),
            total_expense=float(summary.total_expense),
            total_transfer=float(summary.total_transfer),
            net_income=float(summary.net_income),
            transaction_count=summary.transaction_count
        )

    except Exception as e:
        return error_response(500, f"获取交易统计失败: {str(e)}")

@router.get("/search")
async def search_transactions(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """搜索交易记录"""
    try:
        transactions = transaction_service.search_transactions(
            user_id=current_user.id,
            keyword=keyword,
            limit=limit
        )

        # 转换为响应格式
        transaction_responses = []
        for transaction in transactions:
            transaction_dict = {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "type": transaction.type,
                "amount": float(transaction.amount),
                "category_id": transaction.category_id,
                "account_id": transaction.account_id,
                "to_account_id": transaction.to_account_id,
                "transaction_date": transaction.transaction_date,
                "remark": transaction.remark,
                "images": transaction.images,
                "tags": transaction.tags,
                "location": transaction.location,
                "source": transaction.source,
                "wechat_transaction_id": transaction.wechat_transaction_id,
                "original_category": transaction.original_category,
                "merchant_name": transaction.merchant_name,
                "pay_method": transaction.pay_method,
                "is_repeated": transaction.is_repeated,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                # 关联数据
                "category_name": transaction.category.name if transaction.category else None,
                "category_icon": transaction.category.icon if transaction.category else None,
                "category_color": transaction.category.color if transaction.category else None,
                "account_name": transaction.account.name if transaction.account else None,
                "to_account_name": transaction.to_account.name if transaction.to_account else None,
            }
            transaction_responses.append(TransactionResponse(**transaction_dict))

        return success_response(data=transaction_responses)

    except Exception as e:
        return error_response(500, f"搜索交易记录失败: {str(e)}")

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """获取交易记录详情"""
    try:
        transaction = transaction_service.get_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id
        )

        transaction_dict = {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "type": transaction.type,
            "amount": float(transaction.amount),
            "category_id": transaction.category_id,
            "account_id": transaction.account_id,
            "to_account_id": transaction.to_account_id,
            "transaction_date": transaction.transaction_date,
            "remark": transaction.remark,
            "images": transaction.images,
            "tags": transaction.tags,
            "location": transaction.location,
            "source": transaction.source,
            "wechat_transaction_id": transaction.wechat_transaction_id,
            "original_category": transaction.original_category,
            "merchant_name": transaction.merchant_name,
            "pay_method": transaction.pay_method,
            "is_repeated": transaction.is_repeated,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            # 关联数据
            "category_name": transaction.category.name if transaction.category else None,
            "category_icon": transaction.category.icon if transaction.category else None,
            "category_color": transaction.category.color if transaction.category else None,
            "account_name": transaction.account.name if transaction.account else None,
            "to_account_name": transaction.to_account.name if transaction.to_account else None,
        }

        return TransactionResponse(**transaction_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取交易详情失败: {str(e)}")

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """创建交易记录"""
    try:
        transaction = transaction_service.create_transaction(
            user_id=current_user.id,
            transaction_data=transaction_data
        )

        transaction_dict = {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "type": transaction.type,
            "amount": float(transaction.amount),
            "category_id": transaction.category_id,
            "account_id": transaction.account_id,
            "to_account_id": transaction.to_account_id,
            "transaction_date": transaction.transaction_date,
            "remark": transaction.remark,
            "images": transaction.images,
            "tags": transaction.tags,
            "location": transaction.location,
            "source": transaction.source,
            "wechat_transaction_id": transaction.wechat_transaction_id,
            "original_category": transaction.original_category,
            "merchant_name": transaction.merchant_name,
            "pay_method": transaction.pay_method,
            "is_repeated": transaction.is_repeated,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            # 关联数据
            "category_name": transaction.category.name if transaction.category else None,
            "category_icon": transaction.category.icon if transaction.category else None,
            "category_color": transaction.category.color if transaction.category else None,
            "account_name": transaction.account.name if transaction.account else None,
            "to_account_name": transaction.to_account.name if transaction.to_account else None,
        }

        return TransactionResponse(**transaction_dict)

    except Exception as e:
        return error_response(500, f"创建交易记录失败: {str(e)}")

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """更新交易记录"""
    try:
        transaction = transaction_service.update_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id,
            transaction_data=transaction_data
        )

        transaction_dict = {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "type": transaction.type,
            "amount": float(transaction.amount),
            "category_id": transaction.category_id,
            "account_id": transaction.account_id,
            "to_account_id": transaction.to_account_id,
            "transaction_date": transaction.transaction_date,
            "remark": transaction.remark,
            "images": transaction.images,
            "tags": transaction.tags,
            "location": transaction.location,
            "source": transaction.source,
            "wechat_transaction_id": transaction.wechat_transaction_id,
            "original_category": transaction.original_category,
            "merchant_name": transaction.merchant_name,
            "pay_method": transaction.pay_method,
            "is_repeated": transaction.is_repeated,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            # 关联数据
            "category_name": transaction.category.name if transaction.category else None,
            "category_icon": transaction.category.icon if transaction.category else None,
            "category_color": transaction.category.color if transaction.category else None,
            "account_name": transaction.account.name if transaction.account else None,
            "to_account_name": transaction.to_account.name if transaction.to_account else None,
        }

        return TransactionResponse(**transaction_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"更新交易记录失败: {str(e)}")

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """删除交易记录"""
    try:
        success = transaction_service.delete_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id
        )

        if success:
            return success_response(message="删除成功")
        else:
            return error_response(500, "删除失败")

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"删除交易记录失败: {str(e)}")

@router.post("/{transaction_id}/mark-repeated")
async def mark_transaction_as_repeated(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """标记交易为重复"""
    try:
        transaction = transaction_service.get_transaction(
            user_id=current_user.id,
            transaction_id=transaction_id
        )

        updated_transaction = transaction_service.mark_as_repeated(transaction_id)

        return success_response(message="已标记为重复交易")

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"标记重复交易失败: {str(e)}")