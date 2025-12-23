-- 添加 categories 表的 parent_id 外键约束
-- 使用方法: 在 MySQL 客户端中执行此脚本

USE finance_system;

-- 检查并添加外键约束
SET @constraint_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'categories'
      AND COLUMN_NAME = 'parent_id'
      AND REFERENCED_TABLE_NAME IS NOT NULL
);

-- 如果外键不存在，则添加
SET @sql = IF(
    @constraint_exists = 0,
    'ALTER TABLE categories ADD CONSTRAINT fk_category_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE;',
    'SELECT "外键约束已存在" AS message;'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT '迁移完成！' AS status;
