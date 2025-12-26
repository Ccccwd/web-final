import pandas as pd
import io
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from app.models.transaction import TransactionType

def parse_wechat_bill(content: bytes, filename: str = None) -> List[Dict[str, Any]]:
    """
    解析微信账单文件（支持CSV和XLSX格式）

    Args:
        content: 文件内容
        filename: 文件名（用于判断文件格式）

    Returns:
        交易记录列表
    """
    # 判断文件格式
    is_xlsx = filename and filename.lower().endswith('.xlsx')

    if is_xlsx:
        return parse_wechat_xlsx(content)
    else:
        return parse_wechat_csv(content)

def parse_wechat_csv(content: bytes) -> List[Dict[str, Any]]:
    """
    解析微信账单CSV文件

    Args:
        content: CSV文件内容

    Returns:
        交易记录列表
    """
    try:
        # 解码内容
        content_str = content.decode('utf-8')

        # 预处理：移除BOM，处理编码问题
        content_str = content_str.replace('\ufeff', '')

        # 读取CSV
        df = pd.read_csv(io.StringIO(content_str))

        # 清理列名
        df.columns = df.columns.str.strip()

        # 识别列名映射
        column_mapping = detect_column_mapping(df.columns.tolist())

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 数据清洗和转换
        transactions = []

        for index, row in df.iterrows():
            try:
                transaction = parse_transaction_row(row, index + 1)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                print(f"解析第 {index + 1} 行失败: {str(e)}")
                continue

        return transactions

    except Exception as e:
        raise ValueError(f"CSV文件解析失败: {str(e)}")

def detect_column_mapping(columns: List[str]) -> Dict[str, str]:
    """
    检测列名映射

    Args:
        columns: 原始列名列表

    Returns:
        列名映射字典
    """
    mapping = {}

    # 定义可能的列名模式 - 针对微信账单优化
    # 使用精确匹配优先，避免重复映射
    patterns = {
        'transaction_time': [
            '交易时间', '时间', '交易时间\xa0(北京时间)', '交易时间(北京时间)',
            '交易时间\xa0', '交易时间\xa0\xa0', '创建时间', '交易日期'
        ],
        'income_expense_type': [  # 收/支类型
            '收/支', '收支类型', '收/支\xa0'
        ],
        'transaction_type': [  # 具体交易类型
            '交易类型', '类型', '类型\xa0'
        ],
        'counterparty': [  # 交易对方
            '交易对方', '对方账户', '对方', '交易对方\xa0'
        ],
        'merchant_name': [  # 商品/商户
            '商品', '商品说明', '商品\xa0'
        ],
        'transaction_amount': [
            '金额', '金额(元)', '交易金额', '金额\xa0', '金额\xa0\xa0', '金额\xa0(元)'
        ],
        'payment_method': [
            '支付方式', '付款方式', '收/付款方式', '支付', '交易方式', '方式'
        ],
        'transaction_status': [
            '交易状态', '当前状态', '状态', '状态\xa0', '支付状态'
        ],
        'transaction_id': [
            '交易单号', '单号', '订单号', '交易号', '流水号'
        ],
        'merchant_order_id': [
            '商户单号', '商家订单号', '订单号\xa0', '商家订单号\xa0'
        ],
        'remark': [
            '备注', '说明', '附言', '备注信息', '留言'
        ]
    }

    # 已映射的字段集合，避免重复
    mapped_fields = set()

    # 先进行精确匹配
    for col in columns:
        col_stripped = col.strip()

        for field_name, pattern_list in patterns.items():
            if field_name in mapped_fields:
                continue  # 已经映射过这个字段

            if col_stripped in pattern_list:
                mapping[col] = field_name
                mapped_fields.add(field_name)
                break

    # 如果精确匹配后还有未映射的列，进行模糊匹配
    for col in columns:
        if col in mapping:
            continue  # 已经映射过

        col_lower = col.lower().strip()

        for field_name, pattern_list in patterns.items():
            if field_name in mapped_fields:
                continue  # 已经映射过这个字段

            for pattern in pattern_list:
                pattern_lower = pattern.lower()

                # 包含匹配
                if pattern_lower in col_lower or col_lower in pattern_lower:
                    mapping[col] = field_name
                    mapped_fields.add(field_name)
                    break

            if col in mapping:
                break

    return mapping

