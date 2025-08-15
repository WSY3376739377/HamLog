# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import shutil
import time

# 导入我们已经解耦的后端模块
from modules.database import init_db, add_qso, delete_qso, update_qso_cell, query_qso, add_qso_batch
from modules.helpers import now_str, get_beijing_time, get_utc_time
from modules.config import load_config, save_config
from modules import adif
from modules import statistics

# Matplotlib for Tkinter
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

VERSION = '2.0.0-tk' # 更新版本号以反映UI重写
GITHUB_REPO = 'https://github.com/WSY3376739377/HamLog'

class HamLogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HamLog 日志软件")
        self.root.geometry("1000x750")

        # --- 创建主框架 ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(expand=True, fill='both')

        # --- 创建顶部信息栏 ---
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill='x', pady=5)
        
        ttk.Label(top_bar, text="HamLog 日志软件", font=("Arial", 18, "bold"), foreground="blue").pack(side='left')
        
        self.utc_time_label = ttk.Label(top_bar, text="", font=("Arial", 10))
        self.utc_time_label.pack(side='right', padx=10)
        ttk.Label(top_bar, text="UTC：").pack(side='right')
        
        self.bj_time_label = ttk.Label(top_bar, text="", font=("Arial", 10))
        self.bj_time_label.pack(side='right', padx=10)
        ttk.Label(top_bar, text="北京时间：").pack(side='right')

        # --- 创建选项卡控件 ---
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill="both", pady=5)

        # 创建各个选项卡的Frame
        self.add_tab = ttk.Frame(self.notebook, padding="10")
        self.query_tab = ttk.Frame(self.notebook, padding="10")
        self.stats_tab = ttk.Frame(self.notebook, padding="10")
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.about_tab = ttk.Frame(self.notebook, padding="10")

        # 将Frame添加到Notebook
        self.notebook.add(self.add_tab, text="增加日志")
        self.notebook.add(self.query_tab, text="查询日志")
        self.notebook.add(self.stats_tab, text="统计")
        self.notebook.add(self.settings_tab, text="设置")
        self.notebook.add(self.about_tab, text="关于")

        # 绑定选项卡切换事件，以便在切换到统计页面时自动刷新
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # --- 初始化功能 ---
        self.create_add_tab_widgets()
        self.create_query_tab_widgets()
        self.create_stats_tab_widgets()
        self.create_settings_tab_widgets()
        self.create_about_tab_widgets()
        
        self.update_time()

    def create_add_tab_widgets(self):
        # --- 加载默认值 ---
        self.config = load_config()
        defaults = self.config.get('defaults', {})

        # --- 使用 .grid() 布局 ---
        frame = ttk.Frame(self.add_tab)
        frame.pack(fill='x', padx=10, pady=10)

        # --- Tkinter 变量 ---
        self.add_tab_vars = {
            'call': tk.StringVar(value=defaults.get('call', '')),
            'mode': tk.StringVar(value=defaults.get('mode', '')),
            'freq': tk.StringVar(value=defaults.get('freq', '')),
            'power': tk.StringVar(value=defaults.get('power', '')),
            'datetime': tk.StringVar(value=now_str()),
            'qth_prov': tk.StringVar(value=defaults.get('qth_prov', '')),
            'qth_city': tk.StringVar(value=defaults.get('qth_city', '')),
            'rst_sent': tk.StringVar(value=defaults.get('rst_sent', '')),
            'rst_recv': tk.StringVar(value=defaults.get('rst_recv', '')),
            'device': tk.StringVar(value=defaults.get('device', ''))
        }

        # --- 创建控件 ---
        fields = [
            ("对方呼号*", 'call'), ("模式", 'mode'), ("频率(MHz)", 'freq'),
            ("功率(W)", 'power'), ("日期时间", 'datetime'), ("QTH 省", 'qth_prov'),
            ("QTH 市", 'qth_city'), ("信号报告(发)", 'rst_sent'),
            ("信号报告(收)", 'rst_recv'), ("设备", 'device')
        ]

        for i, (text, key) in enumerate(fields):
            ttk.Label(frame, text=text).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            if key == 'mode':
                widget = ttk.Combobox(frame, textvariable=self.add_tab_vars[key], values=['SSB','CW','FT8','RTTY','AM','FM'])
            else:
                widget = ttk.Entry(frame, textvariable=self.add_tab_vars[key])
            widget.grid(row=i, column=1, sticky='ew', padx=5)
        
        # 特殊处理 datetime 行
        ttk.Button(frame, text="设为当前时间", command=lambda: self.add_tab_vars['datetime'].set(now_str())).grid(row=4, column=2, padx=5)

        # 内容输入框
        ttk.Label(frame, text="内容").grid(row=len(fields), column=0, sticky='nw', padx=5, pady=5)
        self.content_text = tk.Text(frame, height=5, width=40)
        self.content_text.grid(row=len(fields), column=1, columnspan=2, sticky='ew', padx=5)
        if 'content' in defaults:
            self.content_text.insert('1.0', defaults.get('content', ''))

        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields)+1, column=1, pady=10, sticky='w')
        ttk.Button(button_frame, text="保存", command=self.save_qso).pack(side='left', padx=5)
        ttk.Button(button_frame, text="清空", command=self.clear_add_tab_entries).pack(side='left', padx=5)

        frame.columnconfigure(1, weight=1) # 让输入框列可以拉伸

    def clear_add_tab_entries(self):
        defaults = self.config.get('defaults', {})
        for key, var in self.add_tab_vars.items():
            var.set(defaults.get(key, ''))
        self.add_tab_vars['datetime'].set(now_str())
        self.content_text.delete('1.0', tk.END)
        if 'content' in defaults:
            self.content_text.insert('1.0', defaults.get('content', ''))

    def save_qso(self):
        values = {key: var.get() for key, var in self.add_tab_vars.items()}
        values['content'] = self.content_text.get('1.0', tk.END).strip()

        # --- 输入验证 ---
        try:
            if values['freq']: float(values['freq'])
            if values['power']: float(values['power'])
        except ValueError:
            messagebox.showerror('输入错误', '频率和功率必须为数字！')
            return

        try:
            add_qso(values)
            messagebox.showinfo('成功', '日志已保存')
            self.clear_add_tab_entries()
        except Exception as e:
            messagebox.showerror('保存失败', f'发生错误: {e}')

    def create_query_tab_widgets(self):
        # --- 搜索框和条件 ---
        search_frame = ttk.Frame(self.query_tab)
        search_frame.pack(fill='x', padx=5, pady=5)

        self.search_by_var = tk.StringVar(value='call')
        ttk.Radiobutton(search_frame, text="呼号", variable=self.search_by_var, value='call').pack(side='left', padx=5)
        ttk.Radiobutton(search_frame, text="频率", variable=self.search_by_var, value='freq').pack(side='left', padx=5)
        ttk.Radiobutton(search_frame, text="功率", variable=self.search_by_var, value='power').pack(side='left', padx=5)
        ttk.Radiobutton(search_frame, text="时间", variable=self.search_by_var, value='time').pack(side='left', padx=5)

        self.search_keyword_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_keyword_var, width=20)
        search_entry.pack(side='left', padx=5)
        search_entry.bind("<Return>", lambda event: self.search_qso()) # 绑定回车键
        ttk.Button(search_frame, text="查询", command=self.search_qso).pack(side='left', padx=5)

        # --- Treeview 表格 ---
        table_frame = ttk.Frame(self.query_tab)
        table_frame.pack(expand=True, fill='both', padx=5, pady=5)

        columns = ('id','呼号','模式','频率','功率','时间','省','市','发','收','设备','内容')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor='center')
        
        self.tree.column('id', width=40, stretch=False)
        self.tree.column('时间', width=150, stretch=False)
        self.tree.column('内容', width=200)

        # --- 滚动条 ---
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(expand=True, fill='both')

        # --- 右键菜单 ---
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="修改选中行", command=self.edit_selected_qso)
        self.tree_menu.add_command(label="删除选中行", command=self.delete_selected_qso)

        self.tree.bind("<Button-3>", self.show_tree_menu)

        # 初始加载所有数据
        self.search_qso()

    def search_qso(self):
        keyword = self.search_keyword_var.get()
        by = self.search_by_var.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            rows = query_qso(keyword, by)
            for row in rows:
                self.tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("查询失败", f"数据库查询出错: {e}")

    def show_tree_menu(self, event):
        # 选择被右键点击的行
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def delete_selected_qso(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("提示", "请先选择要删除的日志。")
            return

        item_values = self.tree.item(selected_item, 'values')
        rowid = item_values[0]
        
        if messagebox.askyesno("确认删除", f"您确定要删除呼号为 {item_values[1]} 的这条日志吗？"):
            try:
                delete_qso(rowid)
                self.tree.delete(selected_item)
            except Exception as e:
                messagebox.showerror("删除失败", f"发生错误: {e}")

    def edit_selected_qso(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("提示", "请先选择要修改的日志。")
            return

        item_values = self.tree.item(selected_item, 'values')
        rowid = item_values[0]
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title("修改日志")
        edit_win.transient(self.root) # 窗口置顶
        
        col_map = {
            '呼号': 1, '模式': 2, '频率': 3, '功率': 4, '时间': 5,
            'QTH（省）': 6, 'QTH（市）': 7, 'rst发': 8, 'rst收': 9,
            '设备': 10, '内容': 11
        }
        
        ttk.Label(edit_win, text="选择字段:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        col_var = tk.StringVar()
        col_combo = ttk.Combobox(edit_win, textvariable=col_var, values=list(col_map.keys()), state='readonly', width=38)
        col_combo.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(edit_win, text="新值:").grid(row=1, column=0, padx=10, pady=5, sticky='nw')
        val_text = tk.Text(edit_win, height=5, width=40)
        val_text.grid(row=1, column=1, padx=10, pady=5)

        def on_col_select(event):
            col_name = col_var.get()
            col_index = col_map[col_name]
            current_value = item_values[col_index]
            val_text.delete('1.0', tk.END)
            val_text.insert('1.0', current_value)
        
        col_combo.bind('<<ComboboxSelected>>', on_col_select)

        def save_edit():
            col_name = col_var.get()
            new_value = val_text.get('1.0', tk.END).strip()
            if not col_name:
                messagebox.showwarning("提示", "请选择要修改的字段。", parent=edit_win)
                return
            try:
                update_qso_cell(rowid, col_name, new_value)
                edit_win.destroy()
                self.search_qso()
            except Exception as e:
                messagebox.showerror("更新失败", f"发生错误: {e}", parent=edit_win)

        ttk.Button(edit_win, text="保存", command=save_edit).grid(row=2, column=1, pady=10, sticky='e')

    def create_stats_tab_widgets(self):
        ttk.Button(self.stats_tab, text="刷新统计数据", command=self.refresh_stats).pack(pady=10)
        self.stats_canvas_frame = ttk.Frame(self.stats_tab)
        self.stats_canvas_frame.pack(expand=True, fill='both')
        self.stats_canvas = None # 用于存储canvas对象

    def refresh_stats(self):
        # 清除旧的图表或提示
        for widget in self.stats_canvas_frame.winfo_children():
            widget.destroy()

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(self.stats_canvas_frame, text="统计图表功能不可用，请安装 matplotlib 库。").pack(pady=20)
            return

        try:
            records = query_qso()
            stats_counter = statistics.get_stats_by_mode(records)
            fig = statistics.create_mode_pie_chart(stats_counter)

            self.stats_canvas = FigureCanvasTkAgg(fig, master=self.stats_canvas_frame)
            self.stats_canvas.draw()
            self.stats_canvas.get_tk_widget().pack(expand=True, fill='both')
        except Exception as e:
            messagebox.showerror("统计错误", f"生成图表时出错: {e}")

    def on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if self.notebook.tab(selected_tab_index, "text") == "统计":
            self.refresh_stats()

    def create_settings_tab_widgets(self):
        # --- 默认值设置 ---
        defaults_frame = ttk.LabelFrame(self.settings_tab, text="默认值", padding="10")
        defaults_frame.pack(fill='x', padx=5, pady=5)

        defaults = self.config.get('defaults', {})
        self.defaults_vars = {
            'call': tk.StringVar(value=defaults.get('call', '')),
            'mode': tk.StringVar(value=defaults.get('mode', '')),
            'freq': tk.StringVar(value=defaults.get('freq', '')),
            'power': tk.StringVar(value=defaults.get('power', '')),
            'qth_prov': tk.StringVar(value=defaults.get('qth_prov', '')),
            'qth_city': tk.StringVar(value=defaults.get('qth_city', '')),
            'device': tk.StringVar(value=defaults.get('device', ''))
        }
        
        fields = [("呼号", 'call'), ("模式", 'mode'), ("频率", 'freq'), ("功率", 'power'),
                  ("省", 'qth_prov'), ("市", 'qth_city'), ("设备", 'device')]

        for i, (text, key) in enumerate(fields):
            ttk.Label(defaults_frame, text=text).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            ttk.Entry(defaults_frame, textvariable=self.defaults_vars[key], width=30).grid(row=i, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Button(defaults_frame, text="保存默认值", command=self.save_defaults).grid(row=len(fields), column=1, sticky='e', padx=5, pady=10)
        defaults_frame.columnconfigure(1, weight=1)

        # --- 数据操作 ---
        data_frame = ttk.LabelFrame(self.settings_tab, text="数据操作", padding="10")
        data_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(data_frame, text="恢复数据库", command=self.restore_db).pack(side='left', padx=5)
        ttk.Button(data_frame, text="备份数据库", command=self.backup_db).pack(side='left', padx=5)
        ttk.Button(data_frame, text="从 ADIF 导入", command=self.import_adif).pack(side='left', padx=5)
        ttk.Button(data_frame, text="导出为 ADIF", command=self.export_adif).pack(side='left', padx=5)

        # --- 反馈/更新 ---
        feedback_frame = ttk.LabelFrame(self.settings_tab, text="反馈/更新", padding="10")
        feedback_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(feedback_frame, text="GitHub", command=lambda: webbrowser.open(GITHUB_REPO)).pack(side='left', padx=5)
        ttk.Button(feedback_frame, text="检查更新", command=lambda: webbrowser.open(GITHUB_REPO + '/releases/latest')).pack(side='left', padx=5)
        ttk.Button(feedback_frame, text="QQ群: 959244571", command=lambda: messagebox.showinfo("QQ群", "QQ群号: 959244571")).pack(side='left', padx=5)

    def save_defaults(self):
        self.config.setdefault('defaults', {})
        for key, var in self.defaults_vars.items():
            self.config['defaults'][key] = var.get()
        try:
            save_config(self.config)
            messagebox.showinfo("成功", "默认值已保存。")
        except Exception as e:
            messagebox.showerror("失败", f"保存配置失败: {e}")

    def import_adif(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(title="选择要导入的 ADIF 文件", filetypes=(("ADIF Files", "*.adi"), ("All Files", "*.*")))
        if not filepath: return
        try:
            qso_to_add = adif.import_from_adif(filepath)
            if qso_to_add:
                inserted_count = add_qso_batch(qso_to_add)
                messagebox.showinfo('导入完成', f'成功导入 {inserted_count} / {len(qso_to_add)} 条记录。')
                self.search_qso() # 刷新表格
            else:
                messagebox.showinfo('导入结束', '没有找到可导入的有效记录。')
        except Exception as e:
            messagebox.showerror("导入失败", f"发生错误: {e}")

    def export_adif(self):
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(title="保存为 ADIF 文件", defaultextension=".adi", filetypes=(("ADIF Files", "*.adi"),))
        if not filepath: return
        try:
            records = query_qso()
            adif.export_to_adif(records, filepath)
            messagebox.showinfo('成功', f'日志已成功导出到:\n{filepath}')
        except Exception as e:
            messagebox.showerror('导出失败', f'发生错误: {e}')

    def backup_db(self):
        from tkinter import filedialog
        source_db = 'hamlog.db'
        if not os.path.exists(source_db):
            messagebox.showerror('错误', '数据库文件 hamlog.db 不存在，无法备份。')
            return
        backup_filename = f"hamlog_backup_{time.strftime('%Y%m%d_%H%M%S')}.db"
        filepath = filedialog.asksaveasfilename(title="保存数据库备份", initialfile=backup_filename, filetypes=(("SQLite Database", "*.db"),))
        if not filepath: return
        try:
            shutil.copy(source_db, filepath)
            messagebox.showinfo('备份成功', f'数据库已成功备份到:\n{filepath}')
        except Exception as e:
            messagebox.showerror('备份失败', f'发生错误: {e}')

    def restore_db(self):
        from tkinter import filedialog
        if not messagebox.askyesno("确认恢复", '警告：此操作将用备份文件覆盖当前数据库。\n所有未备份的数据都将丢失！\n\n您确定要继续吗？'):
            return
        filepath = filedialog.askopenfilename(title="选择要恢复的数据库备份文件", filetypes=(("SQLite Database", "*.db"), ("All Files", "*.*")))
        if not filepath or not os.path.exists(filepath): return
        try:
            shutil.copy(filepath, 'hamlog.db')
            messagebox.showinfo('恢复成功', '数据库已恢复。\n请立即重启程序以加载新数据。')
        except Exception as e:
            messagebox.showerror('恢复失败', f'发生错误: {e}')

    def create_about_tab_widgets(self):
        frame = ttk.Frame(self.about_tab)
        frame.pack(pady=50)
        ttk.Label(frame, text="HamLog 业余无线电日志", font=("Arial", 24, "bold")).pack(pady=10)
        ttk.Label(frame, text=f"版本: {VERSION}").pack(pady=5)
        ttk.Label(frame, text="作者: C盘研究所、BG5JQN").pack(pady=5)
        link = ttk.Label(frame, text="GitHub 项目地址", foreground="blue", cursor="hand2")
        link.pack(pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_REPO))

    def update_time(self):
        """每秒更新顶部的时间标签"""
        self.bj_time_label.config(text=get_beijing_time())
        self.utc_time_label.config(text=get_utc_time())
        self.root.after(1000, self.update_time) # 1秒后再次调用此函数

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 创建主窗口
    root = tk.Tk()
    app = HamLogApp(root)
    
    # 运行事件循环
    root.mainloop()