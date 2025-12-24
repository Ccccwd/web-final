from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.account import AccountType
from app.services.account_service import AccountService
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountTransfer,
    AccountResponse, AccountListResponse, AccountWithStats
)
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    """获取账户服务实例"""
    return AccountService(db)

@router.get("/", response_model=AccountListResponse)
@router.get("", response_model=AccountListResponse)
async def get_accounts(
    type: Optional[str] = Query(None, description="账户类型"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """获取账户列表"""
    try:
        # 处理账户类型（过滤空字符串）
        account_type = None
        if type and type.strip():
            account_type = AccountType(type)
        
        accounts = account_service.get_accounts(
            user_id=current_user.id,
            account_type=account_type,
            is_enabled=is_enabled
        )

        # 转换为响应格式
        account_responses = []
        for account in accounts:
            account_dict = {
                "id": account.id,
                "user_id": account.user_id,
                "name": account.name,
                "type": account.type,
                "balance": float(account.balance),
                "initial_balance": float(account.initial_balance),
                "icon": account.icon,
                "color": account.color,
                "is_default": account.is_default,
                "is_enabled": account.is_enabled,
                "description": account.description,
                "created_at": account.created_at,
                "updated_at": account.updated_at,
            }
            account_responses.append(AccountResponse(**account_dict))

        return AccountListResponse(
            accounts=account_responses,
            total=len(account_responses)
        )

    except Exception as e:
        return error_response(500, f"获取账户列表失败: {str(e)}")

@router.get("/summary")
async def get_account_summary(
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """获取账户统计摘要"""
    try:
        summary = account_service.get_account_summary(current_user.id)

        return success_response(data=summary)

    except Exception as e:
        return error_response(500, f"获取账户统计失败: {str(e)}")

@router.get("/default")
async def get_default_account(
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """获取默认账户"""
    try:
        account = account_service.get_default_account(current_user.id)

        if not account:
            return success_response(message="暂无默认账户", data=None)

        account_dict = {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "type": account.type,
            "balance": float(account.balance),
            "initial_balance": float(account.initial_balance),
            "icon": account.icon,
            "color": account.color,
            "is_default": account.is_default,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }

        return success_response(data=AccountResponse(**account_dict))

    except Exception as e:
        return error_response(500, f"获取默认账户失败: {str(e)}")

@router.get("/{account_id}", response_model=AccountWithStats)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """获取账户详情"""
    try:
        account = account_service.get_account_with_stats(
            user_id=current_user.id,
            account_id=account_id
        )

        return account

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取账户详情失败: {str(e)}")

@router.post("/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """创建账户"""
    try:
        account = account_service.create_account(
            user_id=current_user.id,
            account_data=account_data
        )

        account_dict = {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "type": account.type,
            "balance": float(account.balance),
            "initial_balance": float(account.initial_balance),
            "icon": account.icon,
            "color": account.color,
            "is_default": account.is_default,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }

        return AccountResponse(**account_dict)

    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"创建账户失败: {str(e)}")

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """更新账户"""
    try:
        account = account_service.update_account(
            user_id=current_user.id,
            account_id=account_id,
            account_data=account_data
        )

        account_dict = {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "type": account.type,
            "balance": float(account.balance),
            "initial_balance": float(account.initial_balance),
            "icon": account.icon,
            "color": account.color,
            "is_default": account.is_default,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }

        return AccountResponse(**account_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"更新账户失败: {str(e)}")

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """删除账户"""
    try:
        success = account_service.delete_account(
            user_id=current_user.id,
            account_id=account_id
        )

        if success:
            return success_response(message="删除成功")
        else:
            return error_response(500, "删除失败")

    except NotFoundError as e:
        return error_response(404, str(e))
    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"删除账户失败: {str(e)}")

@router.post("/transfer")
async def transfer_between_accounts(
    transfer_data: AccountTransfer,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """账户间转账"""
    try:
        from_transaction, to_transaction, from_account, to_account = account_service.transfer_between_accounts(
            user_id=current_user.id,
            transfer_data=transfer_data
        )

        # 构建响应数据
        response_data = {
            "from_transaction": {
                "id": from_transaction.id,
                "amount": float(from_transaction.amount),
                "account_name": from_account.name,
                "remark": from_transaction.remark
            },
            "to_transaction": {
                "id": to_transaction.id,
                "amount": float(to_transaction.amount),
                "account_name": to_account.name,
                "remark": to_transaction.remark
            },
            "from_account_balance": float(from_account.balance),
            "to_account_balance": float(to_account.balance)
        }

        return success_response(
            message="转账成功",
            data=response_data
        )

    except ValidationError as e:
        return error_response(400, str(e))
    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"转账失败: {str(e)}")

@router.post("/{account_id}/set-default")
async def set_default_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    account_service: AccountService = Depends(get_account_service)
):
    """设置默认账户"""
    try:
        account = account_service.set_default_account(
            user_id=current_user.id,
            account_id=account_id
        )

        account_dict = {
            "id": account.id,
            "user_id": account.user_id,
            "name": account.name,
            "type": account.type,
            "balance": float(account.balance),
            "initial_balance": float(account.initial_balance),
            "icon": account.icon,
            "color": account.color,
            "is_default": account.is_default,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }

        return success_response(
            message="已设置为默认账户",
            data=AccountResponse(**account_dict)
        )

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"设置默认账户失败: {str(e)}")