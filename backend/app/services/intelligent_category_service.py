import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from app.models.category import CategoryType
from app.models.transaction import TransactionType
from sqlalchemy.orm import Session
from app.models.category import Category

class IntelligentCategoryService:
    """智能分类服务"""

    def __init__(self, db: Session):
        self.db = db
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化分类规则"""
        # 基于商户名称的关键词映射
        self.merchant_keywords = {
            # 餐饮类
            CategoryType.EXPENSE: {
                "餐饮": [
                    "餐厅", "饭店", "酒楼", "食堂", "餐厅", "面馆", "粥店", "烧烤", "火锅",
                    "麦当劳", "肯德基", "汉堡王", "必胜客", "星巴克", "瑞幸咖啡", "喜茶",
                    "奶茶", "咖啡", "果汁", "饮料", "零食", "小吃", "快餐", "外卖",
                    "美团", "饿了么", "盒马", "叮咚买菜", "每日优鲜"
                ],
                "超市": [
                    "超市", "便利店", "沃尔玛", "家乐福", "大润发", "永辉超市", "物美",
                    "7-11", "全家", "罗森", "喜士多", "美宜佳"
                ]
            },

            # 交通类
            CategoryType.EXPENSE: {
                "交通": [
                    "滴滴", "曹操", "神州", "首汽", "出租车", "网约车", "公交", "地铁",
                    "火车", "高铁", "飞机", "携程", "去哪儿", "飞猪", "高德地图",
                    "百度地图", "加油", "停车费", "过路费", "打车", "租车"
                ]
            },

            # 购物类
            CategoryType.EXPENSE: {
                "购物": [
                    "淘宝", "天猫", "京东", "拼多多", "苏宁", "国美", "亚马逊", "唯品会",
                    "衣服", "鞋帽", "化妆品", "护肤品", "电子产品", "家电", "家具",
                    "百货", "商场", "购物", "服装", "手机", "电脑", "相机"
                ]
            },

            # 娱乐类
            CategoryType.EXPENSE: {
                "娱乐": [
                    "电影", "KTV", "酒吧", "游戏", "视频", "音乐", "书店", "运动",
                    "健身房", "游泳", "瑜伽", "舞蹈", "演唱会", "展览", "博物馆"
                ]
            },

            # 医疗类
            CategoryType.EXPENSE: {
                "医疗": [
                    "医院", "诊所", "药店", "体检", "看病", "拿药", "医疗", "健康",
                    "挂号费", "诊金", "药费", "体检费"
                ]
            },

            # 教育类
            CategoryType.EXPENSE: {
                "教育": [
                    "学费", "培训", "课程", "书籍", "文具", "考试", "考证",
                    "新东方", "学而思", "作业帮", "猿辅导", "腾讯课堂"
                ]
            },

            # 居住类
            CategoryType.EXPENSE: {
                "居住": [
                    "房租", "物业", "水电", "燃气", "宽带", "话费", "网费",
                    "装修", "家具", "家电维修", "物业费", "水费", "电费"
                ]
            },

            # 收入类
            CategoryType.INCOME: {
                "工资": [
                    "工资", "薪金", "薪水", "年终奖", "绩效", "补贴", "津贴"
                ],
                "投资收益": [
                    "理财", "基金", "股票", "债券", "收益", "分红", "利息"
                ],
                "礼金": [
                    "红包", "礼金", "转账", "还款", "退款", "奖金"
                ]
            }
        }

        # 支付方式映射
        self.payment_method_mapping = {
            "微信支付": "wechat",
            "支付宝": "alipay",
            "银行卡": "bank",
            "信用卡": "credit_card",
            "现金": "cash",
            "零钱": "wechat_change",
            "零钱通": "wechat_fund"
        }

    def categorize_transaction(
        self,
        merchant_name: str,
        description: str,
        transaction_type: TransactionType,
        user_id: Optional[int] = None
    ) -> Optional[Category]:
        """
        智能分类交易

        Args:
            merchant_name: 商户名称
            description: 交易描述
            transaction_type: 交易类型
            user_id: 用户ID（用于用户自定义分类学习）

        Returns:
            匹配的分类对象
        """
        if not merchant_name and not description:
            return None

        # 构建搜索文本
        search_text = f"{merchant_name or ''} {description or ''}".lower()

        # 根据交易类型选择分类规则
        if transaction_type == TransactionType.EXPENSE:
            return self._categorize_expense(search_text, user_id)
        elif transaction_type == TransactionType.INCOME:
            return self._categorize_income(search_text, user_id)
        else:
            # 转账通常不涉及分类
            return None

    def _categorize_expense(self, search_text: str, user_id: Optional[int] = None) -> Optional[Category]:
        """分类支出交易"""
        rules = self.merchant_keywords.get(CategoryType.EXPENSE, {})

        # 计算每个类别的匹配分数
        category_scores = {}

        for category_name, keywords in rules.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in search_text:
                    score += 1
                    # 完全匹配加分
                    if keyword.lower() == search_text.strip():
                        score += 2

            if score > 0:
                category_scores[category_name] = score

        if not category_scores:
            return None

        # 选择得分最高的类别
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]

        # 查找对应的分类
        return self._find_category_by_name(best_category, CategoryType.EXPENSE, user_id)

    def _categorize_income(self, search_text: str, user_id: Optional[int] = None) -> Optional[Category]:
        """分类收入交易"""
        rules = self.merchant_keywords.get(CategoryType.INCOME, {})

        # 计算每个类别的匹配分数
        category_scores = {}

        for category_name, keywords in rules.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in search_text:
                    score += 1
                    # 完全匹配加分
                    if keyword.lower() == search_text.strip():
                        score += 2

            if score > 0:
                category_scores[category_name] = score

        if not category_scores:
            return None

        # 选择得分最高的类别
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]

        # 查找对应的分类
        return self._find_category_by_name(best_category, CategoryType.INCOME, user_id)

    def _find_category_by_name(
        self,
        category_name: str,
        category_type: CategoryType,
        user_id: Optional[int] = None
    ) -> Optional[Category]:
        """查找分类"""
        query = self.db.query(Category).filter(
            Category.name == category_name,
            Category.type == category_type
        )

        if user_id:
            # 优先查找用户自定义分类
            query = query.filter(Category.user_id == user_id)
            category = query.first()
            if category:
                return category

            # 如果没有用户分类，查找系统分类
            query = self.db.query(Category).filter(
                Category.name == category_name,
                Category.type == category_type,
                Category.is_system == True
            )
        else:
            # 只查找系统分类
            query = query.filter(Category.is_system == True)

        return query.first()

    def suggest_category(
        self,
        merchant_name: str,
        description: str,
        transaction_type: TransactionType,
        user_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Dict[str, any]]:
        """
        建议分类（返回多个可能的分类及其置信度）

        Args:
            merchant_name: 商户名称
            description: 交易描述
            transaction_type: 交易类型
            user_id: 用户ID
            limit: 返回结果数量限制

        Returns:
            分类建议列表
        """
        if not merchant_name and not description:
            return []

        search_text = f"{merchant_name or ''} {description or ''}".lower()

        # 根据交易类型选择规则
        if transaction_type == TransactionType.EXPENSE:
            rules = self.merchant_keywords.get(CategoryType.EXPENSE, {})
        elif transaction_type == TransactionType.INCOME:
            rules = self.merchant_keywords.get(CategoryType.INCOME, {})
        else:
            return []

        # 计算所有类别的匹配分数
        category_scores = {}

        for category_name, keywords in rules.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in search_text:
                    score += 1
                    matched_keywords.append(keyword)
                    # 完全匹配加分
                    if keyword.lower() == search_text.strip():
                        score += 2

            if score > 0:
                category_scores[category_name] = {
                    "score": score,
                    "matched_keywords": matched_keywords
                }

        if not category_scores:
            return []

        # 按分数排序
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:limit]

        # 构建建议结果
        suggestions = []
        for category_name, score_info in sorted_categories:
            category = self._find_category_by_name(
                category_name,
                CategoryType.EXPENSE if transaction_type == TransactionType.EXPENSE else CategoryType.INCOME,
                user_id
            )

            if category:
                suggestions.append({
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "type": category.type,
                        "icon": category.icon,
                        "color": category.color
                    },
                    "confidence": min(score_info["score"] / 3, 1.0),  # 归一化置信度
                    "matched_keywords": score_info["matched_keywords"]
                })

        return suggestions

    def get_category_by_payment_method(self, payment_method: str) -> Optional[str]:
        """
        根据支付方式获取对应账户类型

        Args:
            payment_method: 支付方式

        Returns:
            账户类型名称
        """
        if not payment_method:
            return None

        payment_method_lower = payment_method.lower()

        # 直接匹配
        for method, account_type in self.payment_method_mapping.items():
            if method.lower() in payment_method_lower:
                return account_type

        # 模糊匹配
        if "微信" in payment_method_lower or "零钱" in payment_method_lower:
            return "wechat"
        elif "支付宝" in payment_method_lower:
            return "alipay"
        elif "银行卡" in payment_method_lower or "储蓄卡" in payment_method_lower:
            return "bank"
        elif "信用卡" in payment_method_lower:
            return "credit_card"
        elif "现金" in payment_method_lower:
            return "cash"

        return None

    def learn_from_user_behavior(
        self,
        user_id: int,
        merchant_name: str,
        selected_category_id: int
    ):
        """
        从用户行为中学习（简单版本：记录用户分类偏好）

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            selected_category_id: 用户选择的分类ID
        """
        # 这里可以实现更复杂的学习算法
        # 目前只是记录，实际项目中可以保存到用户偏好表
        pass

    def get_merchant_category_history(
        self,
        user_id: int,
        merchant_name: str,
        limit: int = 5
    ) -> List[Dict[str, any]]:
        """
        获取用户对该商户的历史分类记录

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            limit: 返回记录数量

        Returns:
            历史分类记录
        """
        # 这里需要查询数据库中的历史交易记录
        # 暂时返回空列表，实际项目中需要实现
        return []

    def add_custom_rule(
        self,
        user_id: int,
        keywords: List[str],
        category_id: int,
        transaction_type: TransactionType
    ):
        """
        添加自定义分类规则

        Args:
            user_id: 用户ID
            keywords: 关键词列表
            category_id: 分类ID
            transaction_type: 交易类型
        """
        # 这里需要实现自定义规则的保存和加载
        # 暂时不实现，实际项目中需要创建规则表
        pass