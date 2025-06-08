import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义需要打包的文件和资源
PyInstaller.__main__.run([
    'client/client.py',  # 主程序文件
    '--name=2048Game',  # 生成的exe名称
    '--windowed',  # 使用GUI模式
    '--onefile',  # 打包成单个文件
    '--icon=client/images/2048.ico',  # 程序图标
    '--add-data=client/images;images',  # 添加图片资源
    '--add-data=client/config.py;.',  # 添加配置文件
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
]) 