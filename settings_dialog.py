from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSpinBox, QMessageBox, QComboBox
)
from aqt import mw
from .ai_service import AIService

# 预设各大服务商接口及推荐模型
PROVIDERS = {
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash", "deepseek-v4-pro"]
    },
    "通义千问 (Qwen)": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"]
    },
    "智谱清言 (GLM)": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-flash", "glm-4", "glm-4-plus"]
    },
    "Kimi (Moonshot)": {
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
    },
    "Ollama (本地)": {
        "base_url": "http://localhost:11434/v1",
        "models": ["qwen2.5:7b", "llama3.1:8b", "mistral:latest"]
    },
    "自定义": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o"]
    }
}

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 接口配置")
        self.setFixedWidth(500)
        self.config = mw.addonManager.getConfig(__name__) or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. 服务商选择
        layout.addWidget(QLabel("<b>模型提供商 (Provider):</b>"))
        self.provider_combo = QComboBox()
        for p in PROVIDERS.keys():
            self.provider_combo.addItem(p)
        current_p = self.config.get("provider", "DeepSeek")
        if current_p in PROVIDERS:
            self.provider_combo.setCurrentText(current_p)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        layout.addWidget(self.provider_combo)

        # 2. Base URL
        layout.addWidget(QLabel("<b>接口地址 (Base URL):</b>"))
        self.url_input = QLineEdit(self.config.get("api_base", "https://api.deepseek.com"))
        layout.addWidget(self.url_input)

        # 3. API Key
        layout.addWidget(QLabel("<b>API 密钥 (API Key):</b>"))
        self.key_input = QLineEdit(self.config.get("api_key", ""))
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("本地 Ollama 可不填")
        layout.addWidget(self.key_input)

        # 4. Model (可下拉也可手动输入)
        layout.addWidget(QLabel("<b>模型名称 (Model):</b>"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        layout.addWidget(self.model_combo)
        self.refresh_model_options(self.provider_combo.currentText(), self.config.get("model", ""))

        # 5. Timeout
        h_box = QHBoxLayout()
        h_box.addWidget(QLabel("请求超时时间(秒):"))
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 600)
        self.timeout_input.setValue(self.config.get("timeout", 60))
        h_box.addWidget(self.timeout_input)
        h_box.addStretch()
        layout.addLayout(h_box)

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("🔍 测试连通性")
        self.test_btn.clicked.connect(self.on_test)
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px 14px;")
        self.save_btn.clicked.connect(self.on_save)
        
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def refresh_model_options(self, provider_name: str, current_model: str = ""):
        self.model_combo.clear()
        models = PROVIDERS.get(provider_name, {}).get("models", [])
        for m in models:
            self.model_combo.addItem(m)
        if current_model:
            self.model_combo.setCurrentText(current_model)
        elif models:
            self.model_combo.setCurrentText(models[0])

    def on_provider_changed(self, provider_name: str):
        if provider_name in PROVIDERS and provider_name != "自定义":
            p_data = PROVIDERS[provider_name]
            self.url_input.setText(p_data["base_url"])
            self.refresh_model_options(provider_name)

    def on_test(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.repaint()
        
        ok, msg = AIService.test_connection(
            self.url_input.text().strip(),
            self.key_input.text().strip(),
            self.model_combo.currentText().strip(),
            self.timeout_input.value()
        )
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 测试连通性")
        
        if ok:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "连接失败", msg)

    def on_save(self):
        new_config = {
            **self.config,
            "provider": self.provider_combo.currentText(),
            "api_base": self.url_input.text().strip(),
            "api_key": self.key_input.text().strip(),
            "model": self.model_combo.currentText().strip(),
            "timeout": self.timeout_input.value()
        }
        mw.addonManager.writeConfig(__name__, new_config)
        QMessageBox.information(self, "提示", "配置已保存！")
        self.accept()