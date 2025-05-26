# server.py
import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime, timedelta
import json
import socket
import threading
import signal
import sys

class AuthManager:
    def __init__(self, host='127.0.0.1', port=20480):
        self.host = host
        self.port = port
        self.server_socket = None
        self.db_connection = None
        self.running = True
        self.setup_database()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        print("\n正在关闭服务器...")
        self.running = False
        if self.server_socket:
            # 创建一个临时连接来解除accept的阻塞
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.connect((self.host, self.port))
                temp_socket.close()
            except:
                pass
            self.server_socket.close()
        if self.db_connection:
            self.db_connection.close()
        print("服务器已关闭")
        sys.exit(0)
        
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
        return hashlib.sha256(password.encode()).hexdigest()[:50]

    def create_session(self, uid):
        """创建用户会话"""
        cursor = self.db_connection.cursor()
        session_id = hashlib.sha256(f"{uid}{datetime.now().timestamp()}".encode()).hexdigest()
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=24)
        
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

    def register_user(self, username, password, is_admin=False):
        """注册新用户"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT uid FROM user WHERE username = %s", (username,))
            if cursor.fetchone():
                return {'status': 'error', 'message': '用户名已存在'}

            hashed_password = self.hash_password(password)
            cursor.execute(
                "INSERT INTO user (username, password, is_admin) VALUES (%s, %s, %s)",
                (username, hashed_password, is_admin)
            )
            self.db_connection.commit()
            return {'status': 'success', 'message': '注册成功'}
        except Error as e:
            print(f"注册错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def login(self, username, password, user_type='user'):
        """用户登录"""
        cursor = self.db_connection.cursor()
        try:
            hashed_password = self.hash_password(password)
            cursor.execute(
                "SELECT uid, is_admin FROM user WHERE username = %s AND password = %s AND blocked = FALSE",
                (username, hashed_password)
            )
            result = cursor.fetchone()
            
            if result:
                uid, is_admin = result
                if (user_type == 'admin' and not is_admin) or (user_type == 'user' and is_admin):
                    return {'status': 'error', 'message': '用户类型不匹配'}
                
                session_id = self.create_session(uid)
                return {
                    'status': 'success',
                    'session_id': session_id,
                    'uid': uid
                }
            return {'status': 'error', 'message': '用户名或密码错误 或者 已被封禁'}
        except Error as e:
            print(f"登录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def logout(self, session_id):
        """用户注销"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("DELETE FROM session WHERE session_id = %s", (session_id,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '注销成功'}
        except Error as e:
            print(f"注销错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_user_list(self, search_term=None):
        """获取用户列表"""
        cursor = self.db_connection.cursor()
        try:
            if search_term:
                cursor.execute(
                    "SELECT uid, username, blocked, is_admin FROM user WHERE LOWER(username) LIKE %s",
                    (f"%{search_term.lower()}%",)
                )
            else:
                cursor.execute("SELECT uid, username, blocked, is_admin FROM user")
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'uid': row[0],
                    'username': row[1],
                    'blocked': bool(row[2]),
                    'is_admin': bool(row[3])
                })
            return {'status': 'success', 'users': users}
        except Error as e:
            print(f"获取用户列表错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def ban_user(self, uid):
        """封禁用户"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("UPDATE user SET blocked = TRUE WHERE uid = %s", (uid,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '用户已封禁'}
        except Error as e:
            print(f"封禁用户错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def unban_user(self, uid):
        """解封用户"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("UPDATE user SET blocked = FALSE WHERE uid = %s", (uid,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '用户已解封'}
        except Error as e:
            print(f"解封用户错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        print(f"接受来自 {address} 的连接")
        try:
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    request = json.loads(data.decode('utf-8'))
                    action = request.get('action')
                    response = None

                    if action == 'register':
                        response = self.register_user(
                            request.get('username'),
                            request.get('password'),
                            request.get('is_admin', False)
                        )
                    elif action == 'login':
                        response = self.login(
                            request.get('username'),
                            request.get('password'),
                            request.get('user_type', 'user')
                        )
                    elif action == 'logout':
                        response = self.logout(request.get('session_id'))
                    elif action == 'get_user_list':
                        response = self.get_user_list(request.get('search_term'))
                    elif action == 'ban_user':
                        response = self.ban_user(request.get('uid'))
                    elif action == 'unban_user':
                        response = self.unban_user(request.get('uid'))

                    if response:
                        client_socket.send(json.dumps(response).encode('utf-8'))
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"处理客户端 {address} 时出错: {e}")
                    break
        finally:
            client_socket.close()
            print(f"与 {address} 的连接已关闭")

    def start(self):
        """启动认证服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"认证服务器正在监听 {self.host}:{self.port}")
            print("按 Ctrl+C 可以安全退出服务器")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1)  # 设置超时，以便能够响应关闭信号
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True  # 设置为守护线程，这样主线程退出时，这些线程也会退出
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # 只有在服务器仍在运行时才打印错误
                        print(f"接受连接时出错: {e}")
        except Exception as e:
            print(f"服务器错误: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            if self.db_connection:
                self.db_connection.close()

if __name__ == "__main__":
    server = AuthManager()
    server.start()