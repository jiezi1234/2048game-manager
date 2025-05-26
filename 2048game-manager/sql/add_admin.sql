-- 使用数据库
USE game2048;

-- 添加管理员用户
INSERT INTO user (username, password, is_admin) 
VALUES ('lmj', SHA2('lmj', 256), TRUE); 