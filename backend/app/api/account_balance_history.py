from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.account_balance_history import BalanceChangeType
from app.services.account_balance_history_service import AccountBalanceHistoryService
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_balance_history_service(db: Session = Depends(get_db)) -> AccountBalanceHistoryService:
    """获取账户余额历史服务实例"""
    return AccountBalanceHistoryService(db)

@router.get("/accounts/{account_id}/balance-history")
async def get_account_balance_history(
    account_id: int,
    limit: int = Query(50, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    change_type: Optional[BalanceChangeType] = Query(None, description="变化类型"),
    current_user: User = Depends(get_current_active_user),
    balance_service: AccountBalanceHistoryService = Depends(get_balance_history_service)
):
    """获取账户余额历史"""
    try:
        histories = balance_service.get_account_balance_history(
            user_id=current_user.id,
            account_id=account_id,
            limit=limit,
            offset=offset,
            change_type=change_type
        )

        # 转换为响应格式
        history_responses = []
        for history in histories:
            history_dict = {
                "id": history.id,
                "account_id": history.account_id,
                "transaction_id": history.transaction_id,
                "change_type": history.change_type,
                "amount_before": float(history.amount_before),
                "amount_after": float(history.amount_after),
                "change_amount": float(history.change_amount),
                "description": history.description,
                "reference_id": history.reference_id,
                "created_at": history.created_at
            }
            history_responses.append(history_dict)

        return success_response(data=history_responses)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取账户余额历史失败: {str(e)}")

@router.get("/balance-history")
async def get_user_balance_history(
    limit: int = Query(100, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    change_type: Optional[BalanceChangeType] = Query(None, description="变化类型"),
    current_user: User = Depends(get_current_active_user),
    balance_service: AccountBalanceHistoryService = Depends(get_balance_history_service)
):
    """获取用户所有账户的余额历史"""
    try:
        histories = balance_service.get_user_balance_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            change_type=change_type
        )

        # 转换为响应格式
        history_responses = []
        for history in histories:
            history_dict = {
                "id": history.id,
                "account_id": history.account_id,
                "account_name": history.account.name if history.account else None,
                "transaction_id": history.transaction_id,
                "change_type": history.change_type,
                "amount_before": float(history.amount_before),
                "amount_after": float(history.amount_after),
                "change_amount": float(history.change_amount),
                "description": history.description,
                "reference_id": history.reference_id,
                "created_at": history.created_at
            }
            history_responses.append(history_dict)

        return success_response(data=history_responses)

    except Exception as e:
        return error_response(500, f"获取用户余额历史失败: {str(e)}")

@router.get("/accounts/{account_id}/balance-statistics")
async def get_balance_statistics(
    account_id: int,
    days: int = Query(30, le=365, ge=1, description="统计天数"),
    current_user: User = Depends(get_current_active_user),
    balance_service: AccountBalanceHistoryService = Depends(get_balance_history_service)
):
    """获取账户余额统计信息"""
    try:
        statistics = balance_service.get_balance_statistics(
            user_id=current_user.id,
            account_id=account_id,
            days=days
        )

        return success_response(data=statistics)

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取账户余额统计失败: {str(e)}")

@router.post("/accounts/{account_id}/record-initial-balance")
async def record_initial_balance(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    balance_service: AccountBalanceHistoryService = Depends(get_balance_history_service)
):
    """记录账户初始余额"""
    try:
        history = balance_service.record_initial_balance(account_id)

        history_dict = {
            "id": history.id,
            "account_id": history.account_id,
            "change_type": history.change_type,
            "amount_before": float(history.amount_before),
            "amount_after": float(history.amount_after),
            "change_amount": float(history.change_amount),
            "description": history.description,
            "created_at": history.created_at
        }

        return success_response(
            message="初始余额记录成功",
            data=history_dict
        )

    except NotFoundError as e:
        return error_response(404, str(e))
    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"记录初始余额失败: {str(e)}")