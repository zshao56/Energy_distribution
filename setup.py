import PyInstaller.__main__
import os

# 定义项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 定义需要包含的资源文件
assets_folder = os.path.join(project_root, 'assets')

# 定义PyInstaller参数
pyinstaller_args = [
    'main.py',  # 主脚本
    '--name=能源分布可视化工具',  # 输出的exe名称
    '--onefile',  # 打包成单个exe文件
    '--windowed',  # 不显示控制台窗口
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
    f'--add-data={assets_folder};assets',  # 添加资源文件夹
    '--icon=assets/icon.ico',  # 如果有图标文件
    # 排除不需要的模块以减小体积
    '--exclude-module=matplotlib',
    '--exclude-module=scipy',
    '--exclude-module=pandas',
    '--exclude-module=notebook',
    '--exclude-module=jupyter',
    '--exclude-module=IPython',
    '--exclude-module=PIL.ImageDraw',
    '--exclude-module=PIL.ImageFont',
    # 保留cartopy必要部分
    '--collect-submodules=cartopy.crs',
]

# 运行PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("打包完成！")