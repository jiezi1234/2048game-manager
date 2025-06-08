# client.py
import json
import socket
from tkinter import Tk, Frame, Label, Button, Entry, messagebox, Toplevel
from config import host, port
from main import Game2048,BattleGame2048
from admin import AdminPanel
import subprocess
import sys
import os
import signal
import threading
import time

class AuthGUI:
    def __init__(self, root):
        self.root = root
        self.admin_process = None
        self.game_window = None
        self.admin_window = None
        self.session_id = None
        self.battle_window = None
        self.battle_room_id = None
        self.battle_update_thread = None
        self.stop_battle_update = False

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
            test_socket.connect((host, port))
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

    def get_leaderboard(self):
        """获取排行榜数据"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            request = {
                'action': 'get_leaderboard'
            }
            print("发送排行榜请求...")
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            print(f"收到服务器响应: {response}")
            client.close()
            return response
        except Exception as e:
            print(f"获取排行榜失败: {e}")
            return None

    def show_leaderboard(self):
        """显示排行榜"""
        # 创建排行榜框架
        leaderboard_frame = Frame(self.main_frame)
        leaderboard_frame.pack(pady=20)
        
        Label(leaderboard_frame, text='排行榜', font=("Helvetica", 18, "bold")).pack(pady=10)
        
        # 获取排行榜数据
        print("正在获取排行榜数据...")
        response = self.get_leaderboard()
        print(f"排行榜响应: {response}")
        if response and response.get('status') == 'success':
            leaderboard = response.get('leaderboard', [])
            print(f"排行榜数据: {leaderboard}")
            
            if not leaderboard:
                Label(leaderboard_frame, text='暂无排行榜数据', font=("Helvetica", 12)).pack(pady=10)
                return
                
            # 创建表头
            header_frame = Frame(leaderboard_frame)
            header_frame.pack(fill='x', pady=5)
            Label(header_frame, text='排名', width=5, font=("Helvetica", 12, "bold")).pack(side='left', padx=5)
            Label(header_frame, text='用户名', width=15, font=("Helvetica", 12, "bold")).pack(side='left', padx=5)
            Label(header_frame, text='分数', width=8, font=("Helvetica", 12, "bold")).pack(side='left', padx=5)
            Label(header_frame, text='步数', width=8, font=("Helvetica", 12, "bold")).pack(side='left', padx=5)
            
            # 显示排行榜数据
            for i, record in enumerate(leaderboard, 1):
                record_frame = Frame(leaderboard_frame)
                record_frame.pack(fill='x', pady=2)
                Label(record_frame, text=str(i), width=5).pack(side='left', padx=5)
                Label(record_frame, text=record['username'], width=15).pack(side='left', padx=5)
                Label(record_frame, text=str(record['score']), width=8).pack(side='left', padx=5)
                Label(record_frame, text=str(record['steps']), width=8).pack(side='left', padx=5)
        else:
            Label(leaderboard_frame, text='获取排行榜失败', font=("Helvetica", 12)).pack(pady=10)

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
                client.connect((host, port))
                
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
                client.connect((host, port))
                
                request = {
                    "action": "login",
                    "username": username,
                    "password": password,
                    "user_type": user_type
                }
                
                client.send(json.dumps(request).encode('utf-8'))
                response = json.loads(client.recv(4096).decode('utf-8'))
                
                if response['status'] == 'success':
                    self.session_id = response['session_id']
                    messagebox.showinfo("成功", "登录成功！")
                    login_window.destroy()
                    
                    if user_type == "user":
                        self.root.withdraw()
                        self.game_window = Toplevel()
                        self.game_window.session_id = self.session_id
                        self.game_window.protocol("WM_DELETE_WINDOW", self.on_game_close)
                        
                        # 创建按钮框架
                        button_frame = Frame(self.game_window)
                        button_frame.pack(side='top', fill='x', padx=10, pady=5)
                        
                        # 添加对战按钮
                        Button(button_frame, text='进入对战模式', font=("Helvetica", 12),
                               command=self.show_battle_window).pack(side='right', padx=5)
                        
                        game = Game2048(self.game_window)
                        
                        # 绑定游戏结束事件
                        def on_game_over(event):
                            stats = game.get_game_stats()
                            self.send_game_record(stats['score'], stats['steps'])
                        
                        self.game_window.bind("<<GameOver>>", on_game_over)
                    else:
                        # 启动管理员界面
                        self.root.withdraw()
                        self.admin_window = Toplevel()
                        self.admin_window.session_id = self.session_id
                        self.admin_window.protocol("WM_DELETE_WINDOW", self.on_admin_close)
                        admin_panel = AdminPanel(self.admin_window)
                else:
                    messagebox.showerror("错误", response['message'])
            except Exception as e:
                messagebox.showerror("错误", f"登录失败: {str(e)}")
            finally:
                client.close()
        
        Button(frame, text='登录', font=("Helvetica", 14), width=15,
               command=do_login).pack(pady=20)

    def send_game_record(self, score, steps):
        """发送游戏记录到服务器"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            request = {
                "action": "save_record",
                "session_id": self.session_id,
                "score": int(score),  # 转换为Python原生int类型
                "steps": int(steps)   # 转换为Python原生int类型
            }
            
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            
            if response['status'] != 'success':
                print(f"保存游戏记录失败: {response['message']}")
        except Exception as e:
            print(f"发送游戏记录失败: {str(e)}")
        finally:
            client.close()

    def on_game_close(self):
        """处理游戏窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            try:
                # 发送登出请求
                if self.session_id:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((host, port))
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

    def on_admin_close(self):
        """处理管理员界面关闭事件"""
        try:
            # 发送登出请求
            if self.session_id:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))
                request = {
                    "action": "logout",
                    "session_id": self.session_id
                }
                client.send(json.dumps(request).encode('utf-8'))
                client.close()
        except:
            pass  # 忽略登出时的错误
        finally:
            # 关闭管理员窗口（如果存在）
            if self.admin_window:
                self.admin_window.destroy()
            self.session_id = None
            self.root.deiconify()

    def on_closing(self):
        """处理主窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出系统吗？"):
            try:
                # 发送登出请求
                if self.session_id:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((host, port))
                    request = {
                        "action": "logout",
                        "session_id": self.session_id
                    }
                    client.send(json.dumps(request).encode('utf-8'))
                    client.close()
            except:
                pass  # 忽略登出时的错误
            finally:
                # 关闭管理员窗口（如果存在）
                if hasattr(self, 'admin_window') and self.admin_window:
                    self.admin_window.destroy()
                # 关闭游戏窗口（如果存在）
                if hasattr(self, 'game_window') and self.game_window:
                    self.game_window.destroy()
                # 关闭主窗口
                self.root.quit()

    def show_battle_window(self):
        """显示残局对战窗口"""
        if not self.session_id:
            messagebox.showwarning("警告", "请先登录！")
            return
            
        self.battle_window = Toplevel(self.root)
        self.battle_window.title("残局对战")
        self.battle_window.geometry("600x400")
        
        frame = Frame(self.battle_window, padx=20, pady=20)
        frame.pack(expand='yes', fill='both')
        
        # 创建房间按钮
        Button(frame, text='创建房间', font=("Helvetica", 14), width=15,
               command=self.create_battle_room).pack(pady=10)
        
        # 加入房间区域
        join_frame = Frame(frame)
        join_frame.pack(pady=10)
        
        Label(join_frame, text='房间号:', font=("Helvetica", 14)).pack(side='left', padx=5)
        self.room_entry = Entry(join_frame, font=("Helvetica", 14), width=10)
        self.room_entry.pack(side='left', padx=5)
        
        Button(join_frame, text='加入房间', font=("Helvetica", 14),
               command=self.join_battle_room).pack(side='left', padx=5)

    def create_battle_room(self):
        """创建对战房间"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            request = {
                'action': 'create_battle',
                'session_id': self.session_id
            }
            
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            
            if response['status'] == 'success':
                self.battle_room_id = response['room_id']
                messagebox.showinfo("成功", f"房间创建成功！房间号：{self.battle_room_id}")
                self.start_battle_game()
            else:
                messagebox.showerror("错误", response['message'])
        except Exception as e:
            messagebox.showerror("错误", f"创建房间失败: {str(e)}")
        finally:
            client.close()

    def join_battle_room(self):
        """加入对战房间"""
        room_id = self.room_entry.get()
        if not room_id:
            messagebox.showwarning("警告", "请输入房间号！")
            return
            
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            request = {
                'action': 'join_battle',
                'session_id': self.session_id,
                'room_id': room_id
            }
            
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            
            if response['status'] == 'success':
                self.battle_room_id = room_id
                messagebox.showinfo("成功", "成功加入房间！")
                self.start_battle_game()
            else:
                messagebox.showerror("错误", response['message'])
        except Exception as e:
            messagebox.showerror("错误", f"加入房间失败: {str(e)}")
        finally:
            client.close()

    def start_battle_game(self):
        """开始对战游戏"""
        if self.battle_window:
            self.battle_window.destroy()
            
        self.root.withdraw()
        self.game_window = Toplevel()
        self.game_window.session_id = self.session_id
        self.game_window.protocol("WM_DELETE_WINDOW", self.on_battle_game_close)
        
        # 创建对战游戏实例
        game = BattleGame2048(self.game_window, self.battle_room_id, self.session_id)
        
        # 绑定游戏结束事件
        def on_game_over(event):
            stats = game.get_game_stats()
            self.send_game_record(stats['score'], stats['steps'])
            self.stop_battle_update = True
            
        self.game_window.bind("<<GameOver>>", on_game_over)

    def update_battle_state(self, game):
        """更新对战状态"""
        while not self.stop_battle_update:
            try:
                # 发送自己的状态
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))
                
                request = {
                    'action': 'update_battle_state',
                    'session_id': self.session_id,
                    'room_id': self.battle_room_id,
                    'state': game.get_game_stats()
                }
                
                client.send(json.dumps(request).encode('utf-8'))
                response = json.loads(client.recv(4096).decode('utf-8'))
                
                if response['status'] == 'success':
                    # 获取对手状态
                    request = {
                        'action': 'get_battle_state',
                        'session_id': self.session_id,
                        'room_id': self.battle_room_id
                    }
                    
                    client.send(json.dumps(request).encode('utf-8'))
                    response = json.loads(client.recv(4096).decode('utf-8'))
                    
                    if response['status'] == 'success' and response['opponent_state']:
                        # 更新对手状态显示
                        opponent_state = response['opponent_state']
                        game.update_opponent_state(opponent_state)
                
                client.close()
                time.sleep(1)  # 每秒更新一次
            except Exception as e:
                print(f"更新对战状态失败: {e}")
                time.sleep(1)

    def on_battle_game_close(self):
        """处理对战游戏窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出对战吗？"):
            self.stop_battle_update = True
            if self.game_window:
                self.game_window.destroy()
            self.root.deiconify()



if __name__ == "__main__":
    root = Tk()
    app = AuthGUI(root)
    root.mainloop()