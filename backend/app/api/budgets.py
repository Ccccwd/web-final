from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db

router = APIRouter()

@router.get("/")
async def get_budgets(db: Session = Depends(get_db)):
    """获取预算列表"""
    return {"message": "预算列表"}

@router.post("/")
async def create_budget(db: Session = Depends(get_db)):
    """创建预算"""
    return {"message": "创建预算"}

@router.put("/{budget_id}")
async def update_budget(budget_id: int, db: Session = Depends(get_db)):
    """更新预算"""
    return {"message": f"更新预算: {budget_id}"}

@router.delete("/{budget_id}")
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """删除预算"""
    return {"message": f"删除预算: {budget_id}"}