import uuid
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, 
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox, Qt
)
from aqt import mw

class PromptManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("提示词模板管理")
        self.resize(700, 450)
        self.config = mw.addonManager.getConfig(__name__) or {}
        self.prompts = list(self.config.get("prompts", []))
        self.current_index = -1
        self.init_ui()
        self.load_prompts()

    def init_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 左侧：列表 + 新建/删除
        left_box = QVBoxLayout()
        left_widget = QDialog()
        left_widget.setLayout(left_box)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select_prompt)
        left_box.addWidget(QLabel("<b>已有提示词：</b>"))
        left_box.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ 新建")
        self.add_btn.clicked.connect(self.on_add)
        self.del_btn = QPushButton("🗑 删除")
        self.del_btn.clicked.connect(self.on_delete)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.del_btn)
        left_box.addLayout(btn_row)
        splitter.addWidget(left_widget)

        # 右侧：编辑区域
        right_box = QVBoxLayout()
        right_widget = QDialog()
        right_widget.setLayout(right_box)

        right_box.addWidget(QLabel("<b>标题:</b>"))
        self.title_input = QLineEdit()
        right_box.addWidget(self.title_input)

        right_box.addWidget(QLabel("<b>提示词内容:</b>"))
        self.content_input = QTextEdit()
        right_box.addWidget(self.content_input)

        save_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存修改")
        self.save_btn.clicked.connect(self.on_save_current)
        save_row.addStretch()
        save_row.addWidget(self.save_btn)
        right_box.addLayout(save_row)
        splitter.addWidget(right_widget)

        splitter.setSizes([220, 480])

    def load_prompts(self):
        self.list_widget.clear()
        for p in self.prompts:
            self.list_widget.addItem(p.get("title", "未命名提示词"))
        if self.prompts:
            self.list_widget.setCurrentRow(0)

    def on_select_prompt(self, row: int):
        self.current_index = row
        if 0 <= row < len(self.prompts):
            p = self.prompts[row]
            self.title_input.setText(p.get("title", ""))
            self.content_input.setText(p.get("content", ""))

    def on_add(self):
        new_p = {
            "id": str(uuid.uuid4())[:8],
            "title": "新建提示词",
            "content": "请根据以下材料提炼知识点：\n\n【材料】：\n"
        }
        self.prompts.append(new_p)
        self.save_to_config()
        self.load_prompts()
        self.list_widget.setCurrentRow(len(self.prompts) - 1)

    def on_delete(self):
        if 0 <= self.current_index < len(self.prompts):
            del self.prompts[self.current_index]
            self.save_to_config()
            self.load_prompts()

    def on_save_current(self):
        if 0 <= self.current_index < len(self.prompts):
            self.prompts[self.current_index]["title"] = self.title_input.text().strip()
            self.prompts[self.current_index]["content"] = self.content_input.toPlainText()
            self.save_to_config()
            self.load_prompts()
            QMessageBox.information(self, "提示", "提示词已保存！")

    def save_to_config(self):
        self.config["prompts"] = self.prompts
        mw.addonManager.writeConfig(__name__, self.config)