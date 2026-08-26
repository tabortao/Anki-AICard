from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSpinBox, QMessageBox, Qt
)
from aqt import mw
from .ai_service import AIService

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 接口配置")
        self.setFixedWidth(460)
        self.config = mw.addonManager.getConfig(__name__) or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Base URL
        layout.addWidget(QLabel("接口地址 (Base URL):"))
        self.url_input = QLineEdit(self.config.get("api_base", "https://api.openai.com/v1"))
        layout.addWidget(self.url_input)

        # API Key
        layout.addWidget(QLabel("API 密钥 (API Key):"))
        self.key_input = QLineEdit(self.config.get("api_key", ""))
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)

        # Model
        layout.addWidget(QLabel("模型名称 (Model):"))
        self.model_input = QLineEdit(self.config.get("model", "gpt-4o-mini"))
        layout.addWidget(self.model_input)

        # Timeout
        h_box = QHBoxLayout()
        h_box.addWidget(QLabel("超时时间(秒):"))
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 300)
        self.timeout_input.setValue(self.config.get("timeout", 60))
        h_box.addWidget(self.timeout_input)
        h_box.addStretch()
        layout.addLayout(h_box)

        # Buttons
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试连通性")
        self.test_btn.clicked.connect(self.on_test)
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def on_test(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.repaint()
        
        ok, msg = AIService.test_connection(
            self.url_input.text().strip(),
            self.key_input.text().strip(),
            self.model_input.text().strip(),
            self.timeout_input.value()
        )
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连通性")
        
        if ok:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "连接失败", msg)

    def on_save(self):
        new_config = {
            "api_base": self.url_input.text().strip(),
            "api_key": self.key_input.text().strip(),
            "model": self.model_input.text().strip(),
            "timeout": self.timeout_input.value()
        }
        mw.addonManager.writeConfig(__name__, new_config)
        QMessageBox.information(self, "提示", "配置已保存！")
        self.accept()