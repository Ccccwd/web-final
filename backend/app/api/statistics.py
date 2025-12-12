from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db

router = APIRouter()

@router.get("/overview")
async def get_overview(db: Session = Depends(get_db)):
    """获取首页概览数据"""
    return {"message": "首页概览数据"}

@router.get("/trend")
async def get_trend(db: Session = Depends(get_db)):
    """获取趋势数据"""
    return {"message": "趋势数据"}

@router.get("/category")
async def get_category_statistics(db: Session = Depends(get_db)):
    """获取分类统计"""
    return {"message": "分类统计"}

@router.get("/export/excel")
async def export_excel(db: Session = Depends(get_db)):
    """导出Excel"""
    return {"message": "导出Excel"}

@router.get("/export/pdf")
async def export_pdf(db: Session = Depends(get_db)):
    """导出PDF"""
    return {"message": "导出PDF"}