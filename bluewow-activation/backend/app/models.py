import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bluewow.sqlite3")

def get_conn():
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, action TEXT, detail TEXT)"
    )
    conn.commit()
    conn.close()

def write_log(action: str, detail: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log (ts, action, detail) VALUES (datetime('now'), ?, ?)", (action, detail))
    conn.commit()
    conn.close()
