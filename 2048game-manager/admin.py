import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json

class AdminPanel:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("2048游戏管理员面板")
        self.window.geometry("800x600")
        
        # 设置窗口关闭事件处理
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建主界面
        self.setup_main_ui()
        
    def setup_main_ui(self):
        """设置主界面"""
        # 搜索框
        search_frame = ttk.Frame(self.window, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="搜索用户:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_user).pack(side=tk.LEFT)
        
        # 用户列表
        self.tree = ttk.Treeview(self.window, columns=("用户ID", "用户名", "状态"), show="headings")
        self.tree.heading("用户ID", text="用户ID")
        self.tree.heading("用户名", text="用户名")
        self.tree.heading("状态", text="状态")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="封禁用户", command=self.ban_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="解封用户", command=self.unban_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="安全退出", command=self.on_closing).pack(side=tk.RIGHT, padx=5)
        
        # 初始加载用户列表
        self.refresh_user_list()
        
    def send_request(self, request):
        """向服务器发送请求"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)  # 设置5秒超时
            client.connect(('127.0.0.1', 20480))
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            client.close()
            return response
        except socket.timeout:
            messagebox.showerror("错误", "服务器响应超时")
            return None
        except ConnectionRefusedError:
            messagebox.showerror("错误", "无法连接到服务器")
            return None
        except Exception as e:
            messagebox.showerror("错误", f"服务器连接失败: {e}")
            return None
            
    def refresh_user_list(self):
        """刷新用户列表"""
        response = self.send_request({
            'action': 'get_user_list'
        })
        
        if response and response['status'] == 'success':
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for user in response['users']:
                # 只显示非管理员用户
                if not user['is_admin']:
                    status = "已封禁" if user['blocked'] else "正常"
                    self.tree.insert("", tk.END, values=(
                        user['uid'],
                        user['username'],
                        status
                    ))
        elif response:
            messagebox.showerror("错误", response['message'])
            
    def search_user(self):
        """搜索用户"""
        search_term = self.search_entry.get()
        response = self.send_request({
            'action': 'get_user_list',
            'search_term': search_term
        })
        
        if response and response['status'] == 'success':
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for user in response['users']:
                # 只显示非管理员用户
                if not user['is_admin']:
                    status = "已封禁" if user['blocked'] else "正常"
                    self.tree.insert("", tk.END, values=(
                        user['uid'],
                        user['username'],
                        status
                    ))
        elif response:
            messagebox.showerror("错误", response['message'])
            
    def ban_user(self):
        """封禁用户"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要封禁的用户！")
            return
            
        uid = self.tree.item(selected[0])["values"][0]
        response = self.send_request({
            'action': 'ban_user',
            'uid': uid
        })
        
        if response and response['status'] == 'success':
            self.refresh_user_list()
            messagebox.showinfo("成功", response['message'])
        elif response:
            messagebox.showerror("错误", response['message'])
            
    def unban_user(self):
        """解封用户"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要解封的用户！")
            return
            
        uid = self.tree.item(selected[0])["values"][0]
        response = self.send_request({
            'action': 'unban_user',
            'uid': uid
        })
        
        if response and response['status'] == 'success':
            self.refresh_user_list()
            messagebox.showinfo("成功", response['message'])
        elif response:
            messagebox.showerror("错误", response['message'])
            
    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出管理员界面吗？"):
            try:
                # 尝试发送退出请求到服务器
                self.send_request({
                    'action': 'logout',
                    'session_id': None  # 管理员界面不需要session_id
                })
            except:
                pass  # 忽略退出时的错误
            finally:
                self.window.destroy()
            
    def run(self):
        """运行管理员面板"""
        self.window.mainloop()

if __name__ == "__main__":
    admin_panel = AdminPanel()
    admin_panel.run()
