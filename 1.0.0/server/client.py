import socket
import json
import hashlib
import time

class GameClient:
    def __init__(self, host='127.0.0.1', port=20480):
        self.host = host
        self.port = port
        self.session_id = None
        self.uid = None
        self.socket = None

    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print("成功连接到服务器")
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return False

    def send_request(self, request):
        """发送请求到服务器"""
        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(4096)
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            print(f"通信错误: {e}")
            return None

    def login(self, username, password, user_type='user'):
        """登录请求"""
        # 对密码进行SHA-256加密
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        request = {
            "action": "login",
            "username": username,
            "password": hashed_password,
            "user_type": user_type
        }
        
        response = self.send_request(request)
        if response and response.get('status') == 'success':
            self.session_id = response.get('session_id')
            self.uid = response.get('uid')
            print("登录成功")
            return True
        else:
            print(f"登录失败: {response.get('message') if response else '未知错误'}")
            return False

    def save_game_record(self, score, step):
        """保存游戏记录"""
        if not self.session_id:
            print("未登录，无法保存记录")
            return False

        request = {
            "action": "save_record",
            "session_id": self.session_id,
            "score": score,
            "step": step
        }
        
        response = self.send_request(request)
        if response and response.get('status') == 'success':
            print("游戏记录保存成功")
            return True
        else:
            print(f"保存记录失败: {response.get('message') if response else '未知错误'}")
            return False

    def get_game_records(self):
        """获取游戏记录"""
        if not self.session_id:
            print("未登录，无法获取记录")
            return None

        request = {
            "action": "get_records",
            "session_id": self.session_id
        }
        
        response = self.send_request(request)
        if response and response.get('status') == 'success':
            return response.get('records')
        else:
            print(f"获取记录失败: {response.get('message') if response else '未知错误'}")
            return None

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            print("已断开与服务器的连接")

# 使用示例
def main():
    # 创建客户端实例
    client = GameClient()
    
    # 连接到服务器
    if not client.connect():
        return
    
    try:
        # 登录示例
        if client.login("test_user", "password123"):
            # 保存游戏记录示例
            client.save_game_record(2048, 50)
            
            # 获取游戏记录示例
            records = client.get_game_records()
            if records:
                print("\n游戏记录:")
                for record in records:
                    print(f"时间: {record['created_at']}, 分数: {record['score']}, 步数: {record['step']}")
    
    finally:
        # 关闭连接
        client.close()

if __name__ == "__main__":
    main()
