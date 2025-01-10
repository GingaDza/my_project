# src/data/data_manager.py
from .db_utils import (
    add_worker_to_db,
    get_all_workers_from_db,
    get_worker_by_name_from_db,
    update_worker_in_db,
    delete_worker_from_db,
)

class DataManager:
    """データのCRUD操作を管理するクラス。"""
    def __init__(self):
        pass

    def add_worker(self, name, skill_levels):
        """ワーカーをデータベースに追加する。"""
        add_worker_to_db(name, skill_levels)

    def get_all_workers(self):
        """すべてのワーカーをデータベースから取得する。"""
        return get_all_workers_from_db()

    def get_worker_by_name(self, name):
        """名前でワーカーをデータベースから取得する。"""
        return get_worker_by_name_from_db(name)

    def update_worker(self, old_name, new_name, skill_levels):
        """ワーカーの情報をデータベースで更新する。"""
        update_worker_in_db(old_name, new_name, skill_levels)

    def delete_worker(self, name):
        """ワーカーをデータベースから削除する。"""
        delete_worker_from_db(name)