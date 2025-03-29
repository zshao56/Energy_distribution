import xml.etree.ElementTree as ET
import cartopy.crs as ccrs
import csv
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# 修改data_path函数以适应打包环境
def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是打包环境，使用当前目录
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

def read_cities_from_csv(csv_path):
    """从CSV文件读取城市数据"""
    cities_data = {}
    max_radius = 0  # 记录最大半径值
    
    try:
        # 尝试不同的编码方式
        encodings = ['utf-8', 'gbk', 'latin-1']
        success = False
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as csvfile:
                    print(f"尝试使用 {encoding} 编码读取文件...")
                    # 使用制表符作为分隔符
                    reader = csv.reader(csvfile, delimiter='\t')
                    
                    # 读取并显示第一行（标题行）
                    try:
                        header = next(reader)
                        print(f"CSV文件标题行: {header}")
                    except StopIteration:
                        print("CSV文件为空或格式不正确")
                        continue
                    
                    # 第一次遍历找出最大半径值
                    all_rows = list(reader)
                    for row in all_rows:
                        if len(row) >= 4:  # 确保至少有4列数据
                            try:
                                radius = float(row[3])
                                max_radius = max(max_radius, radius)
                            except ValueError:
                                pass
                    
                    print(f"找到最大半径值: {max_radius}")
                    
                    # 第二次遍历处理数据并按比例缩放半径
                    row_count = 0
                    for row in all_rows:
                        row_count += 1
                        if len(row) >= 4:  # 确保至少有4列数据
                            city_name = row[0].strip()
                            try:
                                lon = float(row[1])
                                lat = float(row[2])
                                original_radius = float(row[3])
                                
                                # 按比例缩放半径，最大值对应10
                                if max_radius > 0:
                                    scaled_radius = (original_radius / max_radius) * 10
                                else:
                                    scaled_radius = 0
                                
                                cities_data[city_name] = (lon, lat, scaled_radius)
                                print(f"成功读取: {city_name}, 坐标: ({lon}, {lat}), 原始值: {original_radius}, 缩放半径: {scaled_radius:.2f}")
                            except ValueError as ve:
                                print(f"警告: 跳过行 {row_count+1} '{row}', 数据格式不正确: {ve}")
                        else:
                            print(f"警告: 跳过行 {row_count+1} '{row}', 列数不足")
                
                success = True
                print(f"成功使用 {encoding} 编码读取文件")
                break
                
            except UnicodeDecodeError:
                print(f"使用 {encoding} 编码读取失败，尝试其他编码...")
                continue
        
        if not success:
            print("尝试了所有编码方式，但都无法正确读取文件")
    
    except FileNotFoundError:
        print(f"错误: 找不到CSV文件 '{csv_path}'")
        print(f"当前工作目录: {os.getcwd()}")
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
    
    return cities_data


def add_city_markers_to_svg(input_svg_path, output_svg_path, cities_data):
    # 读取原始SVG文件
    tree = ET.parse(input_svg_path)
    root = tree.getroot()
    
    # 获取SVG尺寸
    svg_width = float(root.get("width", "1000").replace("px", ""))
    svg_height = float(root.get("height", "500").replace("px", ""))
    
    # 创建罗宾逊投影
    projection = ccrs.Robinson()
    
    # 罗宾逊投影的实际范围（单位：米）
    robinson_x_range = 52200000  # -17000000 到 +17000000
    robinson_y_range = 25000000  # -8600000 到 +86000000
    
    # 创建包含所有标记的组元素
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    group = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"id": "city_markers"})
    
    for city, (lon, lat, radius) in cities_data.items():
        # 转换坐标到罗宾逊投影
        x_proj, y_proj = projection.transform_point(lon, lat, ccrs.Geodetic())
        
        # 映射到SVG坐标系
        # x: 从[-17000000,17000000]映射到[0,svg_width]
        # y: 从[-8600000,8600000]映射到[svg_height,0]（SVG的y轴向下）
        x_svg = (x_proj + 23200000) * (svg_width / robinson_x_range)
        y_svg = (11000000 - y_proj) * (svg_height / robinson_y_range)
        
        # 创建圆圈元素 - 修改填充颜色为#FFB3B3，边框颜色为#EF0000
        circle = ET.Element("{http://www.w3.org/2000/svg}circle", attrib={
            "cx": str(x_svg),
            "cy": str(y_svg),
            "r": str(radius),  # 使用缩放后的半径
            "stroke": "#EF0000",
            "fill": "rgba(255,179,179,0.5)",
            "stroke-width": "0.5"
        })
        group.append(circle)
        
        # 创建圆心黑点
        center_dot = ET.Element("{http://www.w3.org/2000/svg}circle", attrib={
            "cx": str(x_svg),
            "cy": str(y_svg),
            "r": "1.5",
            "fill": "black"
        })
        group.append(center_dot)
        
        # 创建文本元素
        text = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
            "x": str(x_svg + 8),  # 减小文本偏移
            "y": str(y_svg),
            "font-size": "10px",  # 减小字体大小
            "fill": "black",
            "font-family": "Arial, sans-serif"
        })
        text.text = city
        group.append(text)
    
    # 添加图例说明
    legend_group = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"id": "legend"})
    
    # 设置图例位置（左下角）
    legend_x = 50
    legend_y = svg_height - 50
    
    # 添加最大值参考圆（半径为10）
    legend_circle = ET.Element("{http://www.w3.org/2000/svg}circle", attrib={
        "cx": str(legend_x),
        "cy": str(legend_y),
        "r": "10",
        "stroke": "#EF0000",
        "fill": "rgba(255,179,179,0.5)",
        "stroke-width": "0.5"
    })
    legend_group.append(legend_circle)
    
    # 添加图例文本
    legend_text = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
        "x": str(legend_x + 15),
        "y": str(legend_y + 5),
        "font-size": "12px",
        "fill": "black",
        "font-family": "Arial, sans-serif"
    })
    legend_text.text = "最大值"
    legend_group.append(legend_text)
    
    # 将图例添加到SVG
    root.append(legend_group)
    
    # 将城市标记组元素添加到SVG根元素中
    root.append(group)
    
    # 保存修改后的SVG文件
    tree.write(output_svg_path, encoding="utf-8", xml_declaration=True)
    print(f'成功生成SVG文件: {output_svg_path}')

