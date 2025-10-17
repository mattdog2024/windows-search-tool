"""
搜索历史对话框

Story 2.6: 搜索历史和快捷功能
- 显示搜索历史
- 支持选择历史查询
- 删除历史记录
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from datetime import datetime


class SearchHistoryDialog:
    """
    搜索历史对话框

    显示最近和热门的搜索记录
    """

    def __init__(self, parent, search_history):
        """
        初始化对话框

        Args:
            parent: 父窗口
            search_history: 搜索历史管理器
        """
        self.parent = parent
        self.search_history = search_history
        self.selected_query = None

        # 创建窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("搜索历史")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_history()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 使用 Notebook 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 最近搜索页
        self._create_recent_tab(notebook)

        # 热门搜索页
        self._create_popular_tab(notebook)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="使用选中的查询",
            command=self._use_query
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="删除选中项",
            command=self._delete_selected
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="清空历史",
            command=self._clear_all
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="关闭",
            command=self._close
        ).pack(side=tk.LEFT, padx=5)

    def _create_recent_tab(self, notebook):
        """创建最近搜索页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="最近搜索")

        # 创建 Treeview
        columns = ("查询", "模式", "结果数", "时间")
        self.recent_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 设置列
        self.recent_tree.heading("#0", text="序号")
        self.recent_tree.column("#0", width=50, minwidth=50)

        self.recent_tree.heading("查询", text="查询")
        self.recent_tree.heading("模式", text="模式")
        self.recent_tree.heading("结果数", text="结果数")
        self.recent_tree.heading("时间", text="时间")

        self.recent_tree.column("查询", width=250)
        self.recent_tree.column("模式", width=100)
        self.recent_tree.column("结果数", width=100)
        self.recent_tree.column("时间", width=150)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=self.recent_tree.yview
        )
        self.recent_tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击使用查询
        self.recent_tree.bind('<Double-1>', lambda e: self._use_query())

    def _create_popular_tab(self, notebook):
        """创建热门搜索页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="热门搜索")

        # 创建 Treeview
        columns = ("查询", "搜索次数", "最后使用")
        self.popular_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 设置列
        self.popular_tree.heading("#0", text="排名")
        self.popular_tree.column("#0", width=50, minwidth=50)

        self.popular_tree.heading("查询", text="查询")
        self.popular_tree.heading("搜索次数", text="搜索次数")
        self.popular_tree.heading("最后使用", text="最后使用")

        self.popular_tree.column("查询", width=300)
        self.popular_tree.column("搜索次数", width=100)
        self.popular_tree.column("最后使用", width=150)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=self.popular_tree.yview
        )
        self.popular_tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.popular_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击使用查询
        self.popular_tree.bind('<Double-1>', lambda e: self._use_query())

    def _load_history(self):
        """加载历史记录"""
        # 加载最近搜索
        recent = self.search_history.get_recent_searches(limit=50)

        for i, item in enumerate(recent, 1):
            query = item['query']
            mode = item.get('mode', 'fts')
            result_count = item.get('result_count', 0)
            timestamp = item.get('timestamp', '')

            # 格式化时间
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
            else:
                time_str = ""

            # 格式化模式
            mode_map = {'fts': '全文搜索', 'semantic': '语义搜索', 'hybrid': '混合搜索'}
            mode_str = mode_map.get(mode, mode)

            self.recent_tree.insert(
                '',
                'end',
                text=str(i),
                values=(query, mode_str, result_count, time_str)
            )

        # 加载热门搜索
        popular = self.search_history.get_popular_searches(limit=20)

        for i, item in enumerate(popular, 1):
            query = item['query']
            count = item.get('count', 0)
            timestamp = item.get('timestamp', '')

            # 格式化时间
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
            else:
                time_str = ""

            self.popular_tree.insert(
                '',
                'end',
                text=str(i),
                values=(query, count, time_str)
            )

    def _use_query(self):
        """使用选中的查询"""
        # 检查哪个 tab 是活动的
        recent_selection = self.recent_tree.selection()
        popular_selection = self.popular_tree.selection()

        if recent_selection:
            item = self.recent_tree.item(recent_selection[0])
            self.selected_query = item['values'][0]  # 查询列
            self.dialog.destroy()

        elif popular_selection:
            item = self.popular_tree.item(popular_selection[0])
            self.selected_query = item['values'][0]  # 查询列
            self.dialog.destroy()

        else:
            messagebox.showwarning("警告", "请先选择一个查询")

    def _delete_selected(self):
        """删除选中的记录"""
        recent_selection = self.recent_tree.selection()
        popular_selection = self.popular_tree.selection()

        query = None

        if recent_selection:
            item = self.recent_tree.item(recent_selection[0])
            query = item['values'][0]
            self.recent_tree.delete(recent_selection[0])

        elif popular_selection:
            item = self.popular_tree.item(popular_selection[0])
            query = item['values'][0]

        if query:
            self.search_history.remove_search(query)
            # 重新加载
            self._reload_all()
            messagebox.showinfo("提示", "已删除选中的记录")
        else:
            messagebox.showwarning("警告", "请先选择一个记录")

    def _clear_all(self):
        """清空所有历史"""
        response = messagebox.askyesno("确认", "确定要清空所有搜索历史吗?")

        if response:
            self.search_history.clear_history()
            self._reload_all()
            messagebox.showinfo("提示", "搜索历史已清空")

    def _reload_all(self):
        """重新加载所有列表"""
        # 清空现有项
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        for item in self.popular_tree.get_children():
            self.popular_tree.delete(item)

        # 重新加载
        self._load_history()

    def _close(self):
        """关闭对话框"""
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """
        显示对话框

        Returns:
            选中的查询,如果取消则返回 None
        """
        self.dialog.wait_window()
        return self.selected_query


def show_search_history_dialog(parent, search_history) -> Optional[str]:
    """
    显示搜索历史对话框

    Args:
        parent: 父窗口
        search_history: 搜索历史管理器

    Returns:
        选中的查询
    """
    dialog = SearchHistoryDialog(parent, search_history)
    return dialog.show()
