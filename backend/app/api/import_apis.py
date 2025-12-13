from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import base64
import io

from app.config.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.import_service import ImportService
from app.services.wechat_bill_service import WeChatBillService
from app.schemas.import_log import (
    ImportRequest, ImportResponse, ImportLogListResponse,
    ImportLogResponse
)
from app.core.responses import success_response, error_response
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()

def get_import_service(db: Session = Depends(get_db)) -> ImportService:
    """获取导入服务实例"""
    return ImportService(db)

def get_wechat_service() -> WeChatBillService:
    """获取微信账单服务实例"""
    return WeChatBillService()

@router.post("/wechat/preview")
async def preview_wechat_bill(
    file: UploadFile = File(..., description="微信账单CSV文件"),
    current_user: User = Depends(get_current_active_user),
    wechat_service: WeChatBillService = Depends(get_wechat_service)
):
    """预览微信账单"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.csv'):
            return error_response(400, "请上传CSV格式文件")

        # 读取文件内容
        content = await file.read()

        # 验证文件格式
        is_valid, error_message = wechat_service.validate_csv_format(content, file.filename)
        if not is_valid:
            return error_response(400, error_message)

        # 解析文件
        csv_content = content.decode('utf-8')
        import_preview = wechat_service.parse_csv_content(csv_content)

        # 获取文件摘要
        file_summary = wechat_service.get_csv_summary(content)

        return success_response(data={
            "preview": import_preview.dict(),
            "summary": file_summary,
            "filename": file.filename,
            "file_size": len(content)
        })

    except Exception as e:
        return error_response(500, f"预览失败: {str(e)}")

@router.post("/wechat/import")
async def import_wechat_bill(
    file: UploadFile = File(..., description="微信账单CSV文件"),
    skip_duplicates: bool = Form(True, description="是否跳过重复记录"),
    auto_categorize: bool = Form(True, description="是否自动分类"),
    default_account_id: Optional[int] = Form(None, description="默认账户ID"),
    current_user: User = Depends(get_current_active_user),
    import_service: ImportService = Depends(get_import_service)
):
    """导入微信账单"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.csv'):
            return error_response(400, "请上传CSV格式文件")

        # 读取文件内容
        content = await file.read()
        csv_content = content.decode('utf-8')

        # 创建导入请求
        import_request = ImportRequest(
            file_content=csv_content,
            filename=file.filename,
            source="wechat",
            skip_duplicates=skip_duplicates,
            auto_categorize=auto_categorize,
            default_account_id=default_account_id
        )

        # 执行导入
        result = await import_service.import_wechat_bill(
            user_id=current_user.id,
            import_request=import_request
        )

        return success_response(
            message=f"导入完成: {result.message}",
            data=result.dict()
        )

    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"导入失败: {str(e)}")

@router.post("/wechat/import-base64")
async def import_wechat_bill_base64(
    import_request: ImportRequest,
    current_user: User = Depends(get_current_active_user),
    import_service: ImportService = Depends(get_import_service)
):
    """通过Base64导入微信账单"""
    try:
        # 解码Base64内容
        try:
            csv_content = base64.b64decode(import_request.file_content).decode('utf-8')
            import_request.file_content = csv_content
        except Exception:
            return error_response(400, "文件内容解码失败")

        # 执行导入
        result = await import_service.import_wechat_bill(
            user_id=current_user.id,
            import_request=import_request
        )

        return success_response(
            message=f"导入完成: {result.message}",
            data=result.dict()
        )

    except ValidationError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"导入失败: {str(e)}")

@router.get("/logs", response_model=ImportLogListResponse)
async def get_import_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    import_service: ImportService = Depends(get_import_service)
):
    """获取导入日志列表"""
    try:
        logs, total = import_service.get_import_logs(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        total_pages = (total + page_size - 1) // page_size

        return ImportLogListResponse(
            import_logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        return error_response(500, f"获取导入日志失败: {str(e)}")

@router.get("/logs/{log_id}", response_model=ImportLogResponse)
async def get_import_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    import_service: ImportService = Depends(get_import_service)
):
    """获取导入日志详情"""
    try:
        import_log = import_service.get_import_log(
            user_id=current_user.id,
            log_id=log_id
        )

        return import_log

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"获取导入日志失败: {str(e)}")

