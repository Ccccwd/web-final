from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.config.settings import settings
from app.api import auth, transactions, statistics, budgets, accounts, categories, import_apis as import_api, account_balance_history, reminders, reports
from app.api.v1.wechat_import import router as wechat_router
from app.core.exceptions import (
    custom_exception_handler, http_exception_handler,
    validation_exception_handler, database_exception_handler,
    general_exception_handler, CustomException
)

app = FastAPI(
    title="个人财务记账系统 API",
    description="一个面向大学生和年轻群体的轻量级个人财务管理系统",
    version="1.0.0"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(categories.router, prefix="/api/categories", tags=["分类管理"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账户管理"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["交易记录"])
app.include_router(import_api.router, prefix="/api/import", tags=["账单导入"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["统计分析"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["预算管理"])
app.include_router(account_balance_history.router, prefix="/api", tags=["账户余额历史"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["智能提醒"])
app.include_router(reports.router, prefix="/api/reports", tags=["分析报告"])
app.include_router(wechat_router, prefix="/api/v1", tags=["微信账单导入"])

@app.get("/")
async def root():
    return {"message": "个人财务记账系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)