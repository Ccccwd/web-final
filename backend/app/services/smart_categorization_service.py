from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import re
import json

from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.models.category_suggestion import CategorySuggestion, LearningRecord
from app.models.user import User
from app.schemas.import_log import CategorySuggestion as CategorySuggestionSchema
from app.core.exceptions import NotFoundError, ValidationError

class SmartCategorizationService:
    def __init__(self, db: Session):
        self.db = db

    def get_category_suggestions(
        self,
        user_id: int,
        merchant_name: str,
        limit: int = 5
    ) -> List[CategorySuggestion]:
        """
        获取分类建议

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            limit: 返回数量限制

        Returns:
            分类建议列表
        """
        suggestions = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.merchant_name.ilike(f"%{merchant_name}%")
        ).order_by(
            desc(CategorySuggestion.confidence),
            desc(CategorySuggestion.frequency),
            desc(CategorySuggestion.success_count)
        ).limit(limit).all()

        return suggestions

    def suggest_category(
        self,
        user_id: int,
        merchant_name: str,
        amount: float,
        transaction_type: TransactionType
    ) -> Optional[CategorySuggestion]:
        """
        智能分类建议

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            amount: 金额
            transaction_type: 交易类型

        Returns:
            分类建议
        """
        # 1. 精确匹配
        exact_match = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.merchant_name == merchant_name,
            CategorySuggestion.confidence >= 0.8
        ).first()

        if exact_match:
            return exact_match

        # 2. 模糊匹配
        fuzzy_match = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.merchant_name.ilike(f"%{merchant_name}%"),
            CategorySuggestion.confidence >= 0.6
        ).order_by(
            desc(CategorySuggestion.confidence),
            desc(CategorySuggestion.frequency)
        ).first()

        if fuzzy_match:
            return fuzzy_match

        # 3. 基于规则的初步建议
        rule_suggestion = self._get_rule_based_suggestion(
            user_id, merchant_name, amount, transaction_type
        )

        return rule_suggestion

    def _get_rule_based_suggestion(
        self,
        user_id: int,
        merchant_name: str,
        amount: float,
        transaction_type: TransactionType
    ) -> Optional[CategorySuggestion]:
        """
        基于规则的分类建议

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            amount: 金额
            transaction_type: 交易类型

        Returns:
            规则建议
        """
        merchant_lower = merchant_name.lower()

        # 餐饮类关键词
        restaurant_keywords = [
            '餐厅', '饭店', '咖啡', '奶茶', '甜品', '零食', '外卖',
            'restaurant', 'cafe', 'coffee', 'food', 'meal'
        ]
        if any(keyword in merchant_lower for keyword in restaurant_keywords):
            category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.name.ilike('%餐饮%') | Category.name.ilike('%食物%')
            ).first()
            if category:
                return CategorySuggestion(
                    user_id=user_id,
                    merchant_name=merchant_name,
                    category_id=category.id,
                    confidence=0.5,
                    based_on='rules'
                )

        # 交通类关键词
        transport_keywords = [
            '出租车', '公交', '地铁', '滴滴', 'uber', '打车',
            'taxi', 'bus', 'subway', 'transport'
        ]
        if any(keyword in merchant_lower for keyword in transport_keywords):
            category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.name.ilike('%交通%') | Category.name.ilike('%出行%')
            ).first()
            if category:
                return CategorySuggestion(
                    user_id=user_id,
                    merchant_name=merchant_name,
                    category_id=category.id,
                    confidence=0.6,
                    based_on='rules'
                )

        # 购物类关键词
        shopping_keywords = [
            '超市', '商场', '淘宝', '京东', '天猫', '拼多多',
            'supermarket', 'mall', 'shopping'
        ]
        if any(keyword in merchant_lower for keyword in shopping_keywords):
            category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.name.ilike('%购物%') | Category.name.ilike('%超市%')
            ).first()
            if category:
                return CategorySuggestion(
                    user_id=user_id,
                    merchant_name=merchant_name,
                    category_id=category.id,
                    confidence=0.5,
                    based_on='rules'
                )

        return None

    def record_feedback(
        self,
        user_id: int,
        transaction_id: int,
        correct_category_id: int,
        suggestion_id: Optional[int] = None,
        feedback_type: str = "confirm",
        user_notes: Optional[str] = None
    ) -> LearningRecord:
        """
        记录用户反馈

        Args:
            user_id: 用户ID
            transaction_id: 交易ID
            correct_category_id: 正确分类ID
            suggestion_id: 建议ID
            feedback_type: 反馈类型
            user_notes: 用户备注

        Returns:
            学习记录
        """
        # 获取交易信息
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not transaction:
            raise NotFoundError("交易不存在")

        # 获取原始建议
        original_suggestion = None
        confidence_before = 0.0
        if suggestion_id:
            original_suggestion = self.db.query(CategorySuggestion).filter(
                CategorySuggestion.id == suggestion_id
            ).first()
            if original_suggestion:
                confidence_before = original_suggestion.confidence

        # 创建学习记录
        learning_record = LearningRecord(
            user_id=user_id,
            transaction_id=transaction_id,
            suggestion_id=suggestion_id,
            original_category_id=transaction.category_id,
            correct_category_id=correct_category_id,
            feedback_type=feedback_type,
            confidence_before=confidence_before,
            user_notes=user_notes,
            model_version="1.0",
            learning_algorithm="user_feedback"
        )

        self.db.add(learning_record)
        self.db.commit()
        self.db.refresh(learning_record)

        # 更新建议统计
        if suggestion_id:
            self._update_suggestion_stats(
                suggestion_id, feedback_type == "confirm"
            )

        return learning_record

    def _update_suggestion_stats(self, suggestion_id: int, is_correct: bool):
        """
        更新建议统计

        Args:
            suggestion_id: 建议ID
            is_correct: 是否正确
        """
        suggestion = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.id == suggestion_id
        ).first()

        if not suggestion:
            return

        if is_correct:
            suggestion.success_count += 1
            # 提高置信度，但不超过0.95
            suggestion.confidence = min(0.95, suggestion.confidence + 0.1)
            suggestion.user_feedback = True
            suggestion.last_confirmed_at = datetime.now()
        else:
            suggestion.failure_count += 1
            # 降低置信度，但不低于0.1
            suggestion.confidence = max(0.1, suggestion.confidence - 0.05)
            suggestion.user_feedback = False

        self.db.commit()

    def update_suggestion_from_learning(
        self,
        user_id: int,
        merchant_name: str,
        category_id: int,
        confidence: float = 0.5
    ) -> CategorySuggestion:
        """
        从学习更新建议

        Args:
            user_id: 用户ID
            merchant_name: 商户名称
            category_id: 分类ID
            confidence: 置信度

        Returns:
            更新的建议
        """
        # 查找现有建议
        suggestion = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.merchant_name == merchant_name
        ).first()

        if suggestion:
            # 更新现有建议
            suggestion.category_id = category_id
            suggestion.frequency += 1
            suggestion.confidence = confidence
            suggestion.based_on = 'machine_learning'
            suggestion.last_updated_at = datetime.now()
        else:
            # 创建新建议
            suggestion = CategorySuggestion(
                user_id=user_id,
                merchant_name=merchant_name,
                category_id=category_id,
                confidence=confidence,
                frequency=1,
                based_on='machine_learning'
            )
            self.db.add(suggestion)

        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def batch_learn_from_transactions(self, user_id: int) -> int:
        """
        从现有交易批量学习

        Args:
            user_id: 用户ID

        Returns:
            学习记录数量
        """
        # 获取最近的交易
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= datetime.now() - timedelta(days=90),
            Transaction.merchant_name.isnot(None)
        ).all()

        learned_count = 0

        for transaction in recent_transactions:
            if transaction.merchant_name:
                # 更新或创建建议
                self.update_suggestion_from_learning(
                    user_id=user_id,
                    merchant_name=transaction.merchant_name,
                    category_id=transaction.category_id,
                    confidence=0.7  # 基于用户自己的交易，置信度较高
                )
                learned_count += 1

        return learned_count

    def get_learning_statistics(self, user_id: int) -> Dict:
        """
        获取学习统计信息

        Args:
            user_id: 用户ID

        Returns:
            学习统计信息
        """
        total_suggestions = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id
        ).count()

        high_confidence_suggestions = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.confidence >= 0.8
        ).count()

        total_learning_records = self.db.query(LearningRecord).filter(
            LearningRecord.user_id == user_id
        ).count()

        recent_learning = self.db.query(LearningRecord).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= datetime.now() - timedelta(days=30)
        ).count()

        # 最常出现的商户
        top_merchants = self.db.query(
            CategorySuggestion.merchant_name,
            func.sum(CategorySuggestion.frequency).label('total_frequency')
        ).filter(
            CategorySuggestion.user_id == user_id
        ).group_by(
            CategorySuggestion.merchant_name
        ).order_by(
            desc('total_frequency')
        ).limit(10).all()

        return {
            "total_suggestions": total_suggestions,
            "high_confidence_suggestions": high_confidence_suggestions,
            "total_learning_records": total_learning_records,
            "recent_learning_count": recent_learning,
            "top_merchants": [
                {"merchant_name": m[0], "frequency": m[1]} for m in top_merchants
            ]
        }

    def export_category_mappings(self, user_id: int) -> Dict[str, int]:
        """
        导出用户分类映射

        Args:
            user_id: 用户ID

        Returns:
            分类映射字典
        """
        mappings = {}
        suggestions = self.db.query(CategorySuggestion).filter(
            CategorySuggestion.user_id == user_id,
            CategorySuggestion.confidence >= 0.7
        ).all()

        for suggestion in suggestions:
            mappings[suggestion.merchant_name] = suggestion.category_id

        return mappings

    def import_category_mappings(
        self,
        user_id: int,
        mappings: Dict[str, int],
        overwrite: bool = False
    ) -> int:
        """
        导入分类映射

        Args:
            user_id: 用户ID
            mappings: 映射字典
            overwrite: 是否覆盖现有映射

        Returns:
            导入数量
        """
        imported_count = 0

        for merchant_name, category_id in mappings.items():
            existing = self.db.query(CategorySuggestion).filter(
                CategorySuggestion.user_id == user_id,
                CategorySuggestion.merchant_name == merchant_name
            ).first()

            if existing and overwrite:
                existing.category_id = category_id
                existing.confidence = 0.9  # 用户手动设置，高置信度
                existing.based_on = 'user_input'
                imported_count += 1
            elif not existing:
                suggestion = CategorySuggestion(
                    user_id=user_id,
                    merchant_name=merchant_name,
                    category_id=category_id,
                    confidence=0.9,
                    based_on='user_input'
                )
                self.db.add(suggestion)
                imported_count += 1

        self.db.commit()
        return imported_count