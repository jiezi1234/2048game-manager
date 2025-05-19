import socket
import threading
import json
import mysql.connector
from mysql.connector import Error
import hashlib
import time
from datetime import datetime, timedelta

class GameServer:
    def __init__(self, host='10.29.107.164', port=20480):
        self.host = host
        self.port = port
        self.server_socket = None
        self.db_connection = None
        self.setup_database()
        
    def setup_database(self):
        """设置数据库连接"""
        try:
            self.db_connection = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                database='game2048',
                user='manager2048',
                password='2147483647'
            )
            print("成功连接到MySQL数据库")
        except Error as e:
            print(f"数据库连接错误: {e}")
            raise

    def hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_session(self, uid):
        """创建用户会话"""
        cursor = self.db_connection.cursor()
        session_id = hashlib.sha256(f"{uid}{time.time()}".encode()).hexdigest()
        created_at = datetime.now()  #会话创建时间
        expires_at = created_at + timedelta(hours=24)  #会话过期时间
        
        try:
            cursor.execute(
                "INSERT INTO session (session_id, uid, created_at, expires_at) VALUES (%s, %s, %s, %s)",
                (session_id, uid, created_at, expires_at)
            )
            self.db_connection.commit()
            return session_id
        except Error as e:
            print(f"创建会话错误: {e}")
            return None
        finally:
            cursor.close()

    def verify_session(self, session_id):
        """验证会话"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "SELECT uid FROM session WHERE session_id = %s AND expires_at > NOW()",
                (session_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    def handle_login(self, data):
        """处理登录请求"""
        cursor = self.db_connection.cursor()
        try:
            username = data.get('username')
            password = self.hash_password(data.get('password'))
            user_type = data.get('user_type')

            # 统一查询用户表
            cursor.execute(
                "SELECT uid, is_admin FROM user WHERE username = %s AND password = %s AND blocked = FALSE",
                (username, password)
            )

            result = cursor.fetchone()
            if result:
                uid, is_admin = result
                # 验证用户类型是否匹配
                if (user_type == 'admin' and not is_admin) or (user_type == 'user' and is_admin):
                    return {'status': 'error', 'message': '用户类型不匹配'}
                
                session_id = self.create_session(uid) #创建会话
                return {
                    'status': 'success',
                    'session_id': session_id,
                    'uid': uid
                }
            return {'status': 'error', 'message': '用户名或密码错误'}
        except Error as e:
            print(f"登录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def save_game_record(self, data):
        """保存游戏记录"""
        cursor = self.db_connection.cursor()
        try:
            uid = self.verify_session(data.get('session_id'))
            if not uid:
                return {'status': 'error', 'message': '无效的会话'}

            cursor.execute(
                "INSERT INTO record (uid, created_at, score, step) VALUES (%s, %s, %s, %s)",
                (uid, datetime.now(), data.get('score'), data.get('step'))
            )
            self.db_connection.commit()
            return {'status': 'success'}
        except Error as e:
            print(f"保存记录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_user_records(self, data):
        """获取用户游戏记录"""
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            uid = self.verify_session(data.get('session_id'))
            if not uid:
                return {'status': 'error', 'message': '无效的会话'}

            cursor.execute(
                "SELECT created_at, score, step FROM record WHERE uid = %s ORDER BY created_at DESC LIMIT 10",
                (uid,)
            )
            records = cursor.fetchall()
            return {
                'status': 'success',
                'records': records
            }
        except Error as e:
            print(f"获取记录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        print(f"接受来自 {address} 的连接")
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break

                request = json.loads(data.decode('utf-8'))
                action = request.get('action')
                response = None

                if action == 'login':
                    response = self.handle_login(request)
                elif action == 'save_record':
                    response = self.save_game_record(request)
                elif action == 'get_records':
                    response = self.get_user_records(request)

                if response:
                    client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"处理客户端 {address} 时出错: {e}")
        finally:
            client_socket.close()
            print(f"与 {address} 的连接已关闭")

    def start(self):
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"游戏服务器正在监听 {self.host}:{self.port}")
            
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
                
        except Exception as e:
            print(f"服务器错误: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            if self.db_connection:
                self.db_connection.close()

if __name__ == "__main__":
    server = GameServer()
    server.start()
