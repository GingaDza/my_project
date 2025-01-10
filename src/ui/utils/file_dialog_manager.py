from PyQt6.QtWidgets import QFileDialog

class FileDialogManager:
    """ファイルダイアログを管理するクラス。"""

    def get_save_filepath(self, parent, title, directory, filter):
        """保存ダイアログを表示し、選択されたファイルパスを返す。"""
        filepath, _ = QFileDialog.getSaveFileName(parent, title, directory, filter)
        return filepath

    def get_open_filepath(self, parent, title, directory, filter):
        """開くダイアログを表示し、選択されたファイルパスを返す。"""
        filepath, _ = QFileDialog.getOpenFileName(parent, title, directory, filter)
        return filepath