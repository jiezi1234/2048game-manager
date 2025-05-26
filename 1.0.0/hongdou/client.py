# client.py
import json
import socket
from tkinter import Tk, Frame, Label, Button, Entry, messagebox, Toplevel
from main import Game2048

class AuthGUI:
    def __init__(self, root):
        self.root = root

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
        register_window.geometry("400x300")
        
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
                    messagebox.showinfo("成功", "登录成功！")
                    login_window.destroy()
                    
                    if user_type == "user":
                        self.root.withdraw()
                        game_window = Toplevel()
                        game = Game2048(game_window)
                        game_window.protocol("WM_DELETE_WINDOW", lambda: self.on_game_close(game))
                    else:
                        messagebox.showinfo("提示", "管理员功能开发中...")
                else:
                    messagebox.showerror("错误", response['message'])
            except Exception as e:
                messagebox.showerror("错误", f"登录失败: {str(e)}")
            finally:
                client.close()
        
        Button(frame, text='登录', font=("Helvetica", 14), width=15,
               command=do_login).pack(pady=20)

    def on_game_close(self, game):
        """处理游戏窗口关闭事件"""
        game.root.destroy()
        self.root.deiconify()

if __name__ == "__main__":
    root = Tk()
    app = AuthGUI(root)
    root.mainloop()