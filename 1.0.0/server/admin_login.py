# coding=utf-8
from tkinter import Toplevel, Tk, Frame, Label, Button, Entry, messagebox
from PIL import Image, ImageTk
import socket
import json

class AdminLogin:
    def __init__(self, root, host='127.0.0.1', port=20480):
        self.root = root
        self.server_host = host
        self.server_port = port
        self.setup_admin_login_ui()
        
    def setup_admin_login_ui(self):
        # 创建主登录框架
        self.login_frame = Frame(self.root, width=400, height=400)
        self.login_frame.pack(expand='yes', fill='both')
        
        # 标题
        Label(self.login_frame, text='管理员登录', font=("Helvetica", 24, "bold")).pack(pady=40)
        
        # 创建输入框容器
        input_frame = Frame(self.login_frame)
        input_frame.pack(pady=10)
        
        # 用户名输入框
        Label(input_frame, text='用户名:', font=("Helvetica", 14), width=8, anchor='e').grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = Entry(input_frame, font=("Helvetica", 14), width=15)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 密码输入框
        Label(input_frame, text='密码:', font=("Helvetica", 14), width=8, anchor='e').grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = Entry(input_frame, font=("Helvetica", 14), width=15, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 按钮容器
        button_frame = Frame(self.login_frame)
        button_frame.pack(pady=20)
        
        # 登录按钮
        Button(button_frame, text='登录', 
               font=("Helvetica", 16),
               width=15,
               command=self.verify_login).pack(pady=10)
        
        # 返回按钮
        Button(button_frame, text='返回', 
               font=("Helvetica", 16),
               width=15,
               command=self.go_back).pack(pady=10)
    
    def verify_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空！")
            return False
            
        try:
            # 创建socket连接
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            
            # 准备登录请求数据
            login_data = {
                'action': 'login',
                'username': username,
                'password': password,
                'user_type': 'admin'
            }
            
            # 发送登录请求
            client_socket.send(json.dumps(login_data).encode('utf-8'))
            
            # 接收服务器响应
            response = json.loads(client_socket.recv(4096).decode('utf-8'))
            client_socket.close()

            if response['status'] == 'success':
                messagebox.showinfo("成功", "登录成功！")
                self.login_frame.destroy()
                return True
            else:
                messagebox.showerror("错误", response['message'])
                return False
                
        except ConnectionRefusedError:
            messagebox.showerror("错误", "无法连接到服务器，请检查服务器是否运行！")
            return False
        except Exception as e:
            messagebox.showerror("错误", f"登录过程中发生错误：{str(e)}")
            return False
    
    def go_back(self):
        self.login_frame.destroy()
        return False

if __name__ == '__main__':
    root = Tk()
    root.title("管理员登录")
    root.geometry("400x400")
    app = AdminLogin(root)
    root.mainloop() 