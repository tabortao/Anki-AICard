import os
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QTextEdit,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QWidget, QScrollArea, Qt, QApplication
)
from aqt import mw
from aqt.operations import QueryOp
from aqt.utils import showInfo, showWarning
from .ai_service import AIService
from .settings_dialog import SettingsDialog

class AICardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("AI 生成卡片")
        self.resize(1200, 720)
        self.cards_data = []  # 存储生成的卡片字段数据列表
        self.field_edits = {} # 动态字段输入框映射
        self.is_updating_ui = False
        self.init_ui()
        self.load_decks_and_models()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ----------------- 左侧面板 -----------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("<b>输入学习材料</b>"))
        self.material_input = QTextEdit()
        self.material_input.setPlaceholderText("在此粘贴学习资料、笔记、词汇列表...")
        left_layout.addWidget(self.material_input, stretch=3)

        # 上传文件行
        upload_layout = QHBoxLayout()
        upload_layout.addWidget(QLabel("📎 上传文件 (txt/md):"))
        self.upload_btn = QPushButton("选择文件...")
        self.upload_btn.clicked.connect(self.on_upload_file)
        upload_layout.addWidget(self.upload_btn)
        upload_layout.addStretch()
        left_layout.addLayout(upload_layout)

        # 生成按钮
        self.gen_btn = QPushButton("生成卡片")
        self.gen_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px;")
        self.gen_btn.clicked.connect(self.on_generate)
        left_layout.addWidget(self.gen_btn)

        # 预览区
        left_layout.addWidget(QLabel("<b>生成的卡片预览</b>"))
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["选择", "正面 (问题)", "背面 (答案)"])
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.preview_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        left_layout.addWidget(self.preview_table, stretch=4)

        # 底部快捷选择与操作栏
        action_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(lambda: self.set_all_checked(True))
        self.unselect_all_btn = QPushButton("取消全选")
        self.unselect_all_btn.clicked.connect(lambda: self.set_all_checked(False))
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self.on_delete_selected)
        
        action_layout.addWidget(self.select_all_btn)
        action_layout.addWidget(self.unselect_all_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        left_layout.addLayout(action_layout)

        splitter.addWidget(left_widget)

        # ----------------- 右侧面板 -----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 顶部：牌组 & 笔记类型 & 配置
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("牌组:"))
        self.deck_combo = QComboBox()
        top_bar.addWidget(self.deck_combo, stretch=2)

        top_bar.addWidget(QLabel("笔记类型:"))
        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        top_bar.addWidget(self.model_combo, stretch=2)

        self.settings_btn = QPushButton("⚙ AI 配置")
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)
        right_layout.addLayout(top_bar)

        # 动态字段编辑区（可滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.scroll_area.setWidget(self.fields_container)
        right_layout.addWidget(self.scroll_area, stretch=1)

        # 标签栏
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("# 标签:"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("添加标签，空格分隔...")
        tag_layout.addWidget(self.tags_input)
        right_layout.addLayout(tag_layout)

        # 底部导入按钮
        bottom_bar = QHBoxLayout()
        self.copy_btn = QPushButton("复制选中卡片")
        self.copy_btn.clicked.connect(self.on_copy_selected)
        self.import_btn = QPushButton("添加到牌组")
        self.import_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.import_btn.clicked.connect(self.on_import)
        
        bottom_bar.addWidget(self.copy_btn)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.import_btn)
        right_layout.addLayout(bottom_bar)

        splitter.addWidget(right_widget)
        splitter.setSizes([550, 650])

    def load_decks_and_models(self):
        """载入 Anki 本地牌组和笔记类型"""
        # 载入牌组
        self.deck_combo.clear()
        decks = mw.col.decks.all_names_and_ids()
        for d in decks:
            self.deck_combo.addItem(d.name, d.id)

        # 载入笔记模板
        self.model_combo.clear()
        models = mw.col.models.all_names_and_ids()
        for m in models:
            self.model_combo.addItem(m.name, m.id)

    def get_current_model_fields(self):
        model_id = self.model_combo.currentData()
        if not model_id:
            return []
        model = mw.col.models.get(model_id)
        return mw.col.models.field_names(model) if model else []

    def on_model_changed(self):
        """当用户切换笔记模板时，动态重构右侧编辑框"""
        # 清空旧控件
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.field_edits.clear()

        fields = self.get_current_model_fields()
        for field in fields:
            lbl = QLabel(f"<b>{field}</b>")
            edit = QTextEdit()
            edit.setPlaceholderText(f"输入 {field}...")
            edit.textChanged.connect(self.on_field_text_edited)
            self.fields_layout.addWidget(lbl)
            self.fields_layout.addWidget(edit)
            self.field_edits[field] = edit
        self.fields_layout.addStretch()

    def on_upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择学习材料文件", "", "Text Files (*.txt *.md)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.material_input.setText(f.read())
            except Exception as e:
                showWarning(f"读取文件失败: {str(e)}")

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def on_generate(self):
        material = self.material_input.toPlainText().strip()
        if not material:
            showWarning("请先输入学习材料！")
            return

        config = mw.addonManager.getConfig(__name__) or {}
        if not config.get("api_key"):
            showWarning("请先点击右上角 [AI 配置] 设置 API Key！")
            return

        fields = self.get_current_model_fields()
        if not fields:
            showWarning("当前笔记类型不存在有效字段！")
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("AI 正在提炼制卡中...")

        # 后台异步执行
        def _op(col):
            return AIService.generate_cards(
                material=material,
                fields=fields,
                api_base=config.get("api_base", "https://api.openai.com/v1"),
                api_key=config.get("api_key", ""),
                model=config.get("model", "gpt-4o-mini"),
                timeout=config.get("timeout", 60)
            )

        def _success(cards):
            self.gen_btn.setEnabled(True)
            self.gen_btn.setText("生成卡片")
            if not cards:
                showInfo("AI 未能从材料中提取出有效卡片。")
                return
            self.cards_data = cards
            self.refresh_preview_table()
            showInfo(f"成功生成 {len(cards)} 张卡片！")

        def _failure(err):
            self.gen_btn.setEnabled(True)
            self.gen_btn.setText("生成卡片")
            showWarning(f"生成失败: {str(err)}")

        QueryOp(parent=self, op=_op, success=_success).failure(_failure).run_in_background()

    def refresh_preview_table(self):
        """刷新左侧表格数据"""
        self.is_updating_ui = True
        self.preview_table.setRowCount(len(self.cards_data))
        fields = self.get_current_model_fields()
        f1 = fields[0] if len(fields) > 0 else ""
        f2 = fields[1] if len(fields) > 1 else ""

        for row, card in enumerate(self.cards_data):
            # Checkbox
            item_check = QTableWidgetItem()
            item_check.setCheckState(Qt.CheckState.Checked)
            self.preview_table.setItem(row, 0, item_check)

            # Col 1 & Col 2
            val1 = card.get(f1, "")
            val2 = card.get(f2, "")
            self.preview_table.setItem(row, 1, QTableWidgetItem(val1))
            self.preview_table.setItem(row, 2, QTableWidgetItem(val2))

        self.is_updating_ui = False
        if self.cards_data:
            self.preview_table.selectRow(0)

    def on_table_selection_changed(self):
        if self.is_updating_ui:
            return
        row = self.preview_table.currentRow()
        if 0 <= row < len(self.cards_data):
            card = self.cards_data[row]
            self.is_updating_ui = True
            for field, edit in self.field_edits.items():
                edit.setText(card.get(field, ""))
            self.is_updating_ui = False

    def on_field_text_edited(self):
        """右侧手动修改内容时同步更新内存和表格"""
        if self.is_updating_ui:
            return
        row = self.preview_table.currentRow()
        if 0 <= row < len(self.cards_data):
            fields = self.get_current_model_fields()
            for field, edit in self.field_edits.items():
                self.cards_data[row][field] = edit.toPlainText()
            
            # 同步更新前两列显示
            self.is_updating_ui = True
            if len(fields) > 0:
                self.preview_table.setItem(row, 1, QTableWidgetItem(self.cards_data[row].get(fields[0], "")))
            if len(fields) > 1:
                self.preview_table.setItem(row, 2, QTableWidgetItem(self.cards_data[row].get(fields[1], "")))
            self.is_updating_ui = False

    def set_all_checked(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for r in range(self.preview_table.rowCount()):
            item = self.preview_table.item(r, 0)
            if item:
                item.setCheckState(state)

    def on_delete_selected(self):
        rows_to_delete = []
        for r in range(self.preview_table.rowCount()):
            item = self.preview_table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                rows_to_delete.append(r)

        if not rows_to_delete:
            showInfo("请勾选需要删除的卡片！")
            return

        for r in reversed(rows_to_delete):
            del self.cards_data[r]

        self.refresh_preview_table()
        if not self.cards_data:
            for edit in self.field_edits.values():
                edit.clear()

    def on_copy_selected(self):
        selected_texts = []
        for r in range(self.preview_table.rowCount()):
            item = self.preview_table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                card = self.cards_data[r]
                line = " | ".join(card.values())
                selected_texts.append(line)
        if selected_texts:
            QApplication.clipboard().setText("\n".join(selected_texts))
            showInfo("已复制选中卡片数据到剪贴板！")

    def on_import(self):
        """导入勾选的卡片到指定牌组"""
        deck_id = self.deck_combo.currentData()
        model_id = self.model_combo.currentData()
        if not deck_id or not model_id:
            showWarning("牌组或笔记类型未找到！")
            return

        model = mw.col.models.get(model_id)
        tags = self.tags_input.text().strip().split()
        
        imported_count = 0
        for r in range(self.preview_table.rowCount()):
            item = self.preview_table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                card_data = self.cards_data[r]
                note = mw.col.new_note(model)
                for fld, val in card_data.items():
                    if fld in note:
                        note[fld] = val
                note.tags = tags
                mw.col.add_note(note, deck_id)
                imported_count += 1

        if imported_count > 0:
            showInfo(f"🎉 成功导入 {imported_count} 张卡片到当前牌组！")
            self.material_input.clear()
            self.cards_data.clear()
            self.preview_table.setRowCount(0)
            for edit in self.field_edits.values():
                edit.clear()
        else:
            showWarning("没有勾选任何卡片进行导入。")