from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.models.category import Category
from app.models.account import Account
from app.models.import_log import ImportLog, ImportStatus
from app.schemas.import_log import (
    ImportLogCreate, ImportLogUpdate, ImportErrorDetail,
    ImportRequest, ImportResponse
)
from app.services.wechat_bill_service import WeChatBillService
from app.services.intelligent_category_service import IntelligentCategoryService
from app.services.transaction_service import TransactionService
from app.services.account_service import AccountService
from app.core.exceptions import ValidationError, NotFoundError

class ImportService:
    """批量导入服务"""

    def __init__(self, db: Session):
        self.db = db
        self.wechat_service = WeChatBillService()
        self.category_service = IntelligentCategoryService(db)
        self.transaction_service = TransactionService(db)
        self.account_service = AccountService(db)

    async def import_wechat_bill(
        self,
        user_id: int,
        import_request: ImportRequest
    ) -> ImportResponse:
        """
        导入微信账单

        Args:
            user_id: 用户ID
            import_request: 导入请求

        Returns:
            导入响应
        """
        try:
            # 创建导入日志
            import_log = self._create_import_log(
                user_id=user_id,
                source=import_request.source,
                filename=import_request.filename
            )

            # 解析CSV内容
            content = import_request.file_content
            import_preview = self.wechat_service.parse_csv_content(content)

            # 更新导入日志
            import_log.total_records = import_preview.total_records
            import_log.status = ImportStatus.PROCESSING
            self.db.commit()

            # 批量导入交易
            success_count, failed_count, errors = await self._batch_import_transactions(
                user_id=user_id,
                transactions_data=import_preview.preview_data,
                import_log_id=import_log.id,
                skip_duplicates=import_request.skip_duplicates,
                auto_categorize=import_request.auto_categorize,
                default_account_id=import_request.default_account_id
            )

            # 更新导入日志状态
            import_log.success_records = success_count
            import_log.failed_records = failed_count
            import_log.error_details = [error.dict() for error in errors]
            import_log.completed_at = datetime.utcnow()
            import_log.status = ImportStatus.SUCCESS if failed_count == 0 else ImportStatus.PARTIAL

            # 生成导入摘要
            import_log.import_summary = self._generate_import_summary(success_count, failed_count)

            self.db.commit()

            return ImportResponse(
                import_log_id=import_log.id,
                status=import_log.status,
                message=import_log.import_summary,
                total_records=import_preview.total_records,
                processed_records=success_count + failed_count
            )

        except Exception as e:
            # 更新导入日志为失败状态
            if 'import_log' in locals():
                import_log.status = ImportStatus.FAILED
                import_log.completed_at = datetime.utcnow()
                import_log.import_summary = f"导入失败: {str(e)}"
                self.db.commit()

            raise Exception(f"导入微信账单失败: {str(e)}")

    async def _batch_import_transactions(
        self,
        user_id: int,
        transactions_data: List[Dict[str, Any]],
        import_log_id: int,
        skip_duplicates: bool = True,
        auto_categorize: bool = True,
        default_account_id: Optional[int] = None
    ) -> Tuple[int, int, List[ImportErrorDetail]]:
        """
        批量导入交易记录

        Args:
            user_id: 用户ID
            transactions_data: 交易数据列表
            import_log_id: 导入日志ID
            skip_duplicates: 是否跳过重复记录
            auto_categorize: 是否自动分类
            default_account_id: 默认账户ID

        Returns:
            (成功数量, 失败数量, 错误详情)
        """
        success_count = 0
        failed_count = 0
        errors = []

        # 获取默认账户
        default_account = None
        if default_account_id:
            try:
                default_account = self.account_service.get_account(user_id, default_account_id)
            except NotFoundError:
                default_account = self.account_service.get_default_account(user_id)

        for i, transaction_data in enumerate(transactions_data):
            try:
                # 检查重复交易
                if skip_duplicates and self._is_duplicate_transaction(user_id, transaction_data):
                    errors.append(ImportErrorDetail(
                        row_number=i + 1,
                        error_type="重复交易",
                        error_message="检测到重复交易，已跳过",
                        row_data=transaction_data
                    ))
                    continue

                # 智能分类
                category = None
                if auto_categorize:
                    category = self.category_service.categorize_transaction(
                        merchant_name=transaction_data.get('merchant_name', ''),
                        description=transaction_data.get('description', ''),
                        transaction_type=transaction_data.get('transaction_type'),
                        user_id=user_id
                    )

                # 如果没有匹配的分类，使用默认分类
                if not category:
                    category = self._get_default_category(user_id, transaction_data.get('transaction_type'))

                # 选择账户
                account = default_account
                if not account:
                    # 根据支付方式选择账户
                    pay_method = transaction_data.get('pay_method', '')
                    if pay_method:
                        account = self._get_account_by_payment_method(user_id, pay_method)

                if not account:
                    raise ValidationError("无法确定交易账户")

                # 创建交易记录
                transaction = Transaction(
                    user_id=user_id,
                    type=transaction_data['transaction_type'],
                    amount=transaction_data['amount'],
                    category_id=category.id,
                    account_id=account.id,
                    to_account_id=None,  # 微信账单一般不涉及转账
                    transaction_date=transaction_data['transaction_time'],
                    remark=transaction_data.get('description', ''),
                    source=TransactionSource.WECHAT,
                    wechat_transaction_id=transaction_data.get('transaction_id'),
                    original_category=transaction_data.get('original_category'),
                    merchant_name=transaction_data.get('merchant_name'),
                    pay_method=transaction_data.get('pay_method'),
                    is_repeated=transaction_data.get('is_potential_duplicate', False)
                )

                self.db.add(transaction)
                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(ImportErrorDetail(
                    row_number=i + 1,
                    error_type="导入错误",
                    error_message=str(e),
                    row_data=transaction_data
                ))

        # 提交所有成功的交易
        if success_count > 0:
            self.db.commit()

        return success_count, failed_count, errors

    def _is_duplicate_transaction(self, user_id: int, transaction_data: Dict[str, Any]) -> bool:
        """检查是否为重复交易"""
        wechat_transaction_id = transaction_data.get('transaction_id')
        if wechat_transaction_id:
            existing = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.wechat_transaction_id == wechat_transaction_id
            ).first()
            return existing is not None

        # 如果没有交易ID，基于时间、金额和商户名称检查
        transaction_time = transaction_data.get('transaction_time')
        amount = transaction_data.get('amount')
        merchant_name = transaction_data.get('merchant_name')

        if all([transaction_time, amount, merchant_name]):
            existing = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date == transaction_time,
                Transaction.amount == amount,
                Transaction.merchant_name == merchant_name
            ).first()
            return existing is not None

        return False

    def _get_default_category(self, user_id: int, transaction_type: TransactionType) -> Category:
        """获取默认分类"""
        category_name = "其他支出" if transaction_type == TransactionType.EXPENSE else "其他收入"
        category_type = "expense" if transaction_type == TransactionType.EXPENSE else "income"

        category = self.db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == category_name,
            Category.type == category_type
        ).first()

        if not category:
            # 如果没有其他分类，查找系统分类
            category = self.db.query(Category).filter(
                Category.is_system == True,
                Category.name == category_name,
                Category.type == category_type
            ).first()

        if not category:
            raise ValidationError(f"未找到默认分类: {category_name}")

        return category

    def _get_account_by_payment_method(self, user_id: int, payment_method: str) -> Optional[Account]:
        """根据支付方式获取账户"""
        account_type = self.category_service.get_category_by_payment_method(payment_method)
        if account_type:
            accounts = self.account_service.get_accounts(user_id, account_type)
            return accounts[0] if accounts else None
        return None

    def _create_import_log(self, user_id: int, source: str, filename: str) -> ImportLog:
        """创建导入日志"""
        import_log = ImportLog(
            user_id=user_id,
            source=source,
            file_name=filename,
            status=ImportStatus.PENDING
        )

        self.db.add(import_log)
        self.db.commit()
        self.db.refresh(import_log)

        return import_log

    def _generate_import_summary(self, success_count: int, failed_count: int) -> str:
        """生成导入摘要"""
        total = success_count + failed_count
        if failed_count == 0:
            return f"成功导入 {success_count} 条交易记录"
        elif success_count == 0:
            return f"导入失败，共 {failed_count} 条记录出错"
        else:
            return f"部分成功，成功 {success_count} 条，失败 {failed_count} 条，共处理 {total} 条记录"

    def get_import_logs(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ImportLog], int]:
        """
        获取用户的导入日志

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            (导入日志列表, 总数量)
        """
        query = self.db.query(ImportLog).filter(ImportLog.user_id == user_id)

        total = query.count()
        logs = query.order_by(ImportLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return logs, total

    def get_import_log(self, user_id: int, log_id: int) -> ImportLog:
        """
        获取导入日志详情

        Args:
            user_id: 用户ID
            log_id: 日志ID

        Returns:
            导入日志
        """
        import_log = self.db.query(ImportLog).filter(
            ImportLog.id == log_id,
            ImportLog.user_id == user_id
        ).first()

        if not import_log:
            raise NotFoundError("导入日志不存在")

        return import_log

    def preview_wechat_bill(self, csv_content: str, filename: str) -> Dict[str, Any]:
        """
        预览微信账单

        Args:
            csv_content: CSV文件内容
            filename: 文件名

        Returns:
            预览信息
        """
        try:
            # 验证文件格式
            is_valid, error_message = self.wechat_service.validate_csv_format(
                csv_content.encode('latin1'), filename
            )

            if not is_valid:
                return {
                    "valid": False,
                    "error": error_message
                }

            # 解析文件
            import_preview = self.wechat_service.parse_csv_content(csv_content)

            # 获取文件摘要
            file_summary = self.wechat_service.get_csv_summary(csv_content.encode('latin1'))

            return {
                "valid": True,
                "preview": import_preview.dict(),
                "summary": file_summary
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"预览失败: {str(e)}"
            }