import csv
import io
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal, InvalidOperation
import chardet

from app.models.transaction import TransactionType, TransactionSource
from app.schemas.import_log import ImportPreview, ImportErrorDetail

class WeChatBillService:
    """微信账单解析服务"""

    def __init__(self):
        # 微信账单字段映射
        self.field_mapping = {
            "交易时间": "transaction_time",
            "交易类型": "transaction_type",
            "交易对方": "counterparty",
            "商品说明": "description",
            "收/付款方式": "payment_method",
            "金额(元)": "amount",
            "交易单号": "transaction_id",
            "商户单号": "merchant_order_id",
            "备注": "remark"
        }

        # 微信交易类型映射
        self.transaction_type_mapping = {
            "微信红包": TransactionType.EXPENSE,
            "转账": TransactionType.TRANSFER,
            "普通消费": TransactionType.EXPENSE,
            "二维码收款": TransactionType.INCOME,
            "扫码支付": TransactionType.EXPENSE,
            "商户消费": TransactionType.EXPENSE,
            "充值": TransactionType.EXPENSE,
            "提现": TransactionType.EXPENSE,
            "退款": TransactionType.INCOME,
            "转入": TransactionType.INCOME,
            "转出": TransactionType.EXPENSE,
            "理财产品申购": TransactionType.EXPENSE,
            "理财产品赎回": TransactionType.INCOME,
            "理财收益": TransactionType.INCOME,
            "信用卡还款": TransactionType.EXPENSE,
            "群收款": TransactionType.INCOME,
            "群付款": TransactionType.EXPENSE,
            "亲属卡消费": TransactionType.EXPENSE,
            "亲属卡充值": TransactionType.EXPENSE,
            "亲属卡还款": TransactionType.INCOME,
        }

    def parse_csv_content(self, csv_content: str) -> ImportPreview:
        """
        解析微信CSV账单内容

        Args:
            csv_content: CSV文件内容

        Returns:
            导入预览信息
        """
        try:
            # 检测文件编码
            encoding = self._detect_encoding(csv_content.encode('latin1'))

            # 重新解码内容
            if encoding == 'utf-8':
                content = csv_content
            else:
                content = csv_content.encode('latin1').decode(encoding)

            # 处理BOM
            if content.startswith('\ufeff'):
                content = content[1:]

            # 解析CSV
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)

            # 查找数据开始行
            header_row_index = self._find_header_row(rows)
            if header_row_index == -1:
                raise ValueError("未找到有效的账单数据行，请确认文件格式是否正确")

            # 解析表头
            headers = rows[header_row_index]
            data_rows = rows[header_row_index + 1:]

            # 跳过空行和总结行
            data_rows = [row for row in data_rows if row and len(row) > 3 and not row[0].startswith('总')]

            # 解析交易数据
            parsed_transactions = []
            error_details = []
            potential_duplicates = 0

            for i, row in enumerate(data_rows):
                try:
                    transaction_data = self._parse_transaction_row(headers, row)
                    if transaction_data:
                        # 检查是否为重复交易（基于时间、金额和描述）
                        if self._is_potential_duplicate(transaction_data, parsed_transactions):
                            potential_duplicates += 1
                            transaction_data['is_potential_duplicate'] = True
                        else:
                            transaction_data['is_potential_duplicate'] = False

                        parsed_transactions.append(transaction_data)
                except Exception as e:
                    error_details.append(ImportErrorDetail(
                        row_number=header_row_index + i + 2,
                        error_type="解析错误",
                        error_message=str(e),
                        row_data={"原始数据": row}
                    ))

            return ImportPreview(
                filename="wechat_bill.csv",
                total_records=len(parsed_transactions),
                preview_data=parsed_transactions[:10],  # 预览前10条
                detected_format="微信账单CSV",
                potential_duplicates=potential_duplicates
            )

        except Exception as e:
            raise ValueError(f"解析微信账单失败: {str(e)}")

    def _detect_encoding(self, content: bytes) -> str:
        """检测文件编码"""
        try:
            result = chardet.detect(content)
            encoding = result['encoding']

            # 常见编码映射
            encoding_map = {
                'GB2312': 'gbk',
                'GBK': 'gbk',
                'UTF-8-SIG': 'utf-8',
                'ascii': 'utf-8'
            }

            return encoding_map.get(encoding, encoding or 'utf-8')
        except:
            return 'utf-8'

    def _find_header_row(self, rows: List[List[str]]) -> int:
        """查找表头行"""
        for i, row in enumerate(rows):
            if len(row) >= 5:
                # 检查是否包含关键字段
                row_text = ' '.join(row)
                if any(keyword in row_text for keyword in ["交易时间", "交易类型", "金额"]):
                    return i
        return -1

    def _parse_transaction_row(self, headers: List[str], row: List[str]) -> Optional[Dict[str, Any]]:
        """解析单行交易数据"""
        if len(row) < len(headers):
            return None

        # 构建字段映射
        transaction = {}
        for i, header in enumerate(headers):
            if i < len(row) and header.strip():
                english_header = self.field_mapping.get(header.strip(), header.strip())
                transaction[english_header] = row[i].strip()

        # 解析交易时间
        transaction_time = self._parse_transaction_time(transaction.get('transaction_time', ''))
        if not transaction_time:
            raise ValueError("交易时间格式错误")

        # 解析交易类型
        transaction_type = self._map_transaction_type(transaction.get('transaction_type', ''))
        if not transaction_type:
            raise ValueError(f"无法识别的交易类型: {transaction.get('transaction_type', '')}")

        # 解析金额
        amount = self._parse_amount(transaction.get('amount', ''))
        if amount is None:
            raise ValueError("金额格式错误")

        return {
            'transaction_time': transaction_time,
            'transaction_type': transaction_type,
            'counterparty': transaction.get('counterparty', ''),
            'description': transaction.get('description', ''),
            'payment_method': transaction.get('payment_method', ''),
            'amount': amount,
            'transaction_id': transaction.get('transaction_id', ''),
            'merchant_order_id': transaction.get('merchant_order_id', ''),
            'remark': transaction.get('remark', ''),
            'original_category': transaction.get('transaction_type', ''),
            'merchant_name': transaction.get('counterparty', ''),
            'pay_method': transaction.get('payment_method', ''),
        }

    def _parse_transaction_time(self, time_str: str) -> Optional[datetime]:
        """解析交易时间"""
        if not time_str:
            return None

        # 常见的时间格式
        time_formats = [
            "%Y年%m月%d日 %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y%m%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M",
        ]

        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        return None

    def _map_transaction_type(self, wechat_type: str) -> Optional[TransactionType]:
        """映射微信交易类型到系统交易类型"""
        if not wechat_type:
            return None

        return self.transaction_type_mapping.get(wechat_type)

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """解析金额"""
        if not amount_str:
            return None

        # 移除常见的金额符号和空格
        clean_amount = re.sub(r'[￥¥,\s]', '', amount_str.strip())

        # 处理正负号
        is_negative = False
        if clean_amount.startswith('-'):
            is_negative = True
            clean_amount = clean_amount[1:]
        elif clean_amount.startswith('+'):
            clean_amount = clean_amount[1:]

        try:
            amount = Decimal(clean_amount)
            return -amount if is_negative else amount
        except InvalidOperation:
            return None

    def _is_potential_duplicate(self, new_transaction: Dict[str, Any], existing_transactions: List[Dict[str, Any]]) -> bool:
        """检查是否为潜在重复交易"""
        for existing in existing_transactions:
            # 相同时间（1分钟内）、相同金额、相同描述认为是重复
            if (abs((new_transaction['transaction_time'] - existing['transaction_time']).total_seconds()) < 60 and
                new_transaction['amount'] == existing['amount'] and
                new_transaction['description'] == existing['description']):
                return True
        return False

    def validate_csv_format(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        验证CSV文件格式

        Args:
            file_content: 文件内容
            filename: 文件名

        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查文件扩展名
            if not filename.lower().endswith('.csv'):
                return False, "文件格式错误，请上传CSV格式文件"

            # 检查文件大小（限制10MB）
            if len(file_content) > 10 * 1024 * 1024:
                return False, "文件过大，请上传小于10MB的文件"

            # 解码文件内容
            encoding = self._detect_encoding(file_content)
            content = file_content.decode(encoding)

            # 处理BOM
            if content.startswith('\ufeff'):
                content = content[1:]

            # 检查是否为CSV格式
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)

            if not rows:
                return False, "文件为空或格式错误"

            # 查找表头行
            header_row_index = self._find_header_row(rows)
            if header_row_index == -1:
                return False, "未找到有效的微信账单表头，请确认文件格式是否正确"

            # 检查表头是否包含必要字段
            headers = rows[header_row_index]
            required_fields = ["交易时间", "交易类型", "金额"]
            header_text = ' '.join(headers)

            for field in required_fields:
                if field not in header_text:
                    return False, f"缺少必要字段: {field}"

            # 检查数据行数量
            data_rows = rows[header_row_index + 1:]
            valid_rows = [row for row in data_rows if row and len(row) > 3 and not row[0].startswith('总')]

            if not valid_rows:
                return False, "未找到有效的交易数据"

            return True, "文件格式验证通过"

        except UnicodeDecodeError:
            return False, "文件编码错误，请使用UTF-8或GBK编码"
        except Exception as e:
            return False, f"文件验证失败: {str(e)}"

    def get_csv_summary(self, file_content: bytes) -> Dict[str, Any]:
        """
        获取CSV文件摘要信息

        Args:
            file_content: 文件内容

        Returns:
            文件摘要信息
        """
        try:
            encoding = self._detect_encoding(file_content)
            content = file_content.decode(encoding)

            if content.startswith('\ufeff'):
                content = content[1:]

            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)

            header_row_index = self._find_header_row(rows)
            if header_row_index == -1:
                return {"error": "未找到有效数据"}

            headers = rows[header_row_index]
            data_rows = rows[header_row_index + 1:]
            valid_rows = [row for row in data_rows if row and len(row) > 3 and not row[0].startswith('总')]

            # 分析数据
            total_amount = Decimal('0')
            income_count = 0
            expense_count = 0
            transaction_types = {}

            for row in valid_rows:
                try:
                    transaction_data = self._parse_transaction_row(headers, row)
                    if transaction_data:
                        amount = transaction_data['amount']
                        transaction_type = transaction_data['transaction_type']
                        original_type = transaction_data['original_category']

                        total_amount += amount

                        if transaction_type == TransactionType.INCOME:
                            income_count += 1
                        else:
                            expense_count += 1

                        # 统计交易类型
                        if original_type not in transaction_types:
                            transaction_types[original_type] = {"count": 0, "amount": Decimal('0')}
                        transaction_types[original_type]["count"] += 1
                        transaction_types[original_type]["amount"] += amount

                except:
                    continue

            return {
                "total_transactions": len(valid_rows),
                "income_count": income_count,
                "expense_count": expense_count,
                "total_amount": float(total_amount),
                "transaction_types": {
                    k: {"count": v["count"], "amount": float(v["amount"])}
                    for k, v in transaction_types.items()
                },
                "date_range": self._get_date_range(headers, valid_rows)
            }

        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}

    def _get_date_range(self, headers: List[str], rows: List[List[str]]) -> Dict[str, str]:
        """获取交易日期范围"""
        dates = []

        for row in rows:
            try:
                transaction_data = self._parse_transaction_row(headers, row)
                if transaction_data and transaction_data['transaction_time']:
                    dates.append(transaction_data['transaction_time'])
            except:
                continue

        if not dates:
            return {}

        min_date = min(dates)
        max_date = max(dates)

        return {
            "start_date": min_date.strftime("%Y-%m-%d"),
            "end_date": max_date.strftime("%Y-%m-%d")
        }