@router.get("/logs/{log_id}/download-errors")
async def download_error_details(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    import_service: ImportService = Depends(get_import_service)
):
    """下载错误详情"""
    try:
        import_log = import_service.get_import_log(
            user_id=current_user.id,
            log_id=log_id
        )

        if not import_log.error_details:
            raise HTTPException(status_code=404, detail="无错误详情")

        # 生成CSV格式的错误详情
        csv_content = _generate_error_csv(import_log.error_details)

        # 创建文件流
        def iterfile():
            yield csv_content.encode('utf-8')

        return StreamingResponse(
            iterfile(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=import_errors_{log_id}.csv"}
        )

    except NotFoundError as e:
        return error_response(404, str(e))
    except Exception as e:
        return error_response(500, f"下载错误详情失败: {str(e)}")

@router.get("/templates/wechat")
async def download_wechat_template():
    """下载微信账单模板说明"""
    try:
        template_content = """微信账单导入模板说明

1. 文件格式要求：
   - 必须为CSV格式文件
   - 文件编码：UTF-8或GBK
   - 文件大小：不超过10MB

2. 必需字段：
   - 交易时间：格式为"YYYY年MM月DD日 HH:MM:SS"
   - 交易类型：如"微信红包"、"转账"、"普通消费"等
   - 金额(元)：数值格式，支持正负数

3. 可选字段：
   - 交易对方：商户或交易对象名称
   - 商品说明：交易描述
   - 收/付款方式：如"零钱"、"银行卡"等
   - 交易单号：微信唯一标识
   - 备注：额外说明信息

4. 注意事项：
   - 确保数据格式正确
   - 交易时间必须有效
   - 金额字段必须为数字
   - 避免重复导入相同交易

示例数据：
交易时间,交易类型,交易对方,商品说明,收/付款方式,金额(元),交易单号,备注
2024年01月15日 12:30:45,普通消费,美团外卖,午餐订单,零钱,-25.50,1000012345678901234567890123456,
2024年01月15日 14:20:33,二维码收款,张三,转账,零钱,100.00,2000012345678901234567890123456,
"""

        def iterfile():
            yield template_content.encode('utf-8')

        return StreamingResponse(
            iterfile(),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=wechat_bill_template.txt"}
        )

    except Exception as e:
        return error_response(500, f"下载模板失败: {str(e)}")

@router.post("/validate")
async def validate_import_file(
    file: UploadFile = File(..., description="要验证的文件"),
    current_user: User = Depends(get_current_active_user),
    wechat_service: WeChatBillService = Depends(get_wechat_service)
):
    """验证导入文件格式"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.csv'):
            return error_response(400, "请上传CSV格式文件")

        # 读取文件内容
        content = await file.read()

        # 验证文件格式
        is_valid, error_message = wechat_service.validate_csv_format(content, file.filename)

        if is_valid:
            # 获取文件摘要信息
            summary = wechat_service.get_csv_summary(content)
            return success_response(
                message="文件格式验证通过",
                data={
                    "valid": True,
                    "summary": summary,
                    "file_size": len(content)
                }
            )
        else:
            return error_response(400, error_message)

    except Exception as e:
        return error_response(500, f"验证失败: {str(e)}")

def _generate_error_csv(error_details: List[dict]) -> str:
    """生成错误详情CSV"""
    if not error_details:
        return ""

    lines = ["行号,错误类型,错误消息,原始数据"]

    for error in error_details:
        # 将原始数据转换为字符串
        raw_data = str(error.get('row_data', {}))
        # 清理CSV特殊字符
        raw_data = raw_data.replace('"', '""')
        raw_data = f'"{raw_data}"'

        line = f"{error.get('row_number', '')},{error.get('error_type', '')},{error.get('error_message', '')},{raw_data}"
        lines.append(line)

    return "\n".join(lines)