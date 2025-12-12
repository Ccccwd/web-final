from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api import auth, transactions, statistics, budgets, accounts

app = FastAPI(
    title="个人财务记账系统 API",
    description="一个面向大学生和年轻群体的轻量级个人财务管理系统",
    version="1.0.0"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["交易记录"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["统计分析"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["预算管理"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账户管理"])

@app.get("/")
async def root():
    return {"message": "个人财务记账系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)