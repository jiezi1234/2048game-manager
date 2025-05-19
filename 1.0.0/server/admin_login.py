# coding=utf-8
from tkinter import Toplevel, Tk, Frame, Label, Button, Entry, messagebox
from PIL import Image, ImageTk

class AdminLogin:
    def __init__(self, root):
        self.root = root
        self.setup_admin_login_ui()
        
    def setup_admin_login_ui(self):
        # 创建主登录框架
        self.login_frame = Frame(self.root, width=400, height=400)
        self.login_frame.pack(expand='yes', fill='both')
        
        # 标题
        Label(self.login_frame, text='管理员登录', font=("Helvetica", 24, "bold")).pack(pady=40)
        
        # 用户名输入框
        username_frame = Frame(self.login_frame)
        username_frame.pack(pady=10)
        Label(username_frame, text='用户名:', font=("Helvetica", 14)).pack(side='left', padx=5)
        self.username_entry = Entry(username_frame, font=("Helvetica", 14), width=15)
        self.username_entry.pack(side='left', padx=5)
        
        # 密码输入框
        password_frame = Frame(self.login_frame)
        password_frame.pack(pady=10)
        Label(password_frame, text='密码:', font=("Helvetica", 14)).pack(side='left', padx=5)
        self.password_entry = Entry(password_frame, font=("Helvetica", 14), width=15, show="*")
        self.password_entry.pack(side='left', padx=5)
        
        # 登录按钮
        Button(self.login_frame, text='登录', 
               font=("Helvetica", 16),
               width=15,
               command=self.verify_login).pack(pady=20)
        
        # 返回按钮
        Button(self.login_frame, text='返回', 
               font=("Helvetica", 16),
               width=15,
               command=self.go_back).pack(pady=10)
    
    def verify_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # 这里可以添加实际的验证逻辑
        if username == "admin" and password == "admin123":
            messagebox.showinfo("成功", "登录成功！")
            self.login_frame.destroy()
            return True
        else:
            messagebox.showerror("错误", "用户名或密码错误！")
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