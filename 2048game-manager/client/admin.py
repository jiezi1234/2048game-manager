import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import argparse
from config import host, port  # 添加这行导入

class AdminPanel:
    def __init__(self, window):
        self.window = window
        self.window.title("2048游戏管理员面板")

        self.window.geometry("1200x800")
        
        # 创建主界面
        self.setup_main_ui()
        
    def setup_main_ui(self):
        """设置主界面"""
        # 创建左右分栏
        left_frame = ttk.Frame(self.window, padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(self.window, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧：原有的用户管理功能
        self.setup_user_management(left_frame)
        
        # 右侧：得分分布图表
        self.setup_score_distribution(right_frame)
        
    def setup_user_management(self, parent):
        """设置用户管理界面"""
        # 搜索框
        search_frame = ttk.Frame(parent, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="搜索用户:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_user).pack(side=tk.LEFT)
        
        # 用户列表
        self.tree = ttk.Treeview(parent, columns=("用户ID", "用户名", "状态"), show="headings")
        self.tree.heading("用户ID", text="用户ID")
        self.tree.heading("用户名", text="用户名")
        self.tree.heading("状态", text="状态")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(parent, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="封禁用户", command=self.ban_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="解封用户", command=self.unban_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="安全退出", command=self.on_closing).pack(side=tk.RIGHT, padx=5)
        
        # 初始加载用户列表
        self.refresh_user_list()
        
    def setup_score_distribution(self, parent):
        """设置得分分布图表界面"""
        # 标题
        ttk.Label(parent, text="用户得分分布", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # 创建图表框架
        self.chart_frame = ttk.Frame(parent)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 刷新按钮
        ttk.Button(parent, text="刷新图表", command=self.refresh_score_distribution).pack(pady=10)
        
        # 初始加载图表
        self.refresh_score_distribution()
        
    def send_request(self, request):
        """向服务器发送请求"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)  # 设置5秒超时
            client.connect((host, port))  # 使用导入的 host 和 port
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
                # 发送退出请求到服务器，使用保存的session_id
                self.send_request({
                    'action': 'logout',
                    'session_id': self.session_id
                })
            except:
                pass  # 忽略退出时的错误
            finally:
                # 直接销毁窗口
                self.window.destroy()
            
    def refresh_score_distribution(self):
        """刷新得分分布图表"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  
        plt.rcParams['axes.unicode_minus'] = False 
        
        response = self.send_request({
            'action': 'get_score_distribution'
        })
        
        if response and response['status'] == 'success':
            # 清除旧的图表
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            
            # 准备数据
            distribution = response['distribution']
            usernames = [item['username'] for item in distribution]
            scores = [item['max_score'] for item in distribution]
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))
            
            # 柱状图
            ax1.bar(usernames, scores)
            ax1.set_title('用户最高分分布', fontsize=10)
            ax1.set_xlabel('用户名', fontsize=8)
            ax1.set_ylabel('最高分', fontsize=8)
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # 饼图
            score_ranges = {
                '0-1000': 0,
                '1000-2000': 0,
                '2000-3000': 0,
                '3000-4000': 0,
                '4000+': 0
            }
            
            for score in scores:
                if score <= 1000:
                    score_ranges['0-1000'] += 1
                elif score <= 2000:
                    score_ranges['1000-2000'] += 1
                elif score <= 3000:
                    score_ranges['2000-3000'] += 1
                elif score <= 4000:
                    score_ranges['3000-4000'] += 1
                else:
                    score_ranges['4000+'] += 1
            
            labels = list(score_ranges.keys())
            sizes = list(score_ranges.values())
            
            # 设置饼图文字大小
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', 
                    textprops={'fontsize': 8})
            ax2.set_title('分数段分布', fontsize=10)
            
            # 调整子图之间的间距
            plt.subplots_adjust(hspace=0.4)  # 增加子图之间的间距
            
            # 将图表嵌入到Tkinter窗口
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        elif response:
            messagebox.showerror("错误", response['message'])
            
    def run(self):
        """运行管理员面板"""
        self.window.mainloop()

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--session_id', required=True, help='管理员会话ID')
    args = parser.parse_args()
    
    # 创建管理员面板实例，传入session_id
    admin_panel = AdminPanel(args.session_id)
    admin_panel.run()
