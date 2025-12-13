from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Union
from app.core.responses import error_response

class CustomException(Exception):
    """自定义异常基类"""
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)

class BusinessException(CustomException):
    """业务逻辑异常"""
    def __init__(self, message: str, code: int = 400, data=None):
        super().__init__(code, message, data)

class AuthenticationError(CustomException):
    """认证异常"""
    def __init__(self, message: str = "认证失败", data=None):
        super().__init__(401, message, data)

class AuthorizationError(CustomException):
    """授权异常"""
    def __init__(self, message: str = "权限不足", data=None):
        super().__init__(403, message, data)

class ValidationError(CustomException):
    """验证异常"""
    def __init__(self, message: str = "参数验证失败", data=None):
        super().__init__(400, message, data)

class NotFoundError(CustomException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", data=None):
        super().__init__(404, message, data)

class DatabaseError(CustomException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败", data=None):
        super().__init__(500, message, data)

# 全局异常处理器
async def custom_exception_handler(request: Request, exc: CustomException):
    """自定义异常处理器"""
    return JSONResponse(
        status_code=exc.code,
        content=error_response(exc.code, exc.message, exc.data).dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail).dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content=error_response(422, "请求参数验证失败", errors).dict()
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理器"""
    return JSONResponse(
        status_code=500,
        content=error_response(500, "数据库操作失败", str(exc)).dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    return JSONResponse(
        status_code=500,
        content=error_response(500, "服务器内部错误", str(exc)).dict()
    )