def parse_transaction_row(row: pd.Series, row_number: int) -> Dict[str, Any]:
    """
    解析单行交易数据

    Args:
        row: 数据行
        row_number: 行号

    Returns:
        交易记录字典
    """
    # 跳过空行或标题行
    if is_empty_or_header_row(row):
        return None

    # 解析交易时间
    transaction_time = parse_datetime(row.get('transaction_time'), row_number)
    if transaction_time is None:
        return None

    # 解析交易类型 - 优先使用income_expense_type（收/支），如果没有则使用transaction_type
    income_expense_str = row.get('income_expense_type') if 'income_expense_type' in row.index else None
    transaction_type_str = row.get('transaction_type') if 'transaction_type' in row.index else None

    # 使用收/支列判断类型，如果没有则使用交易类型列
    type_to_parse = income_expense_str if income_expense_str else transaction_type_str
    transaction_type = parse_transaction_type(type_to_parse)

    if transaction_type is None:
        return None

    # 解析金额
    amount = parse_amount(row.get('transaction_amount'), row_number)
    if amount is None or amount <= 0:
        return None

    # 解析商户名称 - 优先使用counterparty（交易对方），如果没有则使用merchant_name（商品）
    counterparty = row.get('counterparty') if 'counterparty' in row.index else None
    merchant_name = row.get('merchant_name') if 'merchant_name' in row.index else None

    # 使用counterparty或merchant_name，优先使用counterparty
    final_merchant_name = counterparty if counterparty else merchant_name
    final_merchant_name = parse_merchant_name(final_merchant_name)

    # 解析支付方式
    payment_method = parse_payment_method(row.get('payment_method'))

    # 解析备注
    remark = parse_remark(row.get('remark'))

    # 解析交易ID
    transaction_id = parse_transaction_id(row.get('transaction_id'))

    return {
        'transaction_time': transaction_time,
        'transaction_type': transaction_type,
        'amount': amount,
        'merchant_name': final_merchant_name,
        'payment_method': payment_method,
        'remark': remark,
        'transaction_id': transaction_id,
        'transaction_date': transaction_time.date(),
        'account_id': None,  # 需要在API层处理
        'category_id': None,  # 需要在API层处理
        'description': generate_description(final_merchant_name, payment_method, remark)
    }

def is_empty_or_header_row(row: pd.Series) -> bool:
    """
    判断是否为空行或标题行

    Args:
        row: 数据行

    Returns:
        是否为空行或标题行
    """
    # 检查是否所有列都为空或NaN
    if row.isna().all(axis=0):
        return True

    # 检查是否包含标题关键词
    text_values = [str(val) for val in row.values if pd.notna(val) and str(val).strip()]
    text = ' '.join(text_values).lower()

    header_keywords = ['交易时间', '交易类型', '金额', '商品', '支付方式', '状态']
    if any(keyword in text for keyword in header_keywords):
        return True

    return False

def parse_datetime(time_str: Any, row_number: int) -> datetime:
    """
    解析时间字符串

    Args:
        time_str: 时间字符串
        row_number: 行号

    Returns:
        datetime对象
    """
    if pd.isna(time_str) or not time_str:
        raise ValueError(f"第 {row_number} 行：交易时间为空")

    time_str = str(time_str).strip()

    # 常见时间格式
    time_formats = [
        '%Y-%m-%d %H:%M:%S',           # 2024-01-01 12:00:00
        '%Y/%m/%d %H:%M:%S',           # 2024/01/01 12:00:00
        '%Y-%m-%d %H:%M:%S.%f',        # 2024-01-01 12:00:00.000
        '%Y/%m/%d %H:%M:%S.%f',        # 2024/01/01 12:00:00.000
        '%Y年%m月%d日 %H:%M:%S',        # 2024年1月1日 12:00:00
        '%m/%d/%Y %H:%M:%S',           # 01/01/2024 12:00:00
        '%d/%m/%Y %H:%M:%S',           # 01/01/2024 12:00:00
        '%Y-%m-%d',                    # 2024-01-01
        '%Y/%m/%d',                    # 2024/01/01
    ]

    for fmt in time_formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    # 尝试使用正则表达式提取日期时间
    patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, time_str)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 6:
                    year, month, day, hour, minute, second = groups
                    return datetime(
                        int(year), int(month), int(day),
                        int(hour), int(minute), int(second)
                    )
            except (ValueError, TypeError):
                continue

    raise ValueError(f"第 {row_number} 行：无法解析时间格式 '{time_str}'")

def parse_transaction_type(type_str: Any) -> TransactionType:
    """
    解析交易类型

    Args:
        type_str: 交易类型字符串

    Returns:
        TransactionType枚举
    """
    if pd.isna(type_str) or not type_str:
        return None

    type_str = str(type_str).strip()

    # 微信账单的"收/支"列直接就是"收入"或"支出"，优先精确匹配
    if type_str == '收入':
        return TransactionType.INCOME
    if type_str == '支出':
        return TransactionType.EXPENSE

    # 其他收入类型关键词
    income_keywords = ['收入', '转入', '收款']
    if any(keyword in type_str for keyword in income_keywords):
        return TransactionType.INCOME

    # 其他支出类型关键词
    expense_keywords = ['支出', '消费', '支付', '付款']
    if any(keyword in type_str for keyword in expense_keywords):
        return TransactionType.EXPENSE

    # 默认判断：如果包含"转账"，需要根据上下文判断
    # 对于微信账单，大多数转账是支出
    if '转账' in type_str or '红包' in type_str or '提现' in type_str:
        return TransactionType.EXPENSE

    return None

