from aqt import mw, gui_hooks
from aqt.qt import QAction, qconnect
from .main_dialog import AICardDialog

dialog_instance = None

def show_main_dialog():
    global dialog_instance
    if dialog_instance is None:
        dialog_instance = AICardDialog(mw)
    dialog_instance.show()
    dialog_instance.raise_()
    dialog_instance.activateWindow()

def setup_menu():
    action = QAction("AI 生成卡片 (AICard)", mw)
    action.setShortcut("Ctrl+Shift+A")
    qconnect(action.triggered, show_main_dialog)
    # 添加到主窗口 工具(Tools) 菜单下
    mw.form.menuTools.addAction(action)

gui_hooks.main_window_did_init.append(setup_menu)