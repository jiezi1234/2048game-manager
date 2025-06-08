-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS game2048 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建用户并设置密码
CREATE USER IF NOT EXISTS 'manager2048'@'localhost' 
    IDENTIFIED BY '2147483647';

-- 授予用户对 game2048 数据库的全部权限
GRANT ALL PRIVILEGES ON game2048.* TO 'manager2048'@'localhost';
FLUSH PRIVILEGES;

-- 切换到 game2048 数据库
USE game2048;


-- 创建user表
CREATE TABLE IF NOT EXISTS user (
    uid INT PRIMARY KEY AUTO_INCREMENT,
    username CHAR(50) NOT NULL UNIQUE,
    password CHAR(64) NOT NULL,
    blocked BOOLEAN NOT NULL DEFAULT FALSE, 
    is_admin BOOLEAN NOT NULL DEFAULT FALSE 
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

-- 创建对战房间表
CREATE TABLE IF NOT EXISTS battle_room (
    room_id VARCHAR(8) PRIMARY KEY,
    uid1 INT NOT NULL,
    uid2 INT,
    started BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (uid1) REFERENCES user(uid) ON DELETE CASCADE,
    FOREIGN KEY (uid2) REFERENCES user(uid) ON DELETE CASCADE
);

-- 创建对战状态表
CREATE TABLE IF NOT EXISTS battle_state (
    state_id INT PRIMARY KEY AUTO_INCREMENT,
    room_id VARCHAR(8) NOT NULL,
    uid INT NOT NULL,
    score INT NOT NULL,
    steps INT NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (room_id) REFERENCES battle_room(room_id) ON DELETE CASCADE,
    FOREIGN KEY (uid) REFERENCES user(uid) ON DELETE CASCADE,
    UNIQUE KEY unique_room_user (room_id, uid)
);