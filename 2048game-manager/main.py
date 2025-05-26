# coding=utf-8
from tkinter import Toplevel, Tk, HORIZONTAL, RIGHT, Menu, IntVar, Button, Frame, Scale, Label, messagebox
from numpy import zeros, repeat, append, argwhere, concatenate, sum
from numpy.random import randint, choice
from PIL import Image, ImageTk
from random import sample
import os

# 获取项目根目录的绝对路径
basic_dir = os.path.dirname(os.path.abspath(__file__))

class Game2048():
    def __init__(self, master=None):
        self.root = master if master else Tk()
        self.length = 4
        self.size_label = 100
        self.number_start = 4
        self.step = 1
        self.labels = globals()
        self.frames = globals()
        self.images = globals()
        self.numbers = [0,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072]
        self.start_frame = None
        self.score = 0  # 添加分数变量
        self.moves = 0  # 添加步数变量
        self.show_start_screen()

    def show_start_screen(self):
        self.start_frame = Frame(self.root, width=400, height=400)
        self.start_frame.pack(expand='yes', fill='both')
        Label(self.start_frame, text='2048 游戏', font=("Helvetica", 32, "bold")).pack(pady=60)
        Button(self.start_frame, text='开始游戏', font=("Helvetica", 20), command=self.start_game).pack(pady=20)

    def start_game(self):
        if self.start_frame:
            self.start_frame.destroy()
            self.start_frame = None
        self.score = 0  # 重置分数
        self.moves = 0  # 重置步数
        self.new_game(distroy=False)

    # 更改图片的大小使之适应label的大小
    def resize(self,w_box, h_box, image_file):  # 参数是：要适应的窗口宽、高、Image.open后的图片
        pil_image = Image.open(image_file)  # 以一个PIL图像对象打开  【调整待转图片格式】
        w, h = pil_image.size  # 获取图像的原始大小
        f1 = 1.0 * w_box / w
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        pil_image_resized = pil_image.resize((width, height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_image_resized)
    # 设置几种弹窗窗口
    def help(self):  # help窗口
        messagebox.showinfo(title='Hi,这是你需要的帮助（^-^）',
                            message='''基本操作：使用键盘的上、下、左、右分别控制游戏的方向。\n回退操作：点击键盘的b（英文哦！）回到上一步，只有4次机会哦！\n设置操作：你可以在Edit下的Setting通过设置定制你的游戏哦！\n注意：如果重新开始一局游戏需要点击一下游戏框哦！''')
    def success(self):  # help窗口
        anser = messagebox.askokcancel('通关成功（^-^)', '是否重新开始？')
        if anser:
            self.new_game()
    def fail(self):  # help窗口
        anser = messagebox.askokcancel('游戏失败（-……-)', '是否重新开始？')
        if anser:
            self.new_game()
    # 初始化窗口函数
    def new_game(self, distroy = True):
        if distroy:     # 重新开始游戏则摧毁之前的窗口初始化游戏
            self.root.destroy()
            self.root = Tk()
        # 创建主窗口
        self.root.resizable(0,0)
        self.root.title('2048游戏')
        # 将图片数据存入images中
        for num in self.numbers:
            file = os.path.join(basic_dir, 'images', str(num) + '.GIF')
            self.images['img%d'%num] = self.resize(self.size_label, self.size_label, file)
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
        
        # 添加分数显示
        self.score_label = Label(self.info_frame, text=f'得分: {self.score}', 
                               font=("Helvetica", 20, "bold"),
                               bg='#50899b')
        self.score_label.pack(pady=20)
        
        # 添加步数显示
        self.moves_label = Label(self.info_frame, text=f'步数: {self.moves}', 
                               font=("Helvetica", 20, "bold"),
                               bg='#50899b')
        self.moves_label.pack(pady=20)

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
            self.frames['fra%d'%i] = Frame(self.game_frame)
            self.frames['fra%d'%i].pack(side='top',expand='yes',fill='both')
            for j in range(self.length):
                number = self.data[i,j]
                self.labels['lab%d'%ord] = Label(self.frames['fra%d'%i], text=number if number!=0 else '',
                                                    font = ("Helvetica 16 bold italic",20),
                                                    relief='ridge',
                                                    image = self.images['img%d'%number],
                                                    width = self.size_label, height=self.size_label)
                self.labels['lab%d'%ord].pack(side='left',expand='YES',fill='both')
                ord += 1

    def button_move(self, direction):
        # 模拟键盘事件
        event = type('Event', (), {'keysym': direction})()
        self.sum_by_direction(event)

    # 打印数据（更换数字更新后label的图片参数
    def print_data(self):
        ord = 0
        for i in range(self.length):
            for j in range(self.length):
                number = self.data[i,j]
                self.labels['lab%d' % ord]['image'] = self.images['img%d'%number]
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
if __name__ == '__main__':
    game = Game2048()
    game.root.mainloop()