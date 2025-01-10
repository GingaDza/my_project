import sqlite3
from src.data.db_utils import (
    create_table_if_not_exists,
    get_all_workers_from_db,
    insert_worker_into_db,
    get_worker_from_db_by_name,
    update_worker_in_db,
    delete_worker_from_db
)
import threading


class DataManager:
    _lock = threading.Lock()  # スレッドロックを追加

    def __init__(self, db_path="app_data.db"):
        self.db_path = db_path
        # データベース接続テスト
        self.test_database_connection()

    def _connect_to_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 追加
            print("Database connection successful.")
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def test_database_connection(self):
        """データベース接続をテストする。"""
        print("--- DataManager: test_database_connection ---")
        conn = self._connect_to_db()
        if conn is None:
            print("  Database connection failed.")
            return

        try:
            workers = self.get_all_workers()
            print("--- DataManager: test_database_connection: raw data ---")
            workers_raw = get_all_workers_from_db(conn)
            for worker in workers_raw:
                print(f"  Worker: {worker}")
            for worker in workers:
                print(f"  Worker: {worker['name']}, Skills: {worker['skill_levels']}")
            print("--- DataManager: test_database_connection End ---")
        except sqlite3.Error as e:
           print(f"  Error accessing database: {e}")

    def get_all_workers(self):
       with self._connect_to_db() as conn:
        create_table_if_not_exists(conn)
        workers_raw = get_all_workers_from_db(conn)
        for worker in workers_raw:
            print("--- DataManager: get_all_workers: raw data ---")
            print(f"  Worker: {worker}")
        workers = get_all_workers_from_db(conn)
        for worker in workers:
          print("--- DataManager: get_all_workers: processed worker ---")
          print(f"  Worker: {worker['name']}, Skills: {worker['skill_levels']}")
        return workers

    def add_worker(self, name, skill_levels):
        with self._connect_to_db() as conn:
            with DataManager._lock:
                create_table_if_not_exists(conn)
                insert_worker_into_db(conn, name, skill_levels)

    def get_worker_by_name(self, name):
        with self._connect_to_db() as conn:
            create_table_if_not_exists(conn)
            worker = get_worker_from_db_by_name(conn, name)
            return worker

    def update_worker(self, old_name, new_name, skill_levels):
        with self._connect_to_db() as conn:
            with DataManager._lock:
                create_table_if_not_exists(conn)
                update_worker_in_db(conn, old_name, new_name, skill_levels)

    def delete_worker(self, name):
      with self._connect_to_db() as conn:
        with DataManager._lock:
          create_table_if_not_exists(conn)
          delete_worker_from_db(conn, name)
    
    def get_categories(self):
      # ここは仮の実装です。
      return [
        'アンローダー', 'エブリラベラー', 'オートラベラー', 'プッシャー', 'ウォータースパイダー', 'フィンガー',
        'ストー', 'バッファー', '下流管理',
        'ピック', '切り離し', 'TDR',
        'FC返送', 'リパック', '誘導'
          ]