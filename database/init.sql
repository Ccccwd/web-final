-- 个人财务记账系统数据库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS finance_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE finance_system;

-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密后)',
    avatar VARCHAR(255) COMMENT '头像URL',
    phone VARCHAR(20) COMMENT '手机号',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) COMMENT '用户表';

-- 分类表
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    type ENUM('income', 'expense') NOT NULL COMMENT '分类类型: 收入/支出',
    icon VARCHAR(50) COMMENT '图标(emoji)',
    color VARCHAR(20) COMMENT '颜色',
    parent_id INT NULL COMMENT '父分类ID(支持二级分类)',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统预设分类',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_type (type),
    INDEX idx_parent (parent_id)
) COMMENT '分类表';

-- 账户表
CREATE TABLE accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    name VARCHAR(50) NOT NULL COMMENT '账户名称',
    type ENUM('cash', 'bank', 'wechat', 'alipay', 'meal_card', 'credit_card', 'other') NOT NULL COMMENT '账户类型',
    balance DECIMAL(10,2) DEFAULT 0 COMMENT '当前余额',
    initial_balance DECIMAL(10,2) DEFAULT 0 COMMENT '初始余额',
    icon VARCHAR(50) COMMENT '图标',
    color VARCHAR(20) COMMENT '颜色',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认账户',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    description VARCHAR(200) COMMENT '描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_type (type)
) COMMENT '账户表';

-- 交易记录表
CREATE TABLE transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    type ENUM('income', 'expense', 'transfer') NOT NULL COMMENT '交易类型: 收入/支出/转账',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额',
    category_id INT NOT NULL COMMENT '分类ID',
    account_id INT NOT NULL COMMENT '账户ID',
    to_account_id INT NULL COMMENT '转入账户ID(转账时使用)',
    transaction_date DATETIME NOT NULL COMMENT '交易时间',
    remark VARCHAR(200) COMMENT '备注',
    images JSON COMMENT '图片URL数组',
    tags VARCHAR(200) COMMENT '标签(逗号分隔)',
    location VARCHAR(100) COMMENT '地点',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (to_account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    INDEX idx_user_date (user_id, transaction_date),
    INDEX idx_category (category_id),
    INDEX idx_account (account_id),
    INDEX idx_type (type),
    INDEX idx_date (transaction_date)
) COMMENT '交易记录表';

-- 预算表
CREATE TABLE budgets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    category_id INT NULL COMMENT '分类ID(NULL表示总预算)',
    amount DECIMAL(10,2) NOT NULL COMMENT '预算金额',
    period_type ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型: 月度/年度',
    year INT NOT NULL COMMENT '年份',
    month INT NULL COMMENT '月份(月度预算时使用)',
    alert_threshold INT DEFAULT 80 COMMENT '预警阈值(百分比)',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY uk_budget (user_id, category_id, year, month),
    INDEX idx_user_period (user_id, year, month)
) COMMENT '预算表';

-- 提醒表
CREATE TABLE reminders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    type ENUM('daily', 'budget', 'recurring', 'report') NOT NULL COMMENT '提醒类型: 每日记账/预算预警/循环提醒/分析报告',
    title VARCHAR(100) COMMENT '标题',
    content TEXT COMMENT '内容',
    remind_time TIME COMMENT '提醒时间',
    remind_day INT COMMENT '每月第几天(循环提醒)',
    category_id INT NULL COMMENT '关联分类ID(预算提醒)',
    amount DECIMAL(10,2) NULL COMMENT '固定金额提醒',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    last_reminded_at DATETIME COMMENT '最后提醒时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_user_type (user_id, type)
) COMMENT '提醒表';

-- 统计缓存表(可选,用于加速查询)
CREATE TABLE statistics_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    stat_type VARCHAR(50) NOT NULL COMMENT '统计类型: monthly_summary, category_summary等',
    period VARCHAR(20) NOT NULL COMMENT '周期: 2024-12, 2024等',
    data JSON NOT NULL COMMENT '统计数据(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_stat (user_id, stat_type, period),
    INDEX idx_user (user_id),
    INDEX idx_type_period (stat_type, period)
) COMMENT '统计缓存表';

-- 插入系统预设分类数据
INSERT INTO categories (name, type, icon, color, is_system, sort_order) VALUES
-- 支出分类
('餐饮', 'expense', '🍔', '#FF6B6B', TRUE, 1),
('交通', 'expense', '🚇', '#4ECDC4', TRUE, 2),
('娱乐', 'expense', '🎮', '#45B7D1', TRUE, 3),
('购物', 'expense', '🛒', '#96CEB4', TRUE, 4),
('学习', 'expense', '📚', '#FFEAA7', TRUE, 5),
('医疗', 'expense', '🏥', '#DFE6E9', TRUE, 6),
('居住', 'expense', '🏠', '#74B9FF', TRUE, 7),
('通讯', 'expense', '📱', '#A29BFE', TRUE, 8),
('社交', 'expense', '👥', '#FD79A8', TRUE, 9),
('美容', 'expense', '💄', '#FDCB6E', TRUE, 10),
('运动', 'expense', '🏃', '#6C5CE7', TRUE, 11),
('宠物', 'expense', '🐕', '#00B894', TRUE, 12),
('其他', 'expense', '📦', '#636E72', TRUE, 13),

-- 收入分类
('工资', 'income', '💰', '#00B894', TRUE, 1),
('奖金', 'income', '🎁', '#00CEC9', TRUE, 2),
('兼职', 'income', '💸', '#0984E3', TRUE, 3),
('投资收益', 'income', '📈', '#6C5CE7', TRUE, 4),
('红包', 'income', '🧧', '#E17055', TRUE, 5),
('退款', 'income', '💳', '#FDCB6E', TRUE, 6),
('其他', 'income', '📦', '#636E72', TRUE, 7);

-- 插入二级分类数据(餐饮子分类)
INSERT INTO categories (name, type, icon, color, parent_id, is_system, sort_order) VALUES
('早餐', 'expense', '☕', '#FF6B6B', 1, TRUE, 1),
('午餐', 'expense', '🍱', '#FF6B6B', 1, TRUE, 2),
('晚餐', 'expense', '🍽️', '#FF6B6B', 1, TRUE, 3),
('夜宵', 'expense', '🌙', '#FF6B6B', 1, TRUE, 4),
('零食', 'expense', '🍿', '#FF6B6B', 1, TRUE, 5),
('饮料', 'expense', '🥤', '#FF6B6B', 1, TRUE, 6),
('聚餐', 'expense', '🍻', '#FF6B6B', 1, TRUE, 7);

-- 插入二级分类数据(交通子分类)
INSERT INTO categories (name, type, icon, color, parent_id, is_system, sort_order) VALUES
('地铁', 'expense', '🚇', '#4ECDC4', 2, TRUE, 1),
('公交', 'expense', '🚌', '#4ECDC4', 2, TRUE, 2),
('打车', 'expense', '🚕', '#4ECDC4', 2, TRUE, 3),
('加油', 'expense', '⛽', '#4ECDC4', 2, TRUE, 4),
('停车', 'expense', '🅿️', '#4ECDC4', 2, TRUE, 5),
('高速', 'expense', '🛣️', '#4ECDC4', 2, TRUE, 6);