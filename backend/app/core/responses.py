from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

# 定义泛型类型变量
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    success: bool = True

class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    pageSize: int
    total: int
    totalPages: int

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = 200
    message: str = "success"
    data: list[T] = []
    pagination: PaginationInfo
    success: bool = True

# 成功响应的便捷函数
def success_response(data: T = None, message: str = "操作成功") -> APIResponse[T]:
    """创建成功响应"""
    return APIResponse(
        code=200,
        message=message,
        data=data,
        success=True
    )

def paginated_response(
    data: list[T],
    page: int,
    pageSize: int,
    total: int,
    message: str = "查询成功"
) -> PaginatedResponse[T]:
    """创建分页响应"""
    totalPages = (total + pageSize - 1) // pageSize
    return PaginatedResponse(
        code=200,
        message=message,
        data=data,
        pagination=PaginationInfo(
            page=page,
            pageSize=pageSize,
            total=total,
            totalPages=totalPages
        ),
        success=True
    )

# 错误响应的便捷函数
def error_response(code: int, message: str, data: Any = None) -> APIResponse:
    """创建错误响应"""
    return APIResponse(
        code=code,
        message=message,
        data=data,
        success=False
    )

# 常用错误响应
def bad_request_response(message: str = "请求参数错误", data: Any = None) -> APIResponse:
    """400错误响应"""
    return error_response(400, message, data)

def unauthorized_response(message: str = "未授权访问", data: Any = None) -> APIResponse:
    """401错误响应"""
    return error_response(401, message, data)

def forbidden_response(message: str = "禁止访问", data: Any = None) -> APIResponse:
    """403错误响应"""
    return error_response(403, message, data)

def not_found_response(message: str = "资源不存在", data: Any = None) -> APIResponse:
    """404错误响应"""
    return error_response(404, message, data)

def internal_error_response(message: str = "服务器内部错误", data: Any = None) -> APIResponse:
    """500错误响应"""
    return error_response(500, message, data)