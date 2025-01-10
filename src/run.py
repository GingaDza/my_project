import sys
import os
import sqlite3

sys.path.append(os.path.abspath('.'))

from src.data import data_manager
from . import main_window

def main():
    """メインの処理を行う。"""
    print("--- run.py: test_database_connection ---")
    dm = data_manager.DataManager()
    workers = dm.get_all_workers()
    if workers:
       for worker in workers:
           print(f"  Worker: {worker['name']}, Skills: {worker['skill_levels']}")
    print("--- run.py: test_database_connection End ---")

    window = main_window.MainWindow(dm)
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    main()