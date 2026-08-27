# AICard/main_dialog.py
import os
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QTextEdit,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QWidget, QScrollArea, Qt,
    QMenu, QApplication, QFont, QToolButton
)
from aqt import mw
from aqt.operations import QueryOp
from aqt.utils import showInfo, showWarning
from .ai_service import AIService
from .settings_dialog import SettingsDialog
from .prompt_dialog import PromptManagerDialog

class AICardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("AI 批量生成卡片 (AICard)")
        self.resize(1240, 750)
        self.cards_data = []
        self.field_edits = {}
        self.active_edit = None
        self.is_updating_ui = False
        self.init_ui()
        self.load_decks_and_models()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ================= 左侧面板 =================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("<b>输入学习材料</b>"))
        self.material_input = QTextEdit()
        self.material_input.setPlaceholderText("在此粘贴学习资料，或通过提示词模板快速构造提炼需求...")
        left_layout.addWidget(self.material_input, stretch=3)

        # 文件上传 + 提示词快捷菜单栏
        tool_row = QHBoxLayout()
        tool_row.addWidget(QLabel("📎 上传文件:"))
        self.upload_btn = QPushButton("选择文件...")
        self.upload_btn.clicked.connect(self.on_upload_file)
        tool_row.addWidget(self.upload_btn)

        # 💡 提示词模板按钮
        self.prompt_btn = QPushButton("💡 提示词模板 ▾")
        self.prompt_btn.clicked.connect(self.show_prompt_menu)
        tool_row.addWidget(self.prompt_btn)
        tool_row.addStretch()
        left_layout.addLayout(tool_row)

        # 生成按钮
        self.gen_btn = QPushButton("🚀 开始生成卡片")
        self.gen_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 14px; padding: 8px;")
        self.gen_btn.clicked.connect(self.on_generate)
        left_layout.addWidget(self.gen_btn)

        # 预览表格
        left_layout.addWidget(QLabel("<b>生成的卡片预览</b>"))
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["选择", "正面 (字段1)", "背面 (字段2)"])
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.preview_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        left_layout.addWidget(self.preview_table, stretch=4)

        # 底部快捷操作栏
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

        # ================= 右侧面板 =================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 顶部配置栏 (牌组 & 笔记类型 & AI设置)
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

        # ================= 格式化小工具栏 (彻底修复：使用原生 QToolButton) =================
        fmt_toolbar = QHBoxLayout()
        fmt_toolbar.setSpacing(4)
        fmt_toolbar.setContentsMargins(0, 2, 0, 6)

        tools_def = [
            ("b", "B", "加粗 (Bold)", True, False, False, False),
            ("i", "I", "斜体 (Italic)", False, True, False, False),
            ("u", "U", "下划线 (Underline)", False, False, True, False),
            ("code", "</>", "代码块 (Code)", False, False, False, True),
            ("h", "H", "大标题 (Heading)", True, False, False, False),
        ]

        for tag, text, tooltip, is_bold, is_italic, is_underline, is_mono in tools_def:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 使用 autoRaise，让按钮呈现 Anki 原生的无边框扁平样式，悬浮时才亮起
            btn.setAutoRaise(True)
            
            # 仅修改字形，绝对不要修改字体颜色，交给 Anki 主题控制
            font = btn.font()
            font.setPointSize(12)
            font.setBold(is_bold)
            font.setItalic(is_italic)
            font.setUnderline(is_underline)
            if is_mono:
                font.setFamily("Courier New")
            btn.setFont(font)

            btn.clicked.connect(lambda checked, t=tag: self.format_active_text(t))
            fmt_toolbar.addWidget(btn)

        fmt_toolbar.addStretch()
        right_layout.addLayout(fmt_toolbar)

        # ======================================================================

        # 动态字段展示区（支持按模板字段自动扩展）
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

        # 底部导入栏
        bottom_bar = QHBoxLayout()
        self.copy_btn = QPushButton("复制选中卡片")
        self.copy_btn.clicked.connect(self.on_copy_selected)
        self.import_btn = QPushButton("添加到牌组")
        self.import_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 18px;")
        self.import_btn.clicked.connect(self.on_import)
        
        bottom_bar.addWidget(self.copy_btn)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.import_btn)
        right_layout.addLayout(bottom_bar)

        splitter.addWidget(right_widget)
        splitter.setSizes([560, 680])

    def show_prompt_menu(self):
        """弹出提示词快捷菜单"""
        config = mw.addonManager.getConfig(__name__) or {}
        prompts = config.get("prompts", [])
        
        menu = QMenu(self)
        for p in prompts:
            action = menu.addAction(p.get("title", "未命名提示词"))
            action.triggered.connect(lambda checked, content=p.get("content", ""): self.apply_prompt(content))
        
        menu.addSeparator()
        manage_action = menu.addAction("⚙ 管理/编辑提示词...")
        manage_action.triggered.connect(self.open_prompt_manager)

        menu.exec(self.prompt_btn.mapToGlobal(self.prompt_btn.rect().bottomLeft()))

    def apply_prompt(self, content: str):
        existing = self.material_input.toPlainText()
        if existing.strip():
            self.material_input.setText(content + "\n" + existing)
        else:
            self.material_input.setText(content)

    def open_prompt_manager(self):
        dlg = PromptManagerDialog(self)
        dlg.exec()

    def format_active_text(self, tag: str):
        """在活跃的字段输入框中应用 HTML 格式"""
        if not self.active_edit:
            if self.field_edits:
                self.active_edit = next(iter(self.field_edits.values()))
            else:
                return

        cursor = self.active_edit.textCursor()
        selected = cursor.selectedText()

        tag_pairs = {
            "b": ("<b>", "</b>"),
            "i": ("<i>", "</i>"),
            "u": ("<u>", "</u>"),
            "code": ("<code>", "</code>"),
            "h": ("<h3>", "</h3>")
        }

        if tag in tag_pairs:
            start_tag, end_tag = tag_pairs[tag]
            if selected:
                cursor.insertText(f"{start_tag}{selected}{end_tag}")
            else:
                pos = cursor.position()
                cursor.insertText(f"{start_tag}{end_tag}")
                cursor.setPosition(pos + len(start_tag))
                self.active_edit.setTextCursor(cursor)
        
        self.active_edit.setFocus()

    def load_decks_and_models(self):
        self.deck_combo.clear()
        for d in mw.col.decks.all_names_and_ids():
            self.deck_combo.addItem(d.name, d.id)

        self.model_combo.clear()
        for m in mw.col.models.all_names_and_ids():
            self.model_combo.addItem(m.name, m.id)

    def get_current_model_fields(self):
        model_id = self.model_combo.currentData()
        if not model_id:
            return []
        model = mw.col.models.get(model_id)
        return mw.col.models.field_names(model) if model else []

    def on_model_changed(self):
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.field_edits.clear()
        self.active_edit = None

        fields = self.get_current_model_fields()
        for field in fields:
            lbl = QLabel(f"<b>{field}</b>")
            edit = QTextEdit()
            edit.setPlaceholderText(f"输入 {field}...")
            edit.textChanged.connect(self.on_field_text_edited)
            edit.installEventFilter(self)
            self.fields_layout.addWidget(lbl)
            self.fields_layout.addWidget(edit)
            self.field_edits[field] = edit
        self.fields_layout.addStretch()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.FocusIn and isinstance(obj, QTextEdit):
            self.active_edit = obj
        return super().eventFilter(obj, event)

    def on_upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择学习材料", "", "Text Files (*.txt *.md)")
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
        provider = config.get("provider", "DeepSeek")
        if provider != "Ollama (本地)" and not config.get("api_key"):
            showWarning("请先点击右上角 [AI 配置] 填入对应服务商的 API Key！")
            return

        fields = self.get_current_model_fields()
        if not fields:
            showWarning("当前笔记类型不存在可用字段！")
            return

        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("AI 正在提炼制卡中...")

        def _op(col):
            return AIService.generate_cards(
                material=material,
                fields=fields,
                api_base=config.get("api_base", "https://api.deepseek.com"),
                api_key=config.get("api_key", ""),
                model=config.get("model", "deepseek-chat"),
                timeout=config.get("timeout", 60)
            )

        def _success(cards):
            self.gen_btn.setEnabled(True)
            self.gen_btn.setText("🚀 开始生成卡片")
            if not cards:
                showInfo("AI 未能提取出有效卡片，请检查材料或提示词。")
                return
            self.cards_data = cards
            self.refresh_preview_table()
            showInfo(f"🎉 成功生成 {len(cards)} 张卡片！")

        def _failure(err):
            self.gen_btn.setEnabled(True)
            self.gen_btn.setText("🚀 开始生成卡片")
            showWarning(f"生成异常: {str(err)}")

        QueryOp(parent=self, op=_op, success=_success).failure(_failure).run_in_background()

    def refresh_preview_table(self):
        self.is_updating_ui = True
        self.preview_table.setRowCount(len(self.cards_data))
        fields = self.get_current_model_fields()
        f1 = fields[0] if len(fields) > 0 else ""
        f2 = fields[1] if len(fields) > 1 else ""

        for row, card in enumerate(self.cards_data):
            item_check = QTableWidgetItem()
            item_check.setCheckState(Qt.CheckState.Checked)
            self.preview_table.setItem(row, 0, item_check)
            self.preview_table.setItem(row, 1, QTableWidgetItem(card.get(f1, "")))
            self.preview_table.setItem(row, 2, QTableWidgetItem(card.get(f2, "")))

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
        if self.is_updating_ui:
            return
        row = self.preview_table.currentRow()
        if 0 <= row < len(self.cards_data):
            fields = self.get_current_model_fields()
            for field, edit in self.field_edits.items():
                self.cards_data[row][field] = edit.toPlainText()
            
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
        rows = [r for r in range(self.preview_table.rowCount()) if self.preview_table.item(r, 0).checkState() == Qt.CheckState.Checked]
        if not rows:
            showInfo("请勾选需要删除的卡片！")
            return

        for r in reversed(rows):
            del self.cards_data[r]

        self.refresh_preview_table()
        if not self.cards_data:
            for edit in self.field_edits.values():
                edit.clear()

    def on_copy_selected(self):
        texts = []
        for r in range(self.preview_table.rowCount()):
            if self.preview_table.item(r, 0).checkState() == Qt.CheckState.Checked:
                texts.append(" | ".join(self.cards_data[r].values()))
        if texts:
            QApplication.clipboard().setText("\n".join(texts))
            showInfo("已将选中卡片文本复制到剪贴板！")

    def on_import(self):
        deck_id = self.deck_combo.currentData()
        model_id = self.model_combo.currentData()
        if not deck_id or not model_id:
            showWarning("牌组或笔记类型不存在！")
            return

        model = mw.col.models.get(model_id)
        tags = self.tags_input.text().strip().split()
        
        imported_count = 0
        for r in range(self.preview_table.rowCount()):
            if self.preview_table.item(r, 0).checkState() == Qt.CheckState.Checked:
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
            self.cards_data.clear()
            self.preview_table.setRowCount(0)
            for edit in self.field_edits.values():
                edit.clear()
        else:
            showWarning("没有勾选任何卡片进行导入。")