def parse_amount(amount_str: Any, row_number: int) -> float:
    """
    解析金额

    Args:
        amount_str: 金额字符串
        row_number: 行号

    Returns:
        金额数值
    """
    if pd.isna(amount_str) or not amount_str:
        raise ValueError(f"第 {row_number} 行：金额为空")

    amount_str = str(amount_str).strip()

    # 移除非数字字符（保留负号、小数点）
    clean_amount = re.sub(r'[^\d.-]', '', amount_str)

    try:
        amount = float(clean_amount)
        if amount <= 0:
            raise ValueError("金额必须大于0")
        return amount
    except ValueError:
        raise ValueError(f"第 {row_number} 行：无法解析金额 '{amount_str}'")

def parse_merchant_name(merchant_str: Any) -> str:
    """
    解析商户名称

    Args:
        merchant_str: 商户名称字符串

    Returns:
        清理后的商户名称
    """
    if pd.isna(merchant_str) or not merchant_str:
        return None

    merchant_str = str(merchant_str).strip()

    # 移除常见的无效名称
    invalid_names = ['', '-', '/', 'null', 'None', 'NaN', '未知']
    if merchant_str in invalid_names:
        return None

    # 限制长度
    if len(merchant_str) > 200:
        merchant_str = merchant_str[:200]

    return merchant_str

def parse_payment_method(method_str: Any) -> str:
    """
    解析支付方式

    Args:
        method_str: 支付方式字符串

    Returns:
        清理后的支付方式
    """
    if pd.isna(method_str) or not method_str:
        return None

    method_str = str(method_str).strip()

    # 标准化支付方式名称
    method_mapping = {
        '零钱': '微信零钱',
        '银行卡': '银行卡',
        '信用卡': '信用卡',
        '借记卡': '借记卡',
        '余额': '账户余额',
    }

    for key, value in method_mapping.items():
        if key in method_str:
            return value

    return method_str

def parse_remark(remark_str: Any) -> str:
    """
    解析备注

    Args:
        remark_str: 备注字符串

    Returns:
        清理后的备注
    """
    if pd.isna(remark_str) or not remark_str:
        return None

    remark_str = str(remark_str).strip()

    # 限制长度
    if len(remark_str) > 500:
        remark_str = remark_str[:500]

    return remark_str

def parse_transaction_id(id_str: Any) -> str:
    """
    解析交易ID

    Args:
        id_str: 交易ID字符串

    Returns:
        清理后的交易ID
    """
    if pd.isna(id_str) or not id_str:
        return None

    id_str = str(id_str).strip()

    # 移除常见的无效ID
    invalid_ids = ['', '-', '/', 'null', 'None', 'NaN']
    if id_str in invalid_ids:
        return None

    # 限制长度
    if len(id_str) > 100:
        id_str = id_str[:100]

    return id_str

def generate_description(merchant_name: str, payment_method: str, remark: str) -> str:
    """
    生成交易描述

    Args:
        merchant_name: 商户名称
        payment_method: 支付方式
        remark: 备注

    Returns:
        交易描述
    """
    description_parts = []

    if merchant_name:
        description_parts.append(f"商户: {merchant_name}")

    if payment_method:
        description_parts.append(f"支付方式: {payment_method}")

    if remark:
        description_parts.append(f"备注: {remark}")

    return ' | '.join(description_parts) if description_parts else None

