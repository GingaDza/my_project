import sqlite3

def create_table_if_not_exists(conn: sqlite3.Connection):
    """ワーカーテーブルが存在しない場合に作成する。"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            skill_levels TEXT
        )""")
    conn.commit()

def insert_worker_into_db(conn: sqlite3.Connection, name, skill_levels):
    """ワーカーをデータベースに挿入する。"""
    cursor = conn.cursor()
    skill_levels_str = ','.join(map(str, skill_levels))
    cursor.execute("INSERT INTO workers (name, skill_levels) VALUES (?, ?)", (name, skill_levels_str))
    conn.commit()


def get_all_workers_from_db(conn: sqlite3.Connection):
    """データベースからすべてのワーカーを取得する。"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    rows = cursor.fetchall()
    workers = []
    for row in rows:  # 修正箇所
        worker = dict(row)
        worker['skill_levels'] = [int(level) for level in worker['skill_levels'].replace("[", "").replace("]", "").split(',')] if worker['skill_levels'] else []
        workers.append(worker)
    return workers


def get_worker_from_db_by_name(conn: sqlite3.Connection, name):
    """名前でワーカーをデータベースから取得する。"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        worker = dict(row)
        worker['skill_levels'] = [int(level) for level in worker['skill_levels'].replace("[", "").replace("]", "").split(',')] if worker['skill_levels'] else []
        return worker
    return None


def update_worker_in_db(conn: sqlite3.Connection, old_name, new_name, skill_levels):
    """データベース内のワーカー情報を更新する。"""
    cursor = conn.cursor()
    skill_levels_str = ','.join(map(str, skill_levels))
    cursor.execute("UPDATE workers SET name=?, skill_levels=? WHERE name=?", (new_name, skill_levels_str, old_name))
    conn.commit()


def delete_worker_from_db(conn: sqlite3.Connection, name):
    """データベースからワーカーを削除する。"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workers WHERE name=?", (name,))
    conn.commit()