from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
import json

from app.models.import_log import ImportLog, ImportStatus
from app.models.import_error_record import ImportErrorRecord
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.account import Account
from app.schemas.import_log import ImportErrorDetail, ImportRetryRequest
from app.core.exceptions import NotFoundError, ValidationError

class ImportErrorAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_import_errors(self, import_log_id: int) -> Dict:
        """
        分析导入错误

        Args:
            import_log_id: 导入日志ID

        Returns:
            错误分析结果
        """
        import_log = self.db.query(ImportLog).filter(
            ImportLog.id == import_log_id
        ).first()

        if not import_log:
            raise NotFoundError("导入日志不存在")

        error_records = self.db.query(ImportErrorRecord).filter(
            ImportErrorRecord.import_log_id == import_log_id
        ).all()

        # 错误分类统计
        error_types = {}
        for record in error_records:
            error_type = record.error_type
            if error_type not in error_types:
                error_types[error_type] = {
                    "count": 0,
                    "can_retry": 0,
                    "cannot_retry": 0,
                    "examples": []
                }

            error_types[error_type]["count"] += 1
            if record.can_retry:
                error_types[error_type]["can_retry"] += 1
            else:
                error_types[error_type]["cannot_retry"] += 1

            # 只保留前3个示例
            if len(error_types[error_type]["examples"]) < 3:
                error_types[error_type]["examples"].append({
                    "row_number": record.row_number,
                    "error_message": record.error_message,
                    "suggested_fix": record.suggested_fix
                })

        # 生成修复建议
        fix_suggestions = self._generate_fix_suggestions(error_types)

        return {
            "import_log_id": import_log_id,
            "total_errors": len(error_records),
            "error_types": error_types,
            "fix_suggestions": fix_suggestions,
            "auto_fixable_count": sum(
                error_types[et]["can_retry"] for et in error_types
            ),
            "requires_manual_fix_count": sum(
                error_types[et]["cannot_retry"] for et in error_types
            )
        }

    def _generate_fix_suggestions(self, error_types: Dict) -> List[Dict]:
        """
        生成修复建议

        Args:
            error_types: 错误类型统计

        Returns:
            修复建议列表
        """
        suggestions = []

        for error_type, stats in error_types.items():
            if error_type == "INVALID_DATE_FORMAT":
                suggestions.append({
                    "error_type": error_type,
                    "affected_count": stats["count"],
                    "description": "日期格式不正确",
                    "auto_fix": True,
                    "fix_steps": [
                        "检测并转换日期格式",
                        "支持多种微信日期格式",
                        "自动修复常见格式问题"
                    ]
                })

            elif error_type == "INVALID_AMOUNT":
                suggestions.append({
                    "error_type": error_type,
                    "affected_count": stats["count"],
                    "description": "金额格式不正确",
                    "auto_fix": True,
                    "fix_steps": [
                        "清理金额中的非数字字符",
                        "转换负数格式",
                        "处理千分位分隔符"
                    ]
                })

            elif error_type == "DUPLICATE_TRANSACTION":
                suggestions.append({
                    "error_type": error_type,
                    "affected_count": stats["count"],
                    "description": "重复交易记录",
                    "auto_fix": True,
                    "fix_steps": [
                        "检测交易ID重复",
                        "检查相同时间金额的记录",
                        "根据用户设置决定跳过或覆盖"
                    ]
                })

            elif error_type == "INVALID_CATEGORY":
                suggestions.append({
                    "error_type": error_type,
                    "affected_count": stats["count"],
                    "description": "分类不存在或无效",
                    "auto_fix": True,
                    "fix_steps": [
                        "使用智能分类建议",
                        "匹配相似商户名称",
                        "创建新分类或使用默认分类"
                    ]
                })

            elif error_type == "INVALID_ACCOUNT":
                suggestions.append({
                    "error_type": error_type,
                    "affected_count": stats["count"],
                    "description": "账户不存在或无效",
                    "auto_fix": True,
                    "fix_steps": [
                        "使用默认账户",
                        "创建新账户",
                        "匹配相似账户名称"
                    ]
                })

        return suggestions

    def get_fixable_errors(self, import_log_id: int) -> List[ImportErrorRecord]:
        """
        获取可修复的错误记录

        Args:
            import_log_id: 导入日志ID

        Returns:
            可修复的错误记录列表
        """
        return self.db.query(ImportErrorRecord).filter(
            ImportErrorRecord.import_log_id == import_log_id,
            ImportErrorRecord.can_retry == True,
            ImportErrorRecord.status == "pending"
        ).all()

    def retry_import_errors(
        self,
        user_id: int,
        import_log_id: int,
        retry_request: ImportRetryRequest
    ) -> Dict:
        """
        重试导入错误记录

        Args:
            user_id: 用户ID
            import_log_id: 导入日志ID
            retry_request: 重试请求

        Returns:
            重试结果
        """
        import_log = self.db.query(ImportLog).filter(
            ImportLog.id == import_log_id,
            ImportLog.user_id == user_id
        ).first()

        if not import_log:
            raise NotFoundError("导入日志不存在")

        # 获取要重试的错误记录
        error_records = self.db.query(ImportErrorRecord).filter(
            ImportErrorRecord.import_log_id == import_log_id,
            ImportErrorRecord.can_retry == True,
            ImportErrorRecord.status == "pending"
        ).all()

        # 过滤指定的错误记录
        if retry_request.error_record_ids:
            error_ids = [r.id for r in error_records]
            error_records = [r for r in error_records if r.id in retry_request.error_record_ids]

        retry_results = []
        success_count = 0
        failed_count = 0

        for error_record in error_records:
            try:
                # 应用修正数据
                if retry_request.corrections and str(error_record.id) in retry_request.corrections:
                    correction = retry_request.corrections[str(error_record.id)]
                    error_record.raw_data.update(correction)
                    error_record.raw_data = json.dumps(error_record.raw_data)

                # 尝试重新解析和导入
                result = self._retry_single_record(error_record, user_id)

                if result["success"]:
                    success_count += 1
                    error_record.status = "resolved"
                    error_record.resolved_at = datetime.now()
                    error_record.resolution_method = "auto_retry"
                else:
                    failed_count += 1
                    error_record.retry_count += 1
                    if error_record.retry_count >= 3:  # 最多重试3次
                        error_record.can_retry = False

                retry_results.append({
                    "error_record_id": error_record.id,
                    "row_number": error_record.row_number,
                    "success": result["success"],
                    "message": result["message"]
                })

            except Exception as e:
                failed_count += 1
                error_record.retry_count += 1
                retry_results.append({
                    "error_record_id": error_record.id,
                    "row_number": error_record.row_number,
                    "success": False,
                    "message": f"重试失败: {str(e)}"
                })

        self.db.commit()

        # 更新导入日志状态
        import_log.success_records += success_count
        import_log.failed_records = max(0, import_log.failed_records - success_count)

        if failed_count == 0 and import_log.failed_records == 0:
            import_log.status = ImportStatus.SUCCESS
        elif success_count > 0:
            import_log.status = ImportStatus.PARTIAL

        import_log.completed_at = datetime.now()
        self.db.commit()

        return {
            "total_attempted": len(error_records),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": retry_results,
            "new_status": import_log.status.value
        }

    def _retry_single_record(self, error_record: ImportErrorRecord, user_id: int) -> Dict:
        """
        重试单个记录

        Args:
            error_record: 错误记录
            user_id: 用户ID

        Returns:
            重试结果
        """
        try:
            # 解析原始数据
            raw_data = error_record.raw_data
            if isinstance(raw_data, str):
                raw_data = json.loads(raw_data)

            # 根据错误类型进行相应修复
            if error_record.error_type == "INVALID_DATE_FORMAT":
                fixed_data = self._fix_date_format(raw_data)
            elif error_record.error_type == "INVALID_AMOUNT":
                fixed_data = self._fix_amount_format(raw_data)
            elif error_record.error_type == "INVALID_CATEGORY":
                fixed_data = self._fix_category(raw_data, user_id)
            elif error_record.error_type == "INVALID_ACCOUNT":
                fixed_data = self._fix_account(raw_data, user_id)
            else:
                return {
                    "success": False,
                    "message": f"不支持的错误类型: {error_record.error_type}"
                }

            # 验证修复后的数据
            validation_result = self._validate_record(fixed_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }

            return {
                "success": True,
                "message": "修复成功",
                "fixed_data": fixed_data
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"修复失败: {str(e)}"
            }

    def _fix_date_format(self, data: Dict) -> Dict:
        """修复日期格式"""
        date_str = data.get("transaction_date", "")

        # 常见微信日期格式
        date_patterns = [
            r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",  # 2024-01-01 12:00:00
            r"(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",  # 2024/01/01 12:00:00
            r"(\d{4})(\d{2})(\d{2})",  # 20240101
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                if len(match.groups()) == 6:
                    # 2024-01-01 12:00:00
                    year, month, day, hour, minute, second = match.groups()
                    formatted_date = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                elif len(match.groups()) == 3:
                    # 20240101
                    year, month, day = match.groups()
                    formatted_date = f"{year}-{month}-{day}T00:00:00"
                else:
                    continue

                data["transaction_date"] = formatted_date
                break

        return data

    def _fix_amount_format(self, data: Dict) -> Dict:
        """修复金额格式"""
        amount_str = data.get("amount", "")

        # 移除非数字字符（除了小数点和负号）
        clean_amount = re.sub(r'[^\d.-]', '', amount_str)

        try:
            amount = float(clean_amount)
            data["amount"] = amount
        except ValueError:
            # 如果转换失败，设置为0
            data["amount"] = 0.0

        return data

    def _fix_category(self, data: Dict, user_id: int) -> Dict:
        """修复分类"""
        merchant_name = data.get("merchant_name", "")
        category_id = data.get("category_id")

        # 如果没有分类ID，尝试使用智能分类
        if not category_id and merchant_name:
            from app.services.smart_categorization_service import SmartCategorizationService
            smart_service = SmartCategorizationService(self.db)

            suggestion = smart_service.get_category_suggestions(user_id, merchant_name, limit=1)
            if suggestion:
                data["category_id"] = suggestion[0].category_id

        return data

    def _fix_account(self, data: Dict, user_id: int) -> Dict:
        """修复账户"""
        account_id = data.get("account_id")

        # 如果没有账户ID，使用默认账户
        if not account_id:
            default_account = self.db.query(Account).filter(
                Account.user_id == user_id,
                Account.is_default == True,
                Account.is_enabled == True
            ).first()

            if default_account:
                data["account_id"] = default_account.id

        return data

    def _validate_record(self, data: Dict) -> Dict:
        """验证记录"""
        required_fields = ["transaction_type", "amount"]
        validation_result = {"valid": True, "message": ""}

        for field in required_fields:
            if field not in data or data[field] is None:
                validation_result = {
                    "valid": False,
                    "message": f"缺少必需字段: {field}"
                }
                break

        if validation_result["valid"]:
            # 验证金额
            try:
                amount = float(data["amount"])
                if amount < 0:
                    validation_result = {
                        "valid": False,
                        "message": "金额不能为负数"
                    }
            except (ValueError, TypeError):
                validation_result = {
                    "valid": False,
                    "message": "金额格式无效"
                }

        return validation_result

    def get_error_patterns(self, user_id: int, days: int = 30) -> Dict:
        """
        获取错误模式分析

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            错误模式分析结果
        """
        start_date = datetime.now() - timedelta(days=days)

        # 获取最近的错误记录
        error_records = self.db.query(ImportErrorRecord).join(
            ImportLog
        ).filter(
            ImportLog.user_id == user_id,
            ImportLog.created_at >= start_date,
            ImportErrorRecord.status == "pending"
        ).all()

        # 分析错误模式
        error_patterns = {}
        for record in error_records:
            pattern_key = self._extract_error_pattern(record.error_message)

            if pattern_key not in error_patterns:
                error_patterns[pattern_key] = {
                    "count": 0,
                    "first_seen": record.created_at,
                    "last_seen": record.created_at,
                    "error_types": set(),
                    "examples": []
                }

            error_patterns[pattern_key]["count"] += 1
            error_patterns[pattern_key]["error_types"].add(record.error_type)
            error_patterns[pattern_key]["last_seen"] = max(
                error_patterns[pattern_key]["last_seen"],
                record.created_at
            )

            # 只保留前2个示例
            if len(error_patterns[pattern_key]["examples"]) < 2:
                error_patterns[pattern_key]["examples"].append({
                    "error_message": record.error_message,
                    "merchant_name": record.raw_data.get("merchant_name"),
                    "row_number": record.row_number
                })

        # 转换set为list
        for pattern in error_patterns.values():
            pattern["error_types"] = list(pattern["error_types"])

        return {
            "analysis_period_days": days,
            "total_error_records": len(error_records),
            "error_patterns": error_patterns,
            "most_common_patterns": sorted(
                error_patterns.values(),
                key=lambda x: x["count"],
                reverse=True
            )[:10]
        }

    def _extract_error_pattern(self, error_message: str) -> str:
        """
        提取错误模式

        Args:
            error_message: 错误消息

        Returns:
            错误模式
        """
        # 简化错误消息，提取关键模式
        message_lower = error_message.lower()

        # 日期相关错误
        if any(keyword in message_lower for keyword in ["date", "日期", "时间"]):
            return "date_format_error"

        # 金额相关错误
        if any(keyword in message_lower for keyword in ["amount", "金额", "数字"]):
            return "amount_format_error"

        # 分类相关错误
        if any(keyword in message_lower for keyword in ["category", "分类"]):
            return "category_error"

        # 账户相关错误
        if any(keyword in message_lower for keyword in ["account", "账户"]):
            return "account_error"

        # 格式错误
        if any(keyword in message_lower for keyword in ["format", "格式"]):
            return "format_error"

        # 数据验证错误
        if any(keyword in message_lower for keyword in ["validate", "验证"]):
            return "validation_error"

        return "other_error"