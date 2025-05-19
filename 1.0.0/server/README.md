model.png是数据库模型图
2048gameDB.sql是在MYSQL中创建数据库时使用的脚本，已包含创建数据库和相应权限的用户的语句，其中：
host = 127.0.0.1
port = 3306
dbname  =‘game2048’
username =‘manager2048’
userpassword = ‘2147483647’


我来帮您整理一下服务器与客户端之间的通信格式。根据代码分析，主要有以下几种请求类型：
1. 登录请求 (login)
客户端发送格式：
{
    "action": "login",
    "username": "用户名",
    "password": "密码",
    "user_type": "admin/user"  // 用户类型：管理员或普通用户
}
服务器响应格式：
{
    "status": "success",
    "session_id": "会话ID",
    "uid": "用户ID"
}

// 失败情况
{
    "status": "error",
    "message": "用户名或密码错误/服务器错误"
}
2. 保存游戏记录 (save_record)
客户端发送格式：
{
    "action": "save_record",
    "session_id": "会话ID",
    "score": "游戏分数",
    "step": "游戏步数"
}
服务器响应格式：
{
    "status": "success"
}

// 失败情况
{
    "status": "error",
    "message": "无效的会话/服务器错误"
}
3. 获取游戏记录 (get_records)
客户端发送格式：
{
    "action": "get_records",
    "session_id": "会话ID"
}
服务器响应格式：
{
    "status": "success",
    "records": [
        {
            "created_at": "记录创建时间",
            "score": "游戏分数",
            "step": "游戏步数"
        },
        // ... 最多10条记录
    ]
}

// 失败情况
{
    "status": "error",
    "message": "无效的会话/服务器错误"
}
注意事项：
所有请求都需要包含 action 字段来指定操作类型
除了登录请求外，其他请求都需要提供有效的 session_id
服务器返回的 status 字段只有 "success" 和 "error" 两种状态
所有通信都使用 JSON 格式，并且使用 UTF-8 编码
游戏记录查询最多返回最近10条记录
密码在传输前应该由客户端进行 SHA-256 加密