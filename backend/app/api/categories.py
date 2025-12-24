from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.category import CategoryType
from app.services.category_service import CategoryService
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryListResponse, CategoryWithStats, CategoryTreeResponse
)
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """获取分类服务实例"""
    return CategoryService(db)

@router.get("/", response_model=CategoryListResponse)
@router.get("", response_model=CategoryListResponse)
async def get_categories(
    type: Optional[str] = Query(None, description="分类类型"),
    include_system: bool = Query(True, description="是否包含系统分类"),
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """获取分类列表"""
    try:
        # 处理分类类型（过滤空字符串）
        category_type = None
        if type and type.strip():
            category_type = CategoryType(type)
        
        categories = category_service.get_categories(
            user_id=current_user.id,
            category_type=category_type,
            include_system=include_system,
            parent_id=parent_id
        )

        # 转换为响应格式
        category_responses = []
        for category in categories:
            category_dict = {
                "id": category.id,
                "user_id": None,  # 分类是系统级的,没有user_id
                "name": category.name,
                "type": category.type,
                "icon": category.icon,
                "color": category.color,
                "parent_id": category.parent_id,
                "sort_order": category.sort_order,
                "is_system": category.is_system,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            }
            category_responses.append(CategoryResponse(**category_dict))

        return CategoryListResponse(
            categories=category_responses,
            total=len(category_responses)
        )

    except Exception as e:
        return error_response(500, f"获取分类列表失败: {str(e)}")

@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
    type: Optional[CategoryType] = Query(None, description="分类类型"),
    include_system: bool = Query(True, description="是否包含系统分类"),
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """获取分类树"""
    try:
        categories = category_service.get_category_tree(
            user_id=current_user.id,
            category_type=type,
            include_system=include_system
        )

        # 转换为响应格式
        category_responses = []
        for category in categories:
            category_dict = {
                "id": category.id,
                "user_id": None,  # 分类是系统级的,没有user_id
                "name": category.name,
                "type": category.type,
                "icon": category.icon,
                "color": category.color,
                "parent_id": category.parent_id,
                "sort_order": category.sort_order,
                "is_system": category.is_system,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "children": [],
            }

            # 递归处理子分类
            if hasattr(category, 'children') and category.children:
                for child in category.children:
                    child_dict = {
                        "id": child.id,
                        "user_id": child.user_id,
                        "name": child.name,
                        "type": child.type,
                        "icon": child.icon,
                        "color": child.color,
                        "parent_id": child.parent_id,
                        "sort_order": child.sort_order,
                        "is_system": child.is_system,
                        "created_at": child.created_at,
                        "updated_at": child.updated_at,
                        "children": [],
                    }
                    category_dict["children"].append(CategoryTreeResponse(**child_dict))

            category_responses.append(CategoryTreeResponse(**category_dict))

        return category_responses

    except Exception as e:
        return error_response(500, f"获取分类树失败: {str(e)}")

@router.get("/stats", response_model=List[CategoryWithStats])
async def get_categories_with_stats(
    type: Optional[CategoryType] = Query(None, description="分类类型"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """获取带统计信息的分类列表"""
    try:
        categories = category_service.get_categories_with_usage_stats(
            user_id=current_user.id,
            category_type=type,
            limit=limit
        )

        return categories

    except Exception as e:
        return error_response(500, f"获取分类统计失败: {str(e)}")

@router.get("/{category_id}", response_model=CategoryWithStats)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """获取分类详情"""
    try:
        category = category_service.get_category_with_stats(
            user_id=current_user.id,
            category_id=category_id
        )

        return category

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取分类详情失败: {str(e)}")

@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """创建分类"""
    try:
        category = category_service.create_category(
            user_id=current_user.id,
            category_data=category_data
        )

        category_dict = {
            "id": category.id,
            "user_id": None,  # 分类是系统级的,没有user_id
            "name": category.name,
            "type": category.type,
            "icon": category.icon,
            "color": category.color,
            "parent_id": category.parent_id,
            "sort_order": category.sort_order,
            "is_system": category.is_system,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }

        return CategoryResponse(**category_dict)

    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"创建分类失败: {str(e)}")

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """更新分类"""
    try:
        category = category_service.update_category(
            user_id=current_user.id,
            category_id=category_id,
            category_data=category_data
        )

        category_dict = {
            "id": category.id,
            "user_id": None,  # 分类是系统级的,没有user_id
            "name": category.name,
            "type": category.type,
            "icon": category.icon,
            "color": category.color,
            "parent_id": category.parent_id,
            "sort_order": category.sort_order,
            "is_system": category.is_system,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }

        return CategoryResponse(**category_dict)

    except NotFoundError as e:
        return error_response(404, str(e))
    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"更新分类失败: {str(e)}")

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """删除分类"""
    try:
        success = category_service.delete_category(
            user_id=current_user.id,
            category_id=category_id
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
        return error_response(500, f"删除分类失败: {str(e)}")

@router.post("/init-system")
async def init_system_categories(
    current_user: User = Depends(get_current_active_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """初始化系统分类"""
    try:
        categories = category_service.init_system_categories(current_user.id)

        category_dict_list = []
        for category in categories:
            category_dict = {
                "id": category.id,
                "user_id": None,  # 分类是系统级的,没有user_id
                "name": category.name,
                "type": category.type,
                "icon": category.icon,
                "color": category.color,
                "parent_id": category.parent_id,
                "sort_order": category.sort_order,
                "is_system": category.is_system,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            }
            category_dict_list.append(CategoryResponse(**category_dict))

        return success_response(
            message=f"成功初始化 {len(categories)} 个系统分类",
            data=category_dict_list
        )

    except Exception as e:
        return error_response(500, f"初始化系统分类失败: {str(e)}")