from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db

router = APIRouter()

@router.get("/")
async def get_accounts(db: Session = Depends(get_db)):
    """获取账户列表"""
    return {"message": "账户列表"}

@router.post("/")
async def create_account(db: Session = Depends(get_db)):
    """创建账户"""
    return {"message": "创建账户"}

@router.post("/transfer")
async def transfer_money(db: Session = Depends(get_db)):
    """账户转账"""
    return {"message": "账户转账"}

@router.put("/{account_id}")
async def update_account(account_id: int, db: Session = Depends(get_db)):
    """更新账户"""
    return {"message": f"更新账户: {account_id}"}

@router.delete("/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账户"""
    return {"message": f"删除账户: {account_id}"}