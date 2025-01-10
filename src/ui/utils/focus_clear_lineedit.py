from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt

class FocusClearLineEdit(QLineEdit):
  focus_in = pyqtSignal()
  def __init__(self, parent=None):
    super().__init__(parent)
    self.reset_triggered = False
    self.mainWindow = parent
    self.textChanged.connect(self.onTextChanged)

  @pyqtSlot()
  def focusInEvent(self, event):
    """フォーカスイン時の処理。"""
    self.focus_in.emit()
    print("--- FocusClearLineEdit: focusInEvent ---")
    print("  self.reset_triggered:", self.reset_triggered)
    if self.mainWindow.selected_worker:
        print("  self.mainWindow.selected_worker:", self.mainWindow.selected_worker)
    print("  self.text():", self.text())
    if self.reset_triggered == False:
        if self.mainWindow.selected_worker == None:
           print("  Entering new worker mode (empty input field)")
        return
    self.setFocus()
    print("--- FocusClearLineEdit: focusInEvent End (reset_triggered) ---")
    self.reset_triggered = False
    super().focusInEvent(event)

  @pyqtSlot()
  def focusOutEvent(self, event):
     """フォーカスアウト時の処理。"""
     print("--- FocusClearLineEdit: focusOutEvent ---")
     print("  self.reset_triggered:", self.reset_triggered)
     self.reset_triggered = True
     print("--- FocusClearLineEdit: focusOutEvent End ---")
     super().focusOutEvent(event)

  @pyqtSlot()
  def onTextChanged(self):
    """テキストが変更された時の処理。"""
    print("--- FocusClearLineEdit: onTextChanged ---")
    print("  self.reset_triggered:", self.reset_triggered)
    print("  self.text():", self.text())
    super().textChanged.emit(self.text())
    print("--- FocusClearLineEdit: onTextChanged End ---")