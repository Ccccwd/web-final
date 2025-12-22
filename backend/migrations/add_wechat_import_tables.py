"""
数据库迁移脚本：添加微信导入相关表

运行方式：
python migrations/add_wechat_import_tables.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.config.database import engine, SessionLocal
from app.models import (
    ImportErrorRecord, CategorySuggestion, LearningRecord,
    BalanceVerification, UserPreference
)

def add_wechat_import_tables():
    """添加微信导入相关表"""

    print("开始添加微信导入相关表...")

    # 创建新表
    try:
        ImportErrorRecord.__table__.create(engine, checkfirst=True)
        print("✓ 创建 import_error_records 表")
    except Exception as e:
        print(f"✗ 创建 import_error_records 表失败: {e}")

    try:
        CategorySuggestion.__table__.create(engine, checkfirst=True)
        print("✓ 创建 category_suggestions 表")
    except Exception as e:
        print(f"✗ 创建 category_suggestions 表失败: {e}")

    try:
        LearningRecord.__table__.create(engine, checkfirst=True)
        print("✓ 创建 learning_records 表")
    except Exception as e:
        print(f"✗ 创建 learning_records 表失败: {e}")

    try:
        BalanceVerification.__table__.create(engine, checkfirst=True)
        print("✓ 创建 balance_verifications 表")
    except Exception as e:
        print(f"✗ 创建 balance_verifications 表失败: {e}")

    try:
        UserPreference.__table__.create(engine, checkfirst=True)
        print("✓ 创建 user_preferences 表")
    except Exception as e:
        print(f"✗ 创建 user_preferences 表失败: {e}")

    print("数据库表创建完成！")

def add_indexes():
    """添加性能优化索引"""

    print("开始添加索引...")

    db = SessionLocal()

    try:
        # ImportErrorRecord 索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_import_error_records_import_log_id ON import_error_records(import_log_id)",
            "CREATE INDEX IF NOT EXISTS idx_import_error_records_error_type ON import_error_records(error_type)",
            "CREATE INDEX IF NOT EXISTS idx_import_error_records_can_retry ON import_error_records(can_retry)",
        ]

        # CategorySuggestion 索引
        indexes.extend([
            "CREATE INDEX IF NOT EXISTS idx_category_suggestions_user_id ON category_suggestions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_category_suggestions_merchant_name ON category_suggestions(merchant_name)",
            "CREATE INDEX IF NOT EXISTS idx_category_suggestions_confidence ON category_suggestions(confidence)",
            "CREATE INDEX IF NOT EXISTS idx_category_suggestions_user_merchant ON category_suggestions(user_id, merchant_name)",
        ])

        # LearningRecord 索引
        indexes.extend([
            "CREATE INDEX IF NOT EXISTS idx_learning_records_user_id ON learning_records(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_records_transaction_id ON learning_records(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_records_created_at ON learning_records(created_at)",
        ])

        # BalanceVerification 索引
        indexes.extend([
            "CREATE INDEX IF NOT EXISTS idx_balance_verifications_user_id ON balance_verifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_balance_verifications_account_id ON balance_verifications(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_balance_verifications_import_log_id ON balance_verifications(import_log_id)",
            "CREATE INDEX IF NOT EXISTS idx_balance_verifications_created_at ON balance_verifications(created_at)",
        ])

        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
                print(f"✓ {index_sql}")
            except Exception as e:
                print(f"✗ 执行索引失败 {index_sql}: {e}")

        db.commit()
        print("索引添加完成！")

    except Exception as e:
        db.rollback()
        print(f"添加索引失败: {e}")
    finally:
        db.close()

def update_existing_users():
    """为现有用户添加默认偏好设置"""

    print("开始为现有用户添加默认偏好设置...")

    db = SessionLocal()

    try:
        # 检查是否已有偏好设置的用户
        existing_users_with_prefs = db.execute(
            text("SELECT COUNT(*) FROM user_preferences WHERE user_id IN (SELECT id FROM users)")
        ).scalar()

        if existing_users_with_prefs == 0:
            # 为所有现有用户创建默认偏好设置
            insert_sql = """
                INSERT INTO user_preferences (user_id, balance_verification_enabled, tolerance, created_at)
                SELECT id, true, 0.01, NOW() FROM users
                WHERE id NOT IN (SELECT user_id FROM user_preferences)
            """

            db.execute(text(insert_sql))
            db.commit()
            print("✓ 为现有用户添加了默认偏好设置")
        else:
            print("✓ 用户偏好设置已存在，跳过")

    except Exception as e:
        db.rollback()
        print(f"添加用户偏好设置失败: {e}")
    finally:
        db.close()

def check_migration():
    """检查迁移状态"""

    print("检查数据库迁移状态...")

    db = SessionLocal()

    try:
        # 检查表是否存在
        tables_to_check = [
            'import_error_records',
            'category_suggestions',
            'learning_records',
            'balance_verifications',
            'user_preferences'
        ]

        for table in tables_to_check:
            result = db.execute(text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"))
            exists = result.scalar() > 0
            status = "✓" if exists else "✗"
            print(f"{status} 表 {table}: {'存在' if exists else '不存在'}")

    except Exception as e:
        print(f"检查迁移状态失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    print("=== 微信导入功能数据库迁移 ===")

    # 检查当前状态
    check_migration()
    print()

    # 执行迁移
    add_wechat_import_tables()
    print()

    # 添加索引
    add_indexes()
    print()

    # 更新现有用户
    update_existing_users()
    print()

    # 再次检查状态
    check_migration()
    print()

    print("迁移完成！")

if __name__ == "__main__":
    main()