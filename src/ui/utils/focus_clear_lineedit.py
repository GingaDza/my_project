from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import QHBoxLayout, QComboBox # この行を追加

class FocusClearLineEdit(QLineEdit):
    """フォーカスイン時にテキストをクリアするカスタムQLineEdit。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainWindow = parent
        self.reset_triggered = False
        self.skip_on_text_changed = False  # 追加

        # textChanged シグナルにスロットを接続
        self.textChanged.connect(self.onTextChanged)

    def focusInEvent(self, event: QFocusEvent):
        """フォーカスインイベントをオーバーライドして、特定の条件でテキストをクリアする。"""
        print("--- FocusClearLineEdit: focusInEvent ---")
        print(f"  self.reset_triggered: {self.reset_triggered}")
        print(f"  self.mainWindow.selected_worker: {self.mainWindow.selected_worker}")
        print(f"  self.text(): {self.text()}")

        super().focusInEvent(event)

        # リセットがトリガーされていたら、何もしない
        if self.reset_triggered:
            print("--- FocusClearLineEdit: focusInEvent End (reset_triggered) ---\n")
            return

        # 既存のワーカーが選択されている場合、何もしない
        if self.mainWindow.selected_worker is not None:
            print("--- FocusClearLineEdit: focusInEvent End (existing worker selected) ---\n")
            return
       
        if self.text() == "":
             self.skip_on_text_changed = True
             self.mainWindow.selected_worker = None
             for tab_index in range(self.mainWindow.tab_widget.count()):
                 current_tab_widget = self.mainWindow.tab_widget.widget(tab_index)
                 for child_layout_index in range(current_tab_widget.layout().count()):
                   item = current_tab_widget.layout().itemAt(child_layout_index)
                   if item:
                       if isinstance(item.layout(),QHBoxLayout):
                         child_layout = item.layout()
                         for inner_index in range(child_layout.count()):
                             widget = child_layout.itemAt(inner_index).widget()
                             if isinstance(widget, QComboBox):
                                widget.setCurrentIndex(0)
             print("  Entering new worker mode (empty input field)")
             self.reset_triggered = True
             self.skip_on_text_changed = False

        print("--- FocusClearLineEdit: focusInEvent End ---\n")

    def focusOutEvent(self, event: QFocusEvent):
        """フォーカスアウトイベントをオーバーライドして、reset_triggered フラグをリセットする。"""
        print("--- FocusClearLineEdit: focusOutEvent ---")
        print(f"  self.reset_triggered: {self.reset_triggered}")
        super().focusOutEvent(event)
        print("--- FocusClearLineEdit: focusOutEvent End ---\n")

    def onTextChanged(self):
        """テキストが変更されたときに呼び出され、リセット機能を無効化し、未保存状態にする。"""
        print("--- FocusClearLineEdit: onTextChanged ---")
        print(f"  self.reset_triggered: {self.reset_triggered}")
        print(f"  self.text(): {self.text()}")

        if self.skip_on_text_changed: # 追加
           print("  Text change ignored due to skip_on_text_changed flag.")
           return

        if self.text() != "" and not self.reset_triggered:
            self.reset_triggered = True
        self.mainWindow.unsaved_changes = True
        print("--- FocusClearLineEdit: onTextChanged End ---\n")