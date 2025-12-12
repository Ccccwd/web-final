from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db

router = APIRouter()

@router.get("/")
async def get_transactions(db: Session = Depends(get_db)):
    """获取交易记录列表"""
    return {"message": "交易记录列表"}

@router.post("/")
async def create_transaction(db: Session = Depends(get_db)):
    """创建交易记录"""
    return {"message": "创建交易记录"}

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """获取交易记录详情"""
    return {"message": f"交易记录详情: {transaction_id}"}

@router.put("/{transaction_id}")
async def update_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """更新交易记录"""
    return {"message": f"更新交易记录: {transaction_id}"}

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """删除交易记录"""
    return {"message": f"删除交易记录: {transaction_id}"}