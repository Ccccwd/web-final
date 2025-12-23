"""
添加 categories 表的 parent_id 外键约束

运行方式:
    python migrations/add_category_foreign_key.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.config.database import engine

def upgrade():
    """添加外键约束"""
    with engine.begin() as conn:
        print("正在添加 categories.parent_id 外键约束...")
        
        # 检查外键是否已存在
        check_fk_sql = """
        SELECT CONSTRAINT_NAME 
        FROM information_schema.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'categories'
          AND COLUMN_NAME = 'parent_id'
          AND REFERENCED_TABLE_NAME IS NOT NULL;
        """
        
        result = conn.execute(text(check_fk_sql))
        existing_fk = result.fetchone()
        
        if existing_fk:
            print(f"外键约束已存在: {existing_fk[0]}")
            return
        
        # 添加外键约束
        alter_sql = """
        ALTER TABLE categories 
        ADD CONSTRAINT fk_category_parent 
        FOREIGN KEY (parent_id) REFERENCES categories(id) 
        ON DELETE CASCADE;
        """
        
        conn.execute(text(alter_sql))
        print("外键约束添加成功！")

def downgrade():
    """移除外键约束"""
    with engine.begin() as conn:
        print("正在移除 categories.parent_id 外键约束...")
        
        # 检查外键是否存在
        check_fk_sql = """
        SELECT CONSTRAINT_NAME 
        FROM information_schema.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'categories'
          AND COLUMN_NAME = 'parent_id'
          AND CONSTRAINT_NAME = 'fk_category_parent';
        """
        
        result = conn.execute(text(check_fk_sql))
        existing_fk = result.fetchone()
        
        if not existing_fk:
            print("外键约束不存在")
            return
        
        # 移除外键约束
        alter_sql = """
        ALTER TABLE categories 
        DROP FOREIGN KEY fk_category_parent;
        """
        
        conn.execute(text(alter_sql))
        print("外键约束移除成功！")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='迁移 categories 表外键约束')
    parser.add_argument('--downgrade', action='store_true', help='回滚迁移')
    
    args = parser.parse_args()
    
    try:
        if args.downgrade:
            downgrade()
        else:
            upgrade()
        print("\n迁移完成！")
    except Exception as e:
        print(f"\n迁移失败: {e}")
        sys.exit(1)
