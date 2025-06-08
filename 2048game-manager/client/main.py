# coding=utf-8
from tkinter import Toplevel, Tk, HORIZONTAL, RIGHT, Menu, IntVar, Button, Frame, Scale, Label, messagebox, Entry
from numpy import zeros, repeat, append, argwhere, concatenate, sum
from numpy.random import randint, choice
from PIL import Image, ImageTk
from random import sample
import os
import socket
import json
import threading
import time
from config import host, port

# 获取项目根目录的绝对路径
basic_dir = os.path.dirname(os.path.abspath(__file__))

class Game2048():
    def __init__(self, master=None):
        self.root = master if master else Tk()
        self.length = 4
        self.size_label = 100
        self.number_start = 4
        self.step = 1
        self.labels = {}
        self.frames = {}
        self.images = {}
        self.numbers = [0,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072]
        self.start_frame = None
        self.score = 0  # 添加分数变量
        self.moves = 0  # 添加步数变量
        self.recommendation_label = None  # 添加推荐标签
        
        # 从父窗口获取session_id
        if master:
            # 向上查找包含session_id的父窗口
            current = master
            while current and not hasattr(current, 'session_id'):
                current = current.master
            self.session_id = current.session_id if current else None
        else:
            self.session_id = None
            
        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        self.show_start_screen()

    def send_game_record(self, score, steps):
        """发送游戏记录到服务器"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))  # 使用导入的 host 和 port
            
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

    def game_over(self):
        """游戏结束处理"""
        messagebox.showinfo("游戏结束", f"游戏结束！\n最终分数: {self.score}\n总步数: {self.moves}")
        
        # 保存游戏记录
        self.send_game_record(self.score, self.moves)
        
        # 触发游戏结束事件
        self.root.event_generate("<<GameOver>>")
        
        # 销毁当前游戏窗口，返回到开始界面
        if self.root:
            self.root.destroy()
            self.root = Tk()
            self.show_start_screen()

    def get_game_stats(self):
        """获取游戏统计信息"""
        return {
            'score': int(self.score),  # 转换为Python原生int类型
            'steps': int(self.moves)   # 转换为Python原生int类型
        }

    def show_start_screen(self):
        self.start_frame = Frame(self.root, width=400, height=400)
        self.start_frame.pack(expand='yes', fill='both')
        
        # 创建左侧游戏标题和开始按钮
        left_frame = Frame(self.start_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=20)
        
        Label(left_frame, text='2048 游戏', font=("Helvetica", 32, "bold")).pack(pady=60)
        
        # 创建按钮框架
        buttons_frame = Frame(left_frame)
        buttons_frame.pack(pady=20)
        
        # 添加开始游戏按钮
        Button(buttons_frame, text='开始游戏', font=("Helvetica", 20), 
               command=self.start_game).pack(pady=10)
        
        # 创建右侧排行榜
        right_frame = Frame(self.start_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=20)
        
        # 添加排行榜标题和装饰线
        title_frame = Frame(right_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
        # 左侧装饰线
        Frame(title_frame, height=2, width=135, bg='#e74c3c').pack(side='left', padx=(0, 20))
        
        # 标题
        Label(title_frame, text='排行榜', font=("Helvetica", 28, "bold"), 
              fg='#2c3e50').pack(side='left',padx=20)
        
        # 右侧装饰线
        Frame(title_frame, height=2, width=135, bg='#e74c3c').pack(side='left', padx=(20, 0))
        
        # 获取排行榜数据
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            request = {
                'action': 'get_leaderboard'
            }
            client.send(json.dumps(request).encode('utf-8'))
            response = json.loads(client.recv(4096).decode('utf-8'))
            client.close()
            
            if response and response.get('status') == 'success':
                leaderboard = response.get('leaderboard', [])
                
                # 创建表头
                header_frame = Frame(right_frame)
                header_frame.pack(fill='x', pady=(0, 15))
                
                # 表头装饰线
                Frame(header_frame, height=1, bg='#ecf0f1').pack(fill='x', pady=(0, 10))
                
                Label(header_frame, text='排名', width=5, font=("Helvetica", 12),
                      fg='#7f8c8d').pack(side='left', padx=5)
                Label(header_frame, text='用户名', width=12, font=("Helvetica", 12),
                      fg='#7f8c8d').pack(side='left', padx=40)
                Label(header_frame, text='分数', width=8, font=("Helvetica", 12),
                      fg='#7f8c8d').pack(side='left', padx=5)
                Label(header_frame, text='步数', width=8, font=("Helvetica", 12),
                      fg='#7f8c8d').pack(side='left', padx=30)
                
                # 显示排行榜数据
                for i, record in enumerate(leaderboard, 1):
                    # 为前三名使用不同的样式
                    if i == 1:
                        rank_color = '#FFD700'  # 金色
                        name_color = '#FFD700'  # 金色
                        score_color = '#FFD700'  # 金色
                        rank_text = '冠军'
                    elif i == 2:
                        rank_color = '#C0C0C0'  # 银色
                        name_color = '#C0C0C0'  # 银色
                        score_color = '#C0C0C0'  # 银色
                        rank_text = '亚军'
                    elif i == 3:
                        rank_color = '#CD7F32'  # 铜色
                        name_color = '#CD7F32'  # 铜色
                        score_color = '#CD7F32'  # 铜色
                        rank_text = '季军'
                    else:
                        rank_color = '#7f8c8d'  # 灰色
                        name_color = '#34495e'  # 深灰色
                        score_color = '#7f8c8d'  # 灰色
                        rank_text = str(i)
                    
                    record_frame = Frame(right_frame)
                    record_frame.pack(fill='x', pady=3)
                    
                    # 排名
                    Label(record_frame, text=rank_text, width=5, font=("Helvetica", 12, "bold"),
                          fg=rank_color).pack(side='left', padx=5)
                    
                    # 用户名
                    Label(record_frame, text=record['username'], width=10, font=("Helvetica", 12),
                          fg=name_color).pack(side='left', padx=40)
                    
                    # 分数
                    Label(record_frame, text=str(record['score']), width=10, font=("Helvetica", 12, "bold"),
                          fg=score_color).pack(side='left', padx=5)
                    
                    # 步数
                    Label(record_frame, text=str(record['steps']), width=5, font=("Helvetica", 12),
                          fg='#7f8c8d').pack(side='left', padx=30)
                    
                    # 添加分隔线（除了最后一条记录）
                    if i < len(leaderboard):
                        separator = Frame(record_frame, height=1, bg='#ecf0f1')
                        separator.pack(fill='x', pady=(3, 0))
                
                # 底部装饰线
                Frame(right_frame, height=1, bg='#ecf0f1').pack(fill='x', pady=(10, 0))
            else:
                Label(right_frame, text='暂无排行榜数据', font=("Helvetica", 12),
                      fg='#7f8c8d').pack(pady=10)
        except Exception as e:
            print(f"获取排行榜失败: {e}")
            Label(right_frame, text='获取排行榜失败', font=("Helvetica", 12),
                  fg='#7f8c8d').pack(pady=10)

    def start_game(self):
        if self.start_frame:
            self.start_frame.destroy()
            self.start_frame = None
        self.score = 0  # 重置分数
        self.moves = 0  # 重置步数
        self.new_game(distroy=False)

    def resize(self, w_box, h_box, image_file):
        """调整图片大小"""
        try:
            pil_image = Image.open(image_file)
            w, h = pil_image.size
            f1 = 1.0 * w_box / w
            f2 = 1.0 * h_box / h
            factor = min([f1, f2])
            width = int(w * factor)
            height = int(h * factor)
            pil_image_resized = pil_image.resize((width, height), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(pil_image_resized, master=self.root)  # 指定master为当前窗口
        except Exception as e:
            print(f"加载图片失败: {e}")
            # 创建一个默认的纯色图片
            img = Image.new('RGB', (w_box, h_box), color='#cdc1b4')
            return ImageTk.PhotoImage(img, master=self.root)  # 指定master为当前窗口

    # 设置几种弹窗窗口
    def help(self):  # help窗口
        messagebox.showinfo(title='Hi,这是你需要的帮助（^-^）',
                            message='''基本操作：使用键盘的上、下、左、右分别控制游戏的方向。\n回退操作：点击键盘的b（英文哦！）回到上一步，只有4次机会哦！\n设置操作：你可以在Edit下的Setting通过设置定制你的游戏哦！\n注意：如果重新开始一局游戏需要点击一下游戏框哦！''')
    def success(self):  # help窗口
        anser = messagebox.askokcancel('通关成功（^-^)', '是否重新开始？')
        if anser:
            self.game_over()  # 添加游戏结束事件触发
            self.new_game()
        else:
            self.game_over()  # 添加游戏结束事件触发
    def fail(self):  # help窗口
        anser = messagebox.askokcancel('游戏失败（-……-)', '是否重新开始？')
        if anser:
            self.game_over()  # 添加游戏结束事件触发
            self.new_game()
        else:
            self.game_over()  # 添加游戏结束事件触发
    # 初始化窗口函数
    def new_game(self, distroy=True):
        if distroy:     # 重新开始游戏则摧毁之前的窗口初始化游戏
            self.root.destroy()
            self.root = Tk()
        # 创建主窗口
        self.root.resizable(0,0)
        self.root.title('2048游戏')
        
        # 清空图片缓存
        self.images = {}
        
        # 将图片数据存入images中
        for num in self.numbers:
            try:
                file = os.path.join(basic_dir, 'images', str(num) + '.GIF')
                self.images[f'img{num}'] = self.resize(self.size_label, self.size_label, file)
            except Exception as e:
                print(f"加载图片 {num} 失败: {e}")
                # 创建一个默认的纯色图片
                img = Image.new('RGB', (self.size_label, self.size_label), color='#cdc1b4')
                self.images[f'img{num}'] = ImageTk.PhotoImage(img, master=self.root)  # 指定master为当前窗口
        
        # 清空标签和框架缓存
        self.labels = {}
        self.frames = {}
        
        # 捕捉键盘事件
        self.root.bind("<Key>", self.sum_by_direction)
        self.root.focus_set()
        
        # 创建menubar栏
        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Edit', menu=self.filemenu)
        self.filemenu.add_command(label='Restart', command=self.new_game)
        self.filemenu.add_command(label='Setting', command=self.setup_config)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit', command=self.root.quit)
        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Help', menu=self.helpmenu)
        self.helpmenu.add_command(label='Show Help', command=self.help)
        self.root.config(menu=self.menubar)

        # 创建主游戏区域和右侧信息区域
        self.main_frame = Frame(self.root)
        self.main_frame.pack(side='left', fill='both', expand=True)
        
        self.info_frame = Frame(self.root, width=200)
        self.info_frame.pack(side='right', fill='y', padx=20)
        
        # 添加推荐移动显示
        self.recommendation_label = Label(self.info_frame, text='推荐移动: -', 
                                       font=("Helvetica", 30, "bold"),
                                       fg='#2ecc71')
        self.recommendation_label.pack(pady=10)
        
        # 添加自己的分数显示
        self.score_label = Label(self.info_frame, text=f'我的得分: {self.score}', 
                               font=("Helvetica", 20, "bold"),
                               bg='#50899b')
        self.score_label.pack(pady=20)
        
        # 添加自己的步数显示
        self.moves_label = Label(self.info_frame, text=f'我的步数: {self.moves}', 
                               font=("Helvetica", 20, "bold"),
                               bg='#50899b')
        self.moves_label.pack(pady=20)
        
        # 添加分隔线
        Frame(self.info_frame, height=2, bg='#34495e').pack(fill='x', pady=10)

        # 创建游戏区域容器
        self.game_container = Frame(self.main_frame)
        self.game_container.pack(expand=True, fill='both', padx=20, pady=20)

        # 创建上下按钮样式
        button_style1 = {'font': ('Helvetica', 16, 'bold'), 
                       'width': 3, 
                       'height': 2,
                       'relief': 'raised',
                       'bg': '#9b9450'}

        # 创建左右按钮样式
        button_style2 = {'font': ('Helvetica', 16, 'bold'), 
                       'width': 3, 
                       'height': 2,
                       'relief': 'raised',
                       'bg': '#9b9450'}
        
        # 添加上方向按钮
        self.up_button = Button(self.game_container, text='↑', command=lambda: self.button_move('Up'), **button_style1)
        self.up_button.pack(side='top', pady=10)
        
        # 创建中间区域（包含左右按钮和游戏区域）
        self.middle_frame = Frame(self.game_container)
        self.middle_frame.pack(fill='both', expand=True)
        
        # 添加左方向按钮
        self.left_button = Button(self.middle_frame, text='←', command=lambda: self.button_move('Left'), **button_style2)
        self.left_button.pack(side='left', padx=10)
        
        # 创建游戏区域
        self.game_frame = Frame(self.middle_frame)
        self.game_frame.pack(side='left', fill='both', expand=True)
        
        # 添加右方向按钮
        self.right_button = Button(self.middle_frame, text='→', command=lambda: self.button_move('Right'), **button_style2)
        self.right_button.pack(side='right', padx=10)
        
        # 添加下方向按钮
        self.down_button = Button(self.game_container, text='↓', command=lambda: self.button_move('Down'), **button_style1)
        self.down_button.pack(side='bottom', pady=10)

        self.history_data = zeros((5, self.length, self.length))
        # 初始化data数据
        arr = repeat(0,self.length**2)
        arr[randint(0,self.length**2,self.number_start)] = choice([2,4],self.number_start)
        self.data = arr.reshape(self.length,self.length)
        self.history_data[0] = self.data
        
        # 初始化label数据
        ord = 0
        for i in range(self.length):
            self.frames[f'fra{i}'] = Frame(self.game_frame)
            self.frames[f'fra{i}'].pack(side='top',expand='yes',fill='both')
            for j in range(self.length):
                number = int(self.data[i,j])  # 确保number是Python原生int类型
                self.labels[f'lab{ord}'] = Label(self.frames[f'fra{i}'], 
                                               text=str(number) if number!=0 else '',
                                               font=("Helvetica", 20, "bold"),
                                               relief='ridge',
                                               image=self.images[f'img{number}'],
                                               width=self.size_label, 
                                               height=self.size_label)
                self.labels[f'lab{ord}'].pack(side='left',expand='YES',fill='both')
                ord += 1
        
        # 更新推荐移动
        self.update_recommendation()

    def button_move(self, direction):
        # 模拟键盘事件
        event = type('Event', (), {'keysym': direction})()
        self.sum_by_direction(event)

    def print_data(self):
        """更新界面显示"""
        ord = 0
        for i in range(self.length):
            for j in range(self.length):
                number = int(self.data[i,j])  # 确保number是Python原生int类型
                self.labels[f'lab{ord}']['image'] = self.images[f'img{number}']
                ord += 1

    # 定义加和算法
    def update_score(self, points):
        self.score += points
        self.score_label.config(text=f'得分: {self.score}')

    def update_moves(self):
        self.moves += 1
        self.moves_label.config(text=f'步数: {self.moves}')

    def sum_by_direction(self,event):
        direction = event.keysym
        data_old = self.data.copy()  # 用于判断是否有移动
        if 131072 in self.data:  # 如果出现131072则表示成功通关询问是否重新开始
            self.success()
            return
        if direction in ['Left', 'Up', 'Right', 'Down']:
            if direction in ['Left','Up']:
                self.data = self.data.T if direction=='Up' else self.data # 如果是Up操作则把数组转置
                for i in range(self.length):
                    set_data = [n for n in self.data[i,:] if n != 0]
                    set_len = len(set_data)
                    position = 0
                    while position<set_len-1:
                        two = set_data[position:position+2]
                        if len(set(two))==1:
                            merged_value = sum(two)
                            set_data[position:position+2] = [merged_value,0]
                            self.update_score(merged_value)  # 更新分数
                        position += 1
                    not0 = [n for n in set_data if n != 0]
                    self.data[i,:] = append(not0, repeat(0, self.length-len(not0))) # 刷新数组元素
                self.data = self.data.T if direction=='Up' else self.data # 如果是Up操作则把数组转置回来
            elif direction in ['Right', 'Down']:
                self.data = self.data.T if direction=='Down' else self.data # 如果是Down操作则把数组转置回来
                for i in range(self.length):
                    set_data = [n for n in self.data[i,:] if n != 0]
                    set_len = len(set_data)
                    position = set_len
                    while position>1:
                        two = set_data[position-2:position]
                        if len(set(two))==1:
                            merged_value = sum(two)
                            set_data[position-2:position] = [0,merged_value]
                            self.update_score(merged_value)  # 更新分数
                        position -= 1
                    not0 = [n for n in set_data if n != 0]
                    self.data[i,:] = append(repeat(0, self.length-len(not0)), not0) # 刷新数组元素
                self.data = self.data.T if direction=='Down' else self.data # 如果是Down操作则把数组转置回来
            # 加入新的数字
            if (self.data != data_old).any():
                self.update_moves()  # 更新步数
                position = argwhere(self.data == 0)
                number_0 = position.shape[0]
                number_new = self.step if number_0>self.step else 1
                p = position[sample(range(position.shape[0]),number_new),:]
                self.data[p[:,0],p[:,1]] = choice([2,4], number_new)
                self.history_data = concatenate((self.data.reshape((1,self.length,self.length)),self.history_data[:4]))
                # 更新推荐移动
                self.update_recommendation()
            elif 0 not in self.data: # 判断游戏是否结束了
                self.fail()
                return
        if direction == 'b' and sum(self.history_data[1:])!=0:  # 回退操作
            self.data = self.history_data[1]
            self.history_data = concatenate((self.history_data[1:], zeros((1,self.length,self.length))))
            self.score = 0  # 回退时重置分数
            self.moves = 0  # 回退时重置步数
            self.update_score(0)  # 更新分数显示
            self.update_moves()  # 更新步数显示
            # 更新推荐移动
            self.update_recommendation()
        self.print_data()

    def setup_config(self):
        # 接收设置窗口的数据
        res = self.ask_userinfo()
        if res is None: return
        self.length, self.size_label,self.number_start, self.step = res
        self.new_game(distroy=True)

    def ask_userinfo(self):
        # 将现有参数传递给设置窗口
        current_parameter = [self.length, self.size_label,self.number_start, self.step]
        setting_info = Setting(data=current_parameter)
        self.root.wait_window(setting_info)
        return setting_info.userinfo

    def update_recommendation(self):
        """更新推荐移动显示"""
        if not self.recommendation_label:
            return
            
        best_move, score = self.get_best_move()
        direction_symbols = {
            'Up': '↑',
            'Down': '↓',
            'Left': '←',
            'Right': '→'
        }
        self.recommendation_label.config(
            text=f'推荐移动: {direction_symbols[best_move]}',
            font=("Helvetica", 30, "bold"),
            fg='#2ecc71'
        )

    def get_best_move(self):
        """获取最佳移动方向"""
        moves = ['Up', 'Down', 'Left', 'Right']
        scores = [self.evaluate_move(move) for move in moves]
        best_move = moves[scores.index(max(scores))]
        return best_move, max(scores)

    def evaluate_move(self, direction):
        """评估一个移动的分数"""
        # 保存当前状态
        data_old = self.data.copy()
        score_old = self.score
        
        # 模拟移动
        if direction in ['Left', 'Up']:
            self.data = self.data.T if direction=='Up' else self.data
            for i in range(self.length):
                set_data = [n for n in self.data[i,:] if n != 0]
                set_len = len(set_data)
                position = 0
                while position<set_len-1:
                    two = set_data[position:position+2]
                    if len(set(two))==1:
                        merged_value = sum(two)
                        set_data[position:position+2] = [merged_value,0]
                    position += 1
                not0 = [n for n in set_data if n != 0]
                self.data[i,:] = append(not0, repeat(0, self.length-len(not0)))
            self.data = self.data.T if direction=='Up' else self.data
        elif direction in ['Right', 'Down']:
            self.data = self.data.T if direction=='Down' else self.data
            for i in range(self.length):
                set_data = [n for n in self.data[i,:] if n != 0]
                set_len = len(set_data)
                position = set_len
                while position>1:
                    two = set_data[position-2:position]
                    if len(set(two))==1:
                        merged_value = sum(two)
                        set_data[position-2:position] = [0,merged_value]
                    position -= 1
                not0 = [n for n in set_data if n != 0]
                self.data[i,:] = append(repeat(0, self.length-len(not0)), not0)
            self.data = self.data.T if direction=='Down' else self.data

        # 计算分数
        score = 0
        
        # 1. 计算空格数量
        empty_cells = len(argwhere(self.data == 0))
        score += empty_cells * 10
        
        # 2. 计算合并得分
        merge_score = self.score - score_old
        score += merge_score * 2
        
        # 3. 评估大数字的位置
        max_value = self.data.max()
        max_pos = argwhere(self.data == max_value)[0]
        if max_pos[0] in [0, self.length-1] and max_pos[1] in [0, self.length-1]:
            score += 50  # 大数字在角落
        
        # 4. 评估数字的单调性
        monotonicity = 0
        for i in range(self.length):
            for j in range(self.length-1):
                if self.data[i,j] >= self.data[i,j+1]:
                    monotonicity += 1
                if self.data[j,i] >= self.data[j+1,i]:
                    monotonicity += 1
        score += monotonicity * 5
        
        # 恢复原始状态
        self.data = data_old
        self.score = score_old
        
        return score

    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            # 触发游戏结束事件
            self.root.event_generate("<<GameOver>>")
            # 如果是从父窗口启动的，显示父窗口
            if self.root.master:
                self.root.master.deiconify()
            self.root.destroy()

# 弹出设置窗口
class Setting(Toplevel):
    def __init__(self, data):
        super().__init__()
        self.title('设置游戏参数')
        # 接收游戏的参数，用于设置scale的默认值
        self.length = IntVar()
        self.length.set(data[0])
        self.size = IntVar()
        self.size.set(data[1])
        self.start = IntVar()
        self.start.set(data[2])
        self.step = IntVar()
        self.step.set(data[3])
        # 弹窗界面
        self.setup_UI()
    def setup_UI(self):
        # 第一行（两列）
        row1 = Frame(self)
        row1.pack(fill="x")
        scale_length = Scale(row1, label='每行每列的格子数', from_=2, to=20,
                                orient=HORIZONTAL, length=200, showvalue=1,
                                tickinterval=3, resolution=1, variable=self.length)
        scale_length.set(self.length.get())
        scale_length.pack(side='top',expand='YES',fill='both')
        scale_size = Scale(row1, label='每个格子的大小', from_=10, to=200,
                              orient=HORIZONTAL, length=200, showvalue=1,
                              tickinterval=30, resolution=10, variable=self.size)
        scale_size.set(self.size.get())
        scale_size.pack(side='top',expand='YES',fill='both')
        scale_start = Scale(row1, label='初始化数字格个数', from_=1, to=10,
                               orient=HORIZONTAL, length=200, showvalue=1,
                               tickinterval=2, resolution=1, variable=self.start)
        scale_start.set(self.start.get())
        scale_start.pack(side='top',expand='YES',fill='both')
        scale_step = Scale(row1, label='每步添加的数字个数', from_=1, to=10,
                             orient=HORIZONTAL, length=200, showvalue=1,
                             tickinterval=2,resolution=1, variable=self.step)
        scale_step.set(self.step.get())
        scale_step.pack(side='top',expand='YES',fill='both')

        # 第三行
        row3 = Frame(self)
        row3.pack(fill="x")
        Button(row3, text="取消", command=self.cancel).pack(side=RIGHT)
        Button(row3, text="确定", command=self.ok).pack(side=RIGHT)
    def ok(self):
        self.userinfo = [self.length.get(), self.size.get(),
                         self.start.get(), self.step.get()] # 设置数据
        self.destroy() # 销毁窗口
    def cancel(self):
        self.userinfo = None # 空！
        self.destroy()

class BattleGame2048(Game2048):
    def __init__(self, master=None, battle_room_id=None, session_id=None):
        super().__init__(master)
        self.battle_room_id = battle_room_id
        self.session_id = session_id
        self.stop_battle_update = False
        self.battle_update_thread = None
        self.opponent_score = 0
        self.opponent_moves = 0
        
        # 确保info_frame已经初始化
        if not hasattr(self, 'info_frame'):
            self.info_frame = Frame(self.root, width=200)
            self.info_frame.pack(side='right', fill='y', padx=20)
        
        # 添加对手分数显示
        self.opponent_score_label = Label(self.info_frame, text=f'对手得分: {self.opponent_score}', 
                                        font=("Helvetica", 20, "bold"),
                                        bg='#50899b')
        self.opponent_score_label.pack(pady=20)
        
        # 添加对手步数显示
        self.opponent_moves_label = Label(self.info_frame, text=f'对手步数: {self.opponent_moves}', 
                                        font=("Helvetica", 20, "bold"),
                                        bg='#50899b')
        self.opponent_moves_label.pack(pady=20)
        
        # 启动状态更新线程
        self.start_battle_update()
        
    def start_battle_update(self):
        """启动对战状态更新线程"""
        self.stop_battle_update = False
        self.battle_update_thread = threading.Thread(target=self.update_battle_state)
        self.battle_update_thread.daemon = True
        self.battle_update_thread.start()
        
    def update_battle_state(self):
        """更新对战状态"""
        while not self.stop_battle_update:
            try:
                # 检查游戏窗口是否还存在
                if not hasattr(self, 'root') or not self.root.winfo_exists():
                    self.stop_battle_update = True
                    break
                    
                # 发送自己的状态
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))
                
                request = {
                    'action': 'update_battle_state',
                    'session_id': self.session_id,
                    'room_id': self.battle_room_id,
                    'state': self.get_game_stats()
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
                        self.update_opponent_state(opponent_state)
                
                client.close()
                time.sleep(1)  # 每秒更新一次
            except Exception as e:
                print(f"更新对战状态失败: {e}")
                time.sleep(1)
                
    def update_opponent_state(self, state):
        """更新对手状态显示"""
        if state:
            self.opponent_score = state.get('score', 0)
            self.opponent_moves = state.get('steps', 0)
            if hasattr(self, 'opponent_score_label'):
                self.opponent_score_label.config(text=f'对手得分: {self.opponent_score}')
            if hasattr(self, 'opponent_moves_label'):
                self.opponent_moves_label.config(text=f'对手步数: {self.opponent_moves}')
                
    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出对战吗？"):
            self.stop_battle_update = True
            self.root.destroy()

    def show_battle_window(self):
        """显示残局对战窗口"""
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
                self.start_battle()
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
                self.start_battle()
            else:
                messagebox.showerror("错误", response['message'])
        except Exception as e:
            messagebox.showerror("错误", f"加入房间失败: {str(e)}")
        finally:
            client.close()

    def start_battle(self):
        """开始对战"""
        if self.battle_window:
            self.battle_window.destroy()
            
        self.root.withdraw()
        self.game_window = Toplevel()
        self.game_window.session_id = self.session_id  # 设置session_id
        
        # 创建对战游戏实例
        game = BattleGame2048(self.game_window, self.battle_room_id, self.session_id)
        
        # 绑定游戏结束事件
        def on_game_over(event):
            if self.game_window:
                self.game_window.destroy()
            self.root.deiconify()
        
        self.game_window.bind("<<GameOver>>", on_game_over)
        self.game_window.protocol("WM_DELETE_WINDOW", game.on_closing)

if __name__ == '__main__':
    game = Game2048()
    game.root.mainloop()