"""
索引库选择器 UI 组件

允许用户选择要搜索的索引库（全部/单选/多选）
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class IndexLibrarySelector(ttk.Frame):
    """
    索引库选择器组件

    显示当前选择的索引库，并提供弹出菜单选择多个索引库
    """

    def __init__(self, parent, library_manager, on_selection_changed: Optional[Callable] = None):
        """
        初始化索引库选择器

        Args:
            parent: 父组件
            library_manager: IndexLibraryManager 实例
            on_selection_changed: 选择变化时的回调函数
        """
        super().__init__(parent)
        self.library_manager = library_manager
        self.on_selection_changed = on_selection_changed

        self._create_widgets()

    def _create_widgets(self):
        """创建 UI 组件"""
        # 标签
        ttk.Label(self, text="搜索范围:").pack(side=tk.LEFT, padx=(5, 2))

        # 显示当前选择的按钮
        self.selector_button = ttk.Button(
            self,
            text=self._get_selection_text(),
            command=self._show_selector_dialog,
            width=25
        )
        self.selector_button.pack(side=tk.LEFT, padx=2)

        # 管理按钮
        ttk.Button(
            self,
            text="管理...",
            command=self._show_management_dialog,
            width=8
        ).pack(side=tk.LEFT, padx=2)

    def _get_selection_text(self) -> str:
        """获取当前选择的显示文本"""
        return self.library_manager.get_selection_summary()

    def _show_selector_dialog(self):
        """显示索引库选择对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("选择索引库")
        dialog.geometry("520x450")  # 增加高度以显示按钮
        # dialog.transient(self.master)  # 移除这行以允许窗口拖动
        dialog.grab_set()

        # 顶部说明
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            info_frame,
            text="选择要搜索的索引库：",
            font=("", 10, "bold")
        ).pack(anchor=tk.W)

        # 全选/全不选（加粗显示，与索引库列表区分）
        select_all_frame = ttk.Frame(dialog)
        select_all_frame.pack(fill=tk.X, padx=10, pady=5)

        self.select_all_var = tk.BooleanVar(value=self._is_all_enabled())

        select_all_cb = ttk.Checkbutton(
            select_all_frame,
            text="☑ 全选/全不选",
            variable=self.select_all_var,
            command=self._toggle_all
        )
        select_all_cb.pack(side=tk.LEFT)

        # 添加说明
        ttk.Label(
            select_all_frame,
            text="（勾选此项将选中/取消所有索引库）",
            foreground="gray",
            font=("", 8)
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Separator(dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 索引库列表标题
        ttk.Label(
            dialog,
            text="可用的索引库：",
            font=("", 9)
        ).pack(anchor=tk.W, padx=15, pady=(5, 0))

        # 索引库列表（带滚动条）- 限制高度，不占满所有空间
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))

        # 创建 Canvas 和 Scrollbar 用于滚动
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 索引库复选框列表
        self.library_vars = {}

        for library in self.library_manager.get_all_libraries():
            var = tk.BooleanVar(value=library.enabled)
            self.library_vars[library.name] = var

            # 创建复选框框架
            cb_frame = ttk.Frame(scrollable_frame)
            cb_frame.pack(fill=tk.X, pady=3)

            # 复选框
            cb = ttk.Checkbutton(
                cb_frame,
                text=library.name,
                variable=var,
                command=lambda: self._on_library_toggled()
            )
            cb.pack(side=tk.LEFT, anchor=tk.W)

            # 统计信息
            stats_text = f"({library.doc_count} 个文档"
            if library.size_bytes > 0:
                size_mb = library.size_bytes / (1024 * 1024)
                stats_text += f", {size_mb:.1f} MB"
            stats_text += ")"

            ttk.Label(
                cb_frame,
                text=stats_text,
                foreground="gray"
            ).pack(side=tk.LEFT, padx=(5, 0))

            # 数据库路径（小字）
            ttk.Label(
                scrollable_frame,
                text=f"    路径: {library.db_path}",
                foreground="gray",
                font=("", 8)
            ).pack(anchor=tk.W)

        # 底部按钮（使用 pack 的 side=BOTTOM 确保始终可见）
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text="取消",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            btn_frame,
            text="确定",
            command=lambda: self._apply_selection(dialog)
        ).pack(side=tk.RIGHT, padx=2)

    def _is_all_enabled(self) -> bool:
        """检查是否所有索引库都已启用"""
        enabled = self.library_manager.get_enabled_libraries()
        total = len(self.library_manager.get_all_libraries())
        return len(enabled) == total

    def _toggle_all(self):
        """全选/全不选"""
        enable_all = self.select_all_var.get()

        # 更新所有复选框
        for var in self.library_vars.values():
            var.set(enable_all)

    def _on_library_toggled(self):
        """索引库复选框切换事件"""
        # 检查是否所有都被选中，更新"全选"复选框
        all_enabled = all(var.get() for var in self.library_vars.values())
        self.select_all_var.set(all_enabled)

    def _apply_selection(self, dialog):
        """应用选择"""
        # 至少选择一个索引库
        enabled_count = sum(1 for var in self.library_vars.values() if var.get())

        if enabled_count == 0:
            messagebox.showwarning(
                "警告",
                "请至少选择一个索引库！",
                parent=dialog
            )
            return

        # 更新索引库启用状态
        for name, var in self.library_vars.items():
            self.library_manager.set_library_enabled(name, var.get())

        # 更新按钮文本
        self.selector_button.config(text=self._get_selection_text())

        # 调用回调
        if self.on_selection_changed:
            self.on_selection_changed()

        logger.info(f"索引库选择已更新: {enabled_count} 个库已启用")

        # 关闭对话框
        dialog.destroy()

    def _show_management_dialog(self):
        """显示索引库管理对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("索引库管理")
        dialog.geometry("600x450")
        # dialog.transient(self.master)  # 移除这行以允许窗口拖动
        dialog.grab_set()

        # 顶部说明
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            info_frame,
            text="索引库管理",
            font=("", 11, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            info_frame,
            text="管理所有索引库，添加新库或删除现有库",
            foreground="gray"
        ).pack(anchor=tk.W)

        ttk.Separator(dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 索引库列表（带 Treeview）
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建 Treeview
        columns = ('name', 'docs', 'size', 'path')
        tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)

        tree.heading('#0', text='')
        tree.heading('name', text='索引库名称')
        tree.heading('docs', text='文档数')
        tree.heading('size', text='大小')
        tree.heading('path', text='数据库路径')

        tree.column('#0', width=30)
        tree.column('name', width=150)
        tree.column('docs', width=80)
        tree.column('size', width=80)
        tree.column('path', width=250)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充数据
        for library in self.library_manager.get_all_libraries():
            size_mb = library.size_bytes / (1024 * 1024) if library.size_bytes > 0 else 0
            tree.insert('', tk.END, values=(
                library.name,
                library.doc_count,
                f"{size_mb:.1f} MB",
                library.db_path
            ))

        # 操作按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text="+ 添加索引库",
            command=lambda: self._add_library_dialog(dialog, tree)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="− 删除所选",
            command=lambda: self._delete_selected_library(tree)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="刷新统计",
            command=lambda: self._refresh_library_stats(tree)
        ).pack(side=tk.LEFT, padx=2)

        # 关闭按钮
        ttk.Button(
            btn_frame,
            text="关闭",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=2)

    def _add_library_dialog(self, parent, tree):
        """添加索引库对话框"""
        from tkinter import filedialog
        import tkinter.simpledialog as simpledialog
        import os

        # 选择数据库文件
        db_file = filedialog.askopenfilename(
            title="选择索引库数据库文件",
            filetypes=[
                ("SQLite 数据库", "*.db"),
                ("所有文件", "*.*")
            ],
            parent=parent
        )

        if not db_file:
            return

        # 简化对话框：只询问库名
        library_name = simpledialog.askstring(
            "输入索引库名称",
            "请为这个索引库输入一个名称：",
            initialvalue=os.path.basename(db_file).replace('.db', ''),
            parent=parent
        )

        if not library_name:
            return

        # 添加到管理器
        try:
            self.library_manager.add_library(
                name=library_name,
                db_path=db_file,
                set_as_default=False
            )

            # 刷新 Treeview
            size_mb = 0  # 暂时显示为 0
            tree.insert('', tk.END, values=(
                library_name,
                0,  # doc_count
                f"{size_mb:.1f} MB",
                db_file
            ))

            # 更新按钮文本
            self.selector_button.config(text=self._get_selection_text())

            messagebox.showinfo(
                "成功",
                f"索引库 '{library_name}' 已添加！\n\n"
                f"数据库文件: {db_file}\n\n"
                f"请关闭并重新打开索引库选择对话框以查看新库。",
                parent=parent
            )

            logger.info(f"成功添加索引库: {library_name} -> {db_file}")

            # 关闭管理对话框，提示用户重新打开选择对话框
            parent.destroy()
        except Exception as e:
            messagebox.showerror(
                "错误",
                f"添加索引库失败: {e}",
                parent=parent
            )

    def _delete_selected_library(self, tree):
        """删除选中的索引库"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的索引库！")
            return

        # 获取选中的索引库名称
        item = tree.item(selection[0])
        library_name = item['values'][0]

        # 确认删除
        response = messagebox.askyesno(
            "确认删除",
            f"确定要删除索引库 '{library_name}' 吗？\n\n"
            "注意：这只会从列表中移除索引库，不会删除数据库文件。"
        )

        if response:
            if self.library_manager.remove_library(library_name):
                tree.delete(selection[0])
                # 更新按钮文本
                self.selector_button.config(text=self._get_selection_text())
                messagebox.showinfo("成功", f"索引库 '{library_name}' 已删除")
            else:
                messagebox.showerror("错误", "删除索引库失败")

    def _refresh_library_stats(self, tree):
        """刷新索引库统计信息"""
        messagebox.showinfo(
            "提示",
            "统计信息刷新功能将在后续版本实现。"
        )

    def refresh_display(self):
        """刷新显示（外部调用）"""
        self.selector_button.config(text=self._get_selection_text())