def validate_csv_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """
    验证CSV结构

    Args:
        df: DataFrame对象

    Returns:
        验证结果
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'columns': df.columns.tolist(),
        'row_count': len(df)
    }

    # 检查是否为空文件
    if len(df) == 0:
        result['valid'] = False
        result['errors'].append("CSV文件为空")
        return result

    # 检查列数
    if len(df.columns) < 5:
        result['warnings'].append("CSV文件列数较少，可能缺少必要信息")

    # 检查是否包含关键字段
    required_columns = ['交易时间', '交易类型', '金额']
    found_columns = []

    for col in df.columns:
        col_str = str(col).strip()
        for req_col in required_columns:
            if req_col in col_str:
                found_columns.append(req_col)
                break

    missing_columns = set(required_columns) - set(found_columns)
    if missing_columns:
        result['warnings'].append(f"未找到关键字段: {', '.join(missing_columns)}")

    # 检查数据质量
    null_percentage = (df.isnull().sum() / len(df) * 100).to_dict()

    for col, null_pct in null_percentage.items():
        if null_pct > 50:
            result['warnings'].append(f"列 '{col}' 空值率过高: {null_pct:.1f}%")

    return result

def parse_wechat_xlsx(content: bytes) -> List[Dict[str, Any]]:
    """
    解析微信账单XLSX文件

    Args:
        content: XLSX文件内容

    Returns:
        交易记录列表
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(io.BytesIO(content))

        # 微信账单xlsx文件结构：
        # 前15行是元数据
        # 第16行是分隔线
        # 第17行是表头（包含"交易时间"等列名）
        # 第18行开始是数据

        # 查找表头行（包含"交易时间"的行）
        header_row_index = None
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and '交易时间' in str(row.iloc[0]):
                header_row_index = idx
                break

        if header_row_index is None:
            raise ValueError("未找到有效的账单表头，请确认文件格式是否正确")

        # 获取表头行
        headers = df.iloc[header_row_index].tolist()

        # 获取数据行（表头行之后的所有行）
        data_df = df.iloc[header_row_index + 1:].copy()

        # 清理数据：移除完全空白的行
        data_df = data_df.dropna(how='all')

        # 设置列名
        data_df.columns = headers

        # 清理列名
        data_df.columns = data_df.columns.str.strip()

        # 识别列名映射
        column_mapping = detect_column_mapping(data_df.columns.tolist())

        # 重命名列
        data_df = data_df.rename(columns=column_mapping)

        # 数据清洗和转换
        transactions = []

        for index, row in data_df.iterrows():
            try:
                transaction = parse_transaction_row(row, index + 1)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                print(f"解析第 {index + 1} 行失败: {str(e)}")
                continue

        return transactions

    except Exception as e:
        raise ValueError(f"XLSX文件解析失败: {str(e)}")

def get_file_summary(content: bytes, filename: str) -> Dict[str, Any]:
    """
    获取文件摘要信息

    Args:
        content: 文件内容
        filename: 文件名

    Returns:
        文件摘要信息
    """
    try:
        is_xlsx = filename and filename.lower().endswith('.xlsx')

        if is_xlsx:
            df = pd.read_excel(io.BytesIO(content))

            # 查找表头行
            header_row_index = None
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]) and '交易时间' in str(row.iloc[0]):
                    header_row_index = idx
                    break

            if header_row_index is None:
                return {"error": "未找到有效数据"}

            # 获取表头和数据
            headers = df.iloc[header_row_index].tolist()
            df = df.iloc[header_row_index + 1:].copy()
            df.columns = headers
        else:
            content_str = content.decode('utf-8')
            content_str = content_str.replace('\ufeff', '')
            df = pd.read_csv(io.StringIO(content_str))

        # 清理列名
        df.columns = df.columns.str.strip()

        # 识别列名映射
        column_mapping = detect_column_mapping(df.columns.tolist())
        df = df.rename(columns=column_mapping)

        # 解析数据统计
        income_count = 0
        expense_count = 0
        total_income = 0
        total_expense = 0
        dates = []

        for index, row in df.iterrows():
            try:
                transaction = parse_transaction_row(row, index + 1)
                if transaction:
                    if transaction['transaction_type'] == TransactionType.INCOME:
                        income_count += 1
                        total_income += transaction['amount']
                    else:
                        expense_count += 1
                        total_expense += transaction['amount']

                    dates.append(transaction['transaction_time'])
            except Exception:
                continue

        # 获取日期范围
        date_range = {}
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            date_range = {
                "start_date": min_date.strftime("%Y-%m-%d"),
                "end_date": max_date.strftime("%Y-%m-%d")
            }

        return {
            "total_transactions": len(df),
            "income_count": income_count,
            "expense_count": expense_count,
            "total_income": total_income,
            "total_expense": total_expense,
            "date_range": date_range
        }

    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

    # 检查列数
    if len(df.columns) < 5:
        result['warnings'].append("CSV文件列数较少，可能缺少必要信息")

    # 检查是否包含关键字段
    required_columns = ['交易时间', '交易类型', '金额']
    found_columns = []

    for col in df.columns:
        col_str = str(col).strip()
        for req_col in required_columns:
            if req_col in col_str:
                found_columns.append(req_col)
                break

    missing_columns = set(required_columns) - set(found_columns)
    if missing_columns:
        result['warnings'].append(f"未找到关键字段: {', '.join(missing_columns)}")

    # 检查数据质量
    null_percentage = (df.isnull().sum() / len(df) * 100).to_dict()

    for col, null_pct in null_percentage.items():
        if null_pct > 50:
            result['warnings'].append(f"列 '{col}' 空值率过高: {null_pct:.1f}%")

    return result