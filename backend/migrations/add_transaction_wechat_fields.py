"""
数据库迁移脚本：为 transactions 表添加微信导入相关字段

运行方式：
python migrations/add_transaction_wechat_fields.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.config.database import SessionLocal

def add_transaction_wechat_fields():
    """为 transactions 表添加微信导入相关字段"""

    print("开始为 transactions 表添加微信导入字段...")

    db = SessionLocal()

    try:
        # 检查字段是否已存在
        check_sql = """
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'transactions' AND column_name = 'source'
        """
        result = db.execute(text(check_sql))
        exists = result.scalar() > 0

        if exists:
            print("✓ 字段已存在，跳过迁移")
            return

        # 添加字段
        alter_sqls = [
            """
            ALTER TABLE transactions 
            ADD COLUMN source ENUM('manual', 'wechat', 'import') DEFAULT 'manual' 
            COMMENT '数据来源' AFTER location
            """,
            """
            ALTER TABLE transactions 
            ADD COLUMN wechat_transaction_id VARCHAR(100) 
            COMMENT '微信交易ID(防止重复导入)' AFTER source
            """,
            """
            ALTER TABLE transactions 
            ADD COLUMN original_category VARCHAR(100) 
            COMMENT '原始分类(如微信分类)' AFTER wechat_transaction_id
            """,
            """
            ALTER TABLE transactions 
            ADD COLUMN merchant_name VARCHAR(200) 
            COMMENT '商户名称' AFTER original_category
            """,
            """
            ALTER TABLE transactions 
            ADD COLUMN pay_method VARCHAR(50) 
            COMMENT '支付方式' AFTER merchant_name
            """,
            """
            ALTER TABLE transactions 
            ADD COLUMN is_repeated BOOLEAN DEFAULT FALSE 
            COMMENT '是否重复交易' AFTER pay_method
            """
        ]

        for sql in alter_sqls:
            try:
                db.execute(text(sql))
                print(f"✓ 执行成功: {sql.split('ADD COLUMN')[1].split()[0] if 'ADD COLUMN' in sql else 'SQL'}")
            except Exception as e:
                print(f"✗ 执行失败: {e}")

        # 添加唯一索引
        try:
            db.execute(text("""
                CREATE UNIQUE INDEX idx_wechat_transaction_id 
                ON transactions(wechat_transaction_id)
            """))
            print("✓ 创建唯一索引 idx_wechat_transaction_id")
        except Exception as e:
            print(f"✗ 创建索引失败: {e}")

        # 添加普通索引
        try:
            db.execute(text("""
                CREATE INDEX idx_transactions_source 
                ON transactions(source)
            """))
            print("✓ 创建索引 idx_transactions_source")
        except Exception as e:
            print(f"✗ 创建索引失败: {e}")

        db.commit()
        print("字段添加完成！")

    except Exception as e:
        db.rollback()
        print(f"添加字段失败: {e}")
    finally:
        db.close()

def verify_migration():
    """验证迁移结果"""

    print("\n验证迁移结果...")

    db = SessionLocal()

    try:
        # 检查所有新字段
        fields_to_check = [
            'source',
            'wechat_transaction_id',
            'original_category',
            'merchant_name',
            'pay_method',
            'is_repeated'
        ]

        for field in fields_to_check:
            check_sql = """
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'transactions' AND column_name = %s
            """
            result = db.execute(text(check_sql), {'column_name': field})
            exists = result.scalar() > 0
            status = "✓" if exists else "✗"
            print(f"{status} 字段 {field}: {'存在' if exists else '不存在'}")

    except Exception as e:
        print(f"验证失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    print("=== Transactions 表微信导入字段迁移 ===\n")

    # 执行迁移
    add_transaction_wechat_fields()

    # 验证结果
    verify_migration()

    print("\n迁移完成！")

if __name__ == "__main__":
    main()
