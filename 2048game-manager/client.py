# client.py
import json
import socket
from tkinter import Tk, Frame, Label, Button, Entry, messagebox, Toplevel
from main import Game2048
import subprocess
import sys
import os
import signal

class AuthGUI:
    def __init__(self, root):
        self.root = root
        self.admin_process = None
        self.game_window = None
        self.session_id = None

        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 启动时先检查服务器连接
        if not self.check_server_connection():
            messagebox.showerror("错误", "无法连接到服务器，请确保服务器已启动！")
            root.quit()  # 直接退出程序
            return

        self.root.title("2048游戏认证系统")
        self.root.geometry("400x500")
        self.setup_main_ui()
        
    def check_server_connection(self):
        """检查服务器是否可用"""
        try:
            # 创建临时socket连接测试
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(2)  # 设置2秒超时
            test_socket.connect(('127.0.0.1', 20480))
            test_socket.close()
            return True
        except (socket.timeout, ConnectionRefusedError) as e:
            print(f"服务器连接失败: {e}")
            return False
        except Exception as e:
            print(f"未知错误: {e}")
            return False
    
    def setup_main_ui(self):
        """设置主界面"""
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand='yes', fill='both', padx=20, pady=20)
        
        Label(self.main_frame, text='2048游戏认证系统', font=("Helvetica", 24, "bold")).pack(pady=40)
        
        buttons_frame = Frame(self.main_frame)
        buttons_frame.pack(pady=20)
        
        Button(buttons_frame, text='用户注册', font=("Helvetica", 16), width=15,
               command=self.show_register_window).pack(pady=10)
        
        Button(buttons_frame, text='用户登录', font=("Helvetica", 16), width=15,
               command=self.show_login_window).pack(pady=10)
        
        Button(buttons_frame, text='退出系统', font=("Helvetica", 16), width=15,
               command=self.root.quit).pack(pady=10)

    def show_register_window(self):
        """显示注册窗口"""
        register_window = Toplevel(self.root)
        register_window.title("用户注册")
        register_window.geometry("400x400")
        
        frame = Frame(register_window, padx=20, pady=20)
        frame.pack(expand='yes', fill='both')
        
        Label(frame, text='用户名:', font=("Helvetica", 14)).pack(pady=5)
        username_entry = Entry(frame, font=("Helvetica", 14), width=20)
        username_entry.pack(pady=5)
        
        Label(frame, text='密码:', font=("Helvetica", 14)).pack(pady=5)
        password_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        password_entry.pack(pady=5)
        
        Label(frame, text='确认密码:', font=("Helvetica", 14)).pack(pady=5)
        confirm_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        confirm_entry.pack(pady=5)
        
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
        
        Button(frame, text='注册', font=("Helvetica", 14), width=15,
               command=do_register).pack(pady=20)

    def show_login_window(self):
        """显示登录窗口"""
        login_window = Toplevel(self.root)
        login_window.title("用户登录")
        login_window.geometry("400x300")
        
        frame = Frame(login_window, padx=20, pady=20)
        frame.pack(expand='yes', fill='both')
        
        Label(frame, text='用户名:', font=("Helvetica", 14)).pack(pady=5)
        username_entry = Entry(frame, font=("Helvetica", 14), width=20)
        username_entry.pack(pady=5)
        
        Label(frame, text='密码:', font=("Helvetica", 14)).pack(pady=5)
        password_entry = Entry(frame, font=("Helvetica", 14), width=20, show="*")
        password_entry.pack(pady=5)
        
        user_type_frame = Frame(frame)
        user_type_frame.pack(pady=10)
        Label(user_type_frame, text='用户类型:', font=("Helvetica", 14)).pack(side='left', padx=5)
        
        user_type = "user"
        def set_user_type(type_):
            nonlocal user_type
            user_type = type_
        
        Button(user_type_frame, text='普通用户', font=("Helvetica", 12),
               command=lambda: set_user_type("user")).pack(side='left', padx=5)
        Button(user_type_frame, text='管理员', font=("Helvetica", 12),
               command=lambda: set_user_type("admin")).pack(side='left', padx=5)
        
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空！")
                return
                
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
                    self.session_id = response['session_id']  # 保存会话ID
                    messagebox.showinfo("成功", "登录成功！")
                    login_window.destroy()
                    
                    if user_type == "user":
                        self.root.withdraw()
                        self.game_window = Toplevel()
                        self.game_window.protocol("WM_DELETE_WINDOW", self.on_game_close)
                        game = Game2048(self.game_window)
                    else:
                        # 启动管理员界面
                        self.root.withdraw()
                        try:
                            # 获取当前脚本所在目录
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            admin_path = os.path.join(current_dir, "admin.py")
                            
                            # 使用Python解释器启动admin.py
                            self.admin_process = subprocess.Popen([sys.executable, admin_path])
                            
                            # 当管理员界面关闭时，显示主界面
                            def check_admin_closed():
                                if self.admin_process and self.admin_process.poll() is not None:
                                    # 管理员进程已结束
                                    self.admin_process = None
                                    self.root.deiconify()
                                    return
                                self.root.after(1000, check_admin_closed)
                            
                            self.root.after(1000, check_admin_closed)
                        except Exception as e:
                            messagebox.showerror("错误", f"启动管理员界面失败: {str(e)}")
                            self.root.deiconify()
                else:
                    messagebox.showerror("错误", response['message'])
            except Exception as e:
                messagebox.showerror("错误", f"登录失败: {str(e)}")
            finally:
                client.close()
        
        Button(frame, text='登录', font=("Helvetica", 14), width=15,
               command=do_login).pack(pady=20)

    def on_game_close(self):
        """处理游戏窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            try:
                # 发送登出请求
                if self.session_id:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect(('127.0.0.1', 20480))
                    request = {
                        "action": "logout",
                        "session_id": self.session_id
                    }
                    client.send(json.dumps(request).encode('utf-8'))
                    client.close()
            except:
                pass  # 忽略登出时的错误
            finally:
                if self.game_window:
                    self.game_window.destroy()
                self.session_id = None
                self.root.deiconify()

    def on_closing(self):
        """处理主窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出系统吗？"):
            try:
                # 发送登出请求
                if self.session_id:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect(('127.0.0.1', 20480))
                    request = {
                        "action": "logout",
                        "session_id": self.session_id
                    }
                    client.send(json.dumps(request).encode('utf-8'))
                    client.close()
            except:
                pass  # 忽略登出时的错误
            finally:
                # 关闭管理员进程（如果存在）
                if self.admin_process:
                    try:
                        self.admin_process.terminate()
                        self.admin_process.wait(timeout=5)
                    except:
                        self.admin_process.kill()
                # 关闭游戏窗口（如果存在）
                if self.game_window:
                    self.game_window.destroy()
                # 关闭主窗口
                self.root.quit()

if __name__ == "__main__":
    root = Tk()
    app = AuthGUI(root)
    root.mainloop()