import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime, timedelta
import json
import socket
import threading
from tkinter import Tk, Frame, Label, Button, Entry, messagebox, Toplevel

from main import Game2048

class AuthManager:
    def __init__(self, host='127.0.0.1', port=20480):
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
            # 检查用户名是否已存在
            cursor.execute("SELECT uid FROM user WHERE username = %s", (username,))
            if cursor.fetchone():
                return {'status': 'error', 'message': '用户名已存在'}

            # 创建新用户
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
                # 验证用户类型是否匹配
                if (user_type == 'admin' and not is_admin) or (user_type == 'user' and is_admin):
                    return {'status': 'error', 'message': '用户类型不匹配'}
                
                session_id = self.create_session(uid)
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

                if response:
                    client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"处理客户端 {address} 时出错: {e}")
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

class AuthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2048游戏认证系统")
        self.root.geometry("400x500")
        self.setup_main_ui()
        
    def setup_main_ui(self):
        """设置主界面"""
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand='yes', fill='both', padx=20, pady=20)
        
        # 标题
        Label(self.main_frame, text='2048游戏认证系统', 
              font=("Helvetica", 24, "bold")).pack(pady=40)
        
        # 按钮框架
        buttons_frame = Frame(self.main_frame)
        buttons_frame.pack(pady=20)
        
        # 注册按钮
        Button(buttons_frame, text='用户注册', 
               font=("Helvetica", 16),
               width=15,
               command=self.show_register_window).pack(pady=10)
        
        # 登录按钮
        Button(buttons_frame, text='用户登录', 
               font=("Helvetica", 16),
               width=15,
               command=self.show_login_window).pack(pady=10)
        
        # 退出按钮
        Button(buttons_frame, text='退出系统', 
               font=("Helvetica", 16),
               width=15,
               command=self.root.quit).pack(pady=10)

    def show_register_window(self):
        """显示注册窗口"""
        register_window = Toplevel(self.root)
        register_window.title("用户注册")
        register_window.geometry("400x300")
        
        frame = Frame(register_window, padx=20, pady=20)
        frame.pack(expand='yes', fill='both')
        
        # 用户名输入
        Label(frame, text='用户名:', font=("Helvetica", 14)).pack(pady=5)
        username_entry = Entry(frame, font=("Helvetica", 14), width=20)
        username_entry.pack(pady=5)
        
        # 密码输入
        Label(frame, text='密码:', font=("Helvetica", 14)).pack(pady=5)
        password_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        password_entry.pack(pady=5)
        
        # 确认密码
        Label(frame, text='确认密码:', font=("Helvetica", 14)).pack(pady=5)
        confirm_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        confirm_entry.pack(pady=5)
        
        # 注册按钮
        def do_register():
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空！")
                return
                
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致！")
                return
                
            # 发送注册请求
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(('127.0.0.1', 20480))
                
                request = {
                    "action": "register",
                    "username": username,
                    "password": password,
                    "is_admin": False
                }
                
                client.send(json.dumps(request).encode('utf-8'))
                response = json.loads(client.recv(4096).decode('utf-8'))
                
                if response['status'] == 'success':
                    messagebox.showinfo("成功", "注册成功！")
                    register_window.destroy()
                else:
                    messagebox.showerror("错误", response['message'])
                    
            except Exception as e:
                messagebox.showerror("错误", f"注册失败: {str(e)}")
            finally:
                client.close()
        
        Button(frame, text='注册', 
               font=("Helvetica", 14),
               width=15,
               command=do_register).pack(pady=20)

    def show_login_window(self):
        """显示登录窗口"""
        login_window = Toplevel(self.root)
        login_window.title("用户登录")
        login_window.geometry("400x300")
        
        frame = Frame(login_window, padx=20, pady=20)
        frame.pack(expand='yes', fill='both')
        
        # 用户名输入
        Label(frame, text='用户名:', font=("Helvetica", 14)).pack(pady=5)
        username_entry = Entry(frame, font=("Helvetica", 14), width=20)
        username_entry.pack(pady=5)
        
        # 密码输入
        Label(frame, text='密码:', font=("Helvetica", 14)).pack(pady=5)
        password_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        password_entry.pack(pady=5)
        
        # 用户类型选择
        user_type_frame = Frame(frame)
        user_type_frame.pack(pady=10)
        Label(user_type_frame, text='用户类型:', font=("Helvetica", 14)).pack(side='left', padx=5)
        
        user_type = "user"
        def set_user_type(type_):
            nonlocal user_type
            user_type = type_
        
        Button(user_type_frame, text='普通用户', 
               font=("Helvetica", 12),
               command=lambda: set_user_type("user")).pack(side='left', padx=5)
        Button(user_type_frame, text='管理员', 
               font=("Helvetica", 12),
               command=lambda: set_user_type("admin")).pack(side='left', padx=5)
        
        # 登录按钮
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空！")
                return
                
            # 发送登录请求
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(('127.0.0.1', 20480))
                
                request = {
                    "action": "login",
                    "username": username,
                    "password": password,
                    "user_type": user_type
                }
                
                client.send(json.dumps(request).encode('utf-8'))
                response = json.loads(client.recv(4096).decode('utf-8'))
                
                if response['status'] == 'success':
                    messagebox.showinfo("成功", "登录成功！")
                    login_window.destroy()
                    
                    # 如果是普通用户，启动2048游戏
                    if user_type == "user":
                        self.root.withdraw()  # 隐藏认证窗口
                        game_window = Toplevel()  # 使用Toplevel代替新的Tk实例
                        game = Game2048(game_window)  # 修改Game2048的__init__以接收master参数
                        game_window.protocol("WM_DELETE_WINDOW", lambda: self.on_game_close(game))
                    # 如果是管理员，可以在这里添加管理员界面的跳转
                    else:
                        messagebox.showinfo("提示", "管理员功能开发中...")
                else:
                    messagebox.showerror("错误", response['message'])
                    
            except Exception as e:
                messagebox.showerror("错误", f"登录失败: {str(e)}")
            finally:
                client.close()
        
        Button(frame, text='登录', 
               font=("Helvetica", 14),
               width=15,
               command=do_login).pack(pady=20)

    def on_game_close(self, game):
        """处理游戏窗口关闭事件"""
        game.root.destroy()
        self.root.deiconify()  # 显示认证窗口

if __name__ == "__main__":
    # 启动认证服务器
    server_thread = threading.Thread(target=lambda: AuthManager().start())
    server_thread.daemon = True
    server_thread.start()
    
    # 启动图形界面
    root = Tk()
    app = AuthGUI(root)
    root.mainloop() 