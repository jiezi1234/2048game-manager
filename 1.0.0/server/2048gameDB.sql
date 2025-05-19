-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS game2048 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建用户并设置密码（需替换 YOUR_PASSWORD 为实际密码）
CREATE USER IF NOT EXISTS 'manager2048'@'localhost' 
    IDENTIFIED BY '2147483647';

-- 授予用户对 game2048 数据库的全部权限
GRANT ALL PRIVILEGES ON game2048.* TO 'manager2048'@'localhost';
FLUSH PRIVILEGES;

-- 切换到 game2048 数据库
USE game2048;

-- 创建admin表
CREATE TABLE IF NOT EXISTS admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name CHAR(50) NOT NULL,
    password CHAR(50) NOT NULL
);

-- 创建user表
CREATE TABLE IF NOT EXISTS user (
    uid INT PRIMARY KEY AUTO_INCREMENT,
    username CHAR(50) NOT NULL UNIQUE,
    password CHAR(50) NOT NULL,
    blocked BOOLEAN NOT NULL DEFAULT FALSE
);

-- 创建session表
CREATE TABLE IF NOT EXISTS session (
    session_id VARCHAR(128) PRIMARY KEY,
    uid INT NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid) ON DELETE CASCADE
);

-- 创建record表
CREATE TABLE IF NOT EXISTS record (
    rid INT PRIMARY KEY AUTO_INCREMENT,
    uid INT NOT NULL,
    created_at DATETIME NOT NULL,
    score INT NOT NULL,
    step INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid) ON DELETE CASCADE
);