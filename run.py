import sys
import os
import json

# src ディレクトリを sys.path に追加
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

print(sys.path)

from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.data.data_manager import DataManager

def load_test_data(data_manager):
    """テストデータをデータベースに追加する。"""
    # JSON ファイルからデータを読み込む (例)
    if data_manager.get_all_workers(): # 変更
        print("Data already exists. Skipping test data loading.")
        return

    try:
        with open("test_data.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)

        for worker_data in test_data:
            data_manager.add_worker(
                worker_data["name"],
                worker_data["skill_levels"]
            )
    except FileNotFoundError:
        print("Error: test_data.json not found. Loading hardcoded test data...")
        # JSONファイルが存在しない場合、ハードコードされたテストデータを追加
        data_manager.add_worker("真田", [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        data_manager.add_worker("梶川", [4, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4])
        data_manager.add_worker("千葉", [3, 2, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3])
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in test_data.json. Loading hardcoded test data...")
        # JSONの形式が不正な場合、ハードコードされたテストデータを追加
        data_manager.add_worker("真田", [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        data_manager.add_worker("梶川", [4, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4])
        data_manager.add_worker("千葉", [3, 2, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3])
    except Exception as e:
        print(f"Error loading test data: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data_manager = DataManager()  # DataManager のインスタンスを作成 (データベース接続もここで行う)

    load_test_data(data_manager)  # テストデータの追加

    main_win = MainWindow(data_manager)  # DataManager のインスタンスを渡す
    main_win.show()
    sys.exit(app.exec())