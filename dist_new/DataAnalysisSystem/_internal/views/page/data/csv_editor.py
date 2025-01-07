import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import sys
import shutil
from ttkthemes import ThemedTk

class ModernCSVEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("舆情案例数据管理系统")
        self.root.geometry("1400x900")
        
        # 设置主题和样式
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"))
        self.style.configure("Header.TLabel", font=("Microsoft YaHei", 12))
        self.style.configure("Modern.TButton", font=("Microsoft YaHei", 10))
        self.style.configure("Treeview", font=("Microsoft YaHei", 10), rowheight=25)
        self.style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        
        # 获取资源文件路径和用户数据路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的应用
            self.resource_dir = os.path.dirname(os.path.abspath(sys.executable))
            if sys.platform == 'darwin':  # macOS
                self.resource_dir = os.path.abspath(os.path.join(
                    self.resource_dir, '..', 'Resources', 'data'
                ))
        else:
            # 如果是开发环境
            self.resource_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置用户数据目录
        self.user_data_dir = os.path.expanduser('~/Documents/舆情案例数据')
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
            self.copy_initial_data()
        
        self.files = {
            "案例基本信息": "cases.csv",
            "时间线信息": "timelines.csv",
            "分析信息": "analysis.csv",
            "建议信息": "suggestions.csv"
        }
        
        self.current_file = None
        self.df = None
        
        self.create_widgets()
        self.load_initial_data()
    
    def copy_initial_data(self):
        """复制初始数据到用户目录"""
        try:
            for file_name in self.files.values():
                source = os.path.join(self.resource_dir, file_name)
                target = os.path.join(self.user_data_dir, file_name)
                if os.path.exists(source) and not os.path.exists(target):
                    shutil.copy2(source, target)
            messagebox.showinfo("初始化", "已在"文档"文件夹中创建数据文件")
        except Exception as e:
            messagebox.showerror("错误", f"复制初始数据失败：{str(e)}")
    
    def create_widgets(self):
        # 创建主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill="both", expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(title_frame, text="舆情案例数据管理系统", style="Title.TLabel").pack()
        
        # 添加数据位置提示
        ttk.Label(title_frame, text=f"数据保存位置：{self.user_data_dir}", style="Header.TLabel").pack(pady=(5,0))
        
        # 上部分容器
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill="x", pady=(0, 10))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(top_frame, text="文件选择", padding="5")
        file_frame.pack(side="left", fill="x", expand=True)
        
        ttk.Label(file_frame, text="选择要编辑的文件：", style="Header.TLabel").pack(side="left", padx=5)
        self.file_var = tk.StringVar()
        file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, values=list(self.files.keys()), width=30)
        file_combo.pack(side="left", padx=5)
        file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)
        
        # 按钮区域
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side="right", padx=10)
        
        ttk.Button(btn_frame, text="✚ 添加行", command=self.add_row, style="Modern.TButton", width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✖ 删除选中行", command=self.delete_row, style="Modern.TButton", width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 保存更改", command=self.save_changes, style="Modern.TButton", width=15).pack(side="left", padx=5)
        
        # 创建分隔线
        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=10)
        
        # 表格区域
        table_frame = ttk.LabelFrame(main_container, text="数据预览", padding="5")
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建表格和滚动条
        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tree_scroll_y = ttk.Scrollbar(tree_frame)
        self.tree_scroll_y.pack(side="right", fill="y")
        
        self.tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill="both", expand=True)
        
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        
        # 编辑区域
        edit_frame = ttk.LabelFrame(main_container, text="数据编辑", padding="5")
        edit_frame.pack(fill="x", pady=(0, 10))
        
        self.edit_vars = {}
        self.edit_entries = {}
        self.edit_frame = ttk.Frame(edit_frame)
        self.edit_frame.pack(fill="x", padx=5, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_container, textvariable=self.status_var, relief="sunken", padding=(5, 2))
        status_bar.pack(fill="x", side="bottom")
        self.status_var.set("就绪")
    
    def load_initial_data(self):
        self.file_var.set("案例基本信息")
        self.on_file_selected(None)
    
    def on_file_selected(self, event):
        file_name = self.files[self.file_var.get()]
        self.current_file = os.path.join(self.user_data_dir, file_name)
        
        try:
            self.df = pd.read_csv(self.current_file)
            self.update_tree()
            self.create_edit_fields()
            self.status_var.set(f"已加载文件：{file_name}")
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：{str(e)}")
            self.status_var.set("加载文件失败")
    
    def update_tree(self):
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 设置列
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"
        
        # 设置列宽和标题
        for column in self.df.columns:
            # 计算合适的列宽
            max_width = max(
                len(str(self.df[column].max())) * 10,
                len(column) * 10,
                100
            )
            self.tree.heading(column, text=column)
            self.tree.column(column, width=min(max_width, 300), minwidth=100)
        
        # 添加数据
        for idx, row in self.df.iterrows():
            self.tree.insert("", "end", values=list(row))
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # 交替行颜色
        self.tree.tag_configure("oddrow", background="#f0f0f0")
        self.tree.tag_configure("evenrow", background="#ffffff")
        
        for i, item in enumerate(self.tree.get_children()):
            self.tree.item(item, tags=("evenrow" if i % 2 == 0 else "oddrow",))
    
    def create_edit_fields(self):
        # 清空现有编辑框
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
        
        self.edit_vars = {}
        self.edit_entries = {}
        
        # 创建编辑框
        row = 0
        col = 0
        max_cols = 4  # 每行显示的字段数
        
        for column in self.df.columns:
            frame = ttk.Frame(self.edit_frame)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            
            ttk.Label(frame, text=column + ":", style="Header.TLabel").pack(side="left")
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=30)
            entry.pack(side="left", padx=(5, 0))
            
            self.edit_vars[column] = var
            self.edit_entries[column] = entry
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # 获取选中行的值
        values = self.tree.item(selected_items[0])["values"]
        
        # 更新编辑框
        for column, value in zip(self.df.columns, values):
            self.edit_vars[column].set(str(value))
        
        self.status_var.set("已选择一行数据")
    
    def add_row(self):
        # 创建空行
        new_row = {col: "" for col in self.df.columns}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.update_tree()
        self.status_var.set("已添加新行")
    
    def delete_row(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的行")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的行吗？"):
            for item in selected_items:
                values = self.tree.item(item)["values"]
                # 找到对应的行并删除
                for idx, row in self.df.iterrows():
                    if list(row) == values:
                        self.df = self.df.drop(idx)
                        break
            
            self.df = self.df.reset_index(drop=True)
            self.update_tree()
            self.status_var.set("已删除选中的行")
    
    def save_changes(self):
        try:
            # 获取当前选中的行
            selected_items = self.tree.selection()
            if selected_items:
                item = selected_items[0]
                idx = self.tree.index(item)
                
                # 更新DataFrame中的数据
                for column in self.df.columns:
                    self.df.at[idx, column] = self.edit_vars[column].get()
                
                # 更新树形视图
                self.tree.item(item, values=[self.edit_vars[col].get() for col in self.df.columns])
            
            # 保存到文件
            self.df.to_csv(self.current_file, index=False)
            messagebox.showinfo("成功", "保存成功！")
            self.status_var.set("更改已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
            self.status_var.set("保存失败")

def main():
    root = ThemedTk(theme="arc")  # 使用arc主题
    app = ModernCSVEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 