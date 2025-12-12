from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.core.responses import setup_exception_handlers
from app.config.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title="个人记账系统",
    description="一个功能完整的个人记账管理系统",
    version="1.0.0"
)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置异常处理器
setup_exception_handlers(app)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])

@app.get("/")
async def root():
    return {"message": "个人记账系统 API 服务"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
