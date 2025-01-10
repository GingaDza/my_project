import sqlite3
import json

DB_NAME = "workers.db"

def init_db():
    """データベースを初期化し、テーブルを作成する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            categories TEXT,
            skill_levels TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_worker_to_db(name, skill_levels):
    """ワーカーをデータベースに追加する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 変更: skill_levels をJSON文字列として保存
        skill_levels_json = json.dumps(skill_levels)
        cursor.execute("INSERT INTO workers (name, categories,skill_levels) VALUES (?, ?, ?)", (name, json.dumps([]), skill_levels_json))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Error: Worker with name '{name}' already exists.")
    finally:
        conn.close()

def get_all_workers_from_db():
    """すべてのワーカーをデータベースから取得する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    rows = cursor.fetchall()
    conn.close()
    workers = []
    for row in rows:
        worker = {
            "id": row[0],
            "name": row[1],
             "categories": json.loads(row[2]), #JSON文字列からリストに変換
            # 変更: skill_levels を整数のリストに変換
            "skill_levels": json.loads(row[3]) # JSON文字列からリストに変換
        }
        workers.append(worker)
    return workers

def get_worker_by_name_from_db(name):
    """名前でワーカーをデータベースから取得する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers WHERE name=?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
              "categories": json.loads(row[2]), # JSON文字列からリストに変換
            # 変更: skill_levels を整数のリストに変換
            "skill_levels": json.loads(row[3]) # JSON文字列からリストに変換
        }
    return None

def update_worker_in_db(old_name, new_name, skill_levels):
    """ワーカーの情報をデータベースで更新する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 変更: skill_levels をJSON文字列として保存
        skill_levels_json = json.dumps(skill_levels)
        cursor.execute("UPDATE workers SET name=?, categories=?, skill_levels=? WHERE name=?", (new_name, json.dumps([]),skill_levels_json, old_name))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Error: Worker with name '{new_name}' already exists.")
    finally:
        conn.close()

def delete_worker_from_db(name):
    """ワーカーをデータベースから削除する。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workers WHERE name=?", (name,))
    conn.commit()
    conn.close()