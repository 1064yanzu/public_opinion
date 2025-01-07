import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os

class CSVEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("舆情案例数据编辑器")
        self.root.geometry("1200x800")
        
        # 设置中文字体
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Microsoft YaHei", 10))
        self.style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        
        # 数据文件路径
        self.data_dir = "data"
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
    
    def create_widgets(self):
        # 创建文件选择框
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(file_frame, text="选择要编辑的文件：").pack(side="left")
        self.file_var = tk.StringVar()
        file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, values=list(self.files.keys()))
        file_combo.pack(side="left", padx=5)
        file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)
        
        # 创建按钮框
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加行", command=self.add_row).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="删除选中行", command=self.delete_row).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存更改", command=self.save_changes).pack(side="left", padx=5)
        
        # 创建表格
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll.set)
        self.tree.pack(fill="both", expand=True)
        
        self.tree_scroll.config(command=self.tree.yview)
        
        # 创建编辑框
        edit_frame = ttk.Frame(self.root)
        edit_frame.pack(fill="x", padx=5, pady=5)
        
        self.edit_vars = {}
        self.edit_entries = {}
        self.edit_frame = edit_frame
    
    def load_initial_data(self):
        self.file_var.set("案例基本信息")
        self.on_file_selected(None)
    
    def on_file_selected(self, event):
        file_name = self.files[self.file_var.get()]
        self.current_file = os.path.join(self.data_dir, file_name)
        
        try:
            self.df = pd.read_csv(self.current_file)
            self.update_tree()
            self.create_edit_fields()
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：{str(e)}")
    
    def update_tree(self):
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 设置列
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"
        
        for column in self.df.columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=100)
        
        # 添加数据
        for idx, row in self.df.iterrows():
            self.tree.insert("", "end", values=list(row))
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    def create_edit_fields(self):
        # 清空现有编辑框
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
        
        self.edit_vars = {}
        self.edit_entries = {}
        
        # 创建编辑框
        row = 0
        col = 0
        for column in self.df.columns:
            ttk.Label(self.edit_frame, text=column).grid(row=row, column=col*2, padx=5, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(self.edit_frame, textvariable=var)
            entry.grid(row=row, column=col*2+1, padx=5, pady=2)
            
            self.edit_vars[column] = var
            self.edit_entries[column] = entry
            
            col += 1
            if col >= 3:  # 每行显示3个字段
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
    
    def add_row(self):
        # 创建空行
        new_row = {col: "" for col in self.df.columns}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.update_tree()
    
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
    
    def save_changes(self):
        try:
            self.df.to_csv(self.current_file, index=False)
            messagebox.showinfo("成功", "保存成功！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

def main():
    root = tk.Tk()
    app = CSVEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 