# 创建GUI界面
class EnergyDistributionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("能源分布可视化工具")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # 设置界面
        self.setup_ui()
    
    def setup_ui(self):
        # 标题标签
        title_label = tk.Label(self.root, text="能源分布可视化工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # 框架容器
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # CSV文件选择
        csv_frame = tk.Frame(frame)
        csv_frame.pack(fill="x", pady=5)
        
        csv_label = tk.Label(csv_frame, text="城市数据CSV文件:", width=15, anchor="w")
        csv_label.pack(side="left")
        
        self.csv_path_var = tk.StringVar()
        csv_entry = tk.Entry(csv_frame, textvariable=self.csv_path_var, width=30)
        csv_entry.pack(side="left", padx=5)
        
        csv_button = tk.Button(csv_frame, text="浏览...", command=self.browse_csv)
        csv_button.pack(side="left")
        
        # 输出SVG文件选择
        svg_frame = tk.Frame(frame)
        svg_frame.pack(fill="x", pady=5)
        
        svg_label = tk.Label(svg_frame, text="输出SVG文件:", width=15, anchor="w")
        svg_label.pack(side="left")
        
        self.svg_path_var = tk.StringVar()
        svg_entry = tk.Entry(svg_frame, textvariable=self.svg_path_var, width=30)
        svg_entry.pack(side="left", padx=5)
        
        svg_button = tk.Button(svg_frame, text="浏览...", command=self.browse_svg)
        svg_button.pack(side="left")
        
        # 生成按钮
        generate_button = tk.Button(frame, text="生成地图", command=self.generate_map, bg="#4CAF50", fg="white", font=("Arial", 12))
        generate_button.pack(pady=20)
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        status_label = tk.Label(self.root, textvariable=self.status_var, fg="blue")
        status_label.pack(side="bottom", pady=10)
    
    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="选择城市数据CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if filename:
            self.csv_path_var.set(filename)
    
    def browse_svg(self):
        filename = filedialog.asksaveasfilename(
            title="选择SVG输出位置",
            defaultextension=".svg",
            filetypes=[("SVG文件", "*.svg"), ("所有文件", "*.*")]
        )
        if filename:
            self.svg_path_var.set(filename)
    
    def generate_map(self):
        csv_path = self.csv_path_var.get()
        output_svg_path = self.svg_path_var.get()
        
        if not csv_path or not output_svg_path:
            messagebox.showerror("错误", "请选择CSV文件和SVG输出路径")
            return
        
        self.status_var.set("正在处理数据...")
        self.root.update()
        
        try:
            # 读取城市数据
            cities_data = read_cities_from_csv(csv_path)
            
            if not cities_data:
                self.status_var.set("未读取到任何城市数据")
                messagebox.showwarning("警告", "未读取到任何城市数据，请检查CSV文件格式")
                return
            
            # 使用模板生成SVG
            input_svg = resource_path('assets/robinson_map_original.svg')
            
            # 确保输出文件的目录存在
            output_dir = os.path.dirname(output_svg_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 生成SVG
            add_city_markers_to_svg(input_svg, output_svg_path, cities_data)
            
            self.status_var.set(f"成功生成SVG文件: {output_svg_path}")
            messagebox.showinfo("成功", f"成功生成SVG文件:\n{output_svg_path}")
            
        except Exception as e:
            self.status_var.set(f"处理过程中出错: {str(e)}")
            messagebox.showerror("错误", f"处理过程中出错:\n{str(e)}")

# 主程序
if __name__ == "__main__":
    # 创建GUI应用
    root = tk.Tk()
    app = EnergyDistributionApp(root)
    root.mainloop()