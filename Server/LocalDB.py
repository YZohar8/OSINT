import sqlite3
import json
import os
from datetime import datetime



def init_db():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print("BASE_DIR:", BASE_DIR)

    DATA_DIR = os.path.join(BASE_DIR, "data")
    print("DATA_DIR:", DATA_DIR)

    os.makedirs(DATA_DIR, exist_ok=True)

    DB_FILE = os.path.join(DATA_DIR, "scans.db")
    print("DB_FILE:", DB_FILE)



    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        scan_id TEXT PRIMARY KEY,
        domain TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        status TEXT NOT NULL,
        result TEXT
    )
    """)

    cursor.execute("DELETE FROM scans")
    conn.commit()
    conn.close()

def save_scan(scan_id, scan_data):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_FILE = os.path.join(DATA_DIR, "scans.db")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO scans (scan_id, domain, created_at, completed_at, status, result)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        scan_id,
        scan_data["domain"],
        scan_data["created_at"],
        scan_data.get("completed_at"),
        scan_data["status"],
        json.dumps(scan_data.get("result")),
    ))

    conn.commit()
    conn.close()

def update_scan(scan_id, updates):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_FILE = os.path.join(DATA_DIR, "scans.db")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return

    update_fields = []
    update_values = []

    if "status" in updates:
        update_fields.append("status = ?")
        update_values.append(updates["status"])

    if "completed_at" in updates:
        update_fields.append("completed_at = ?")
        update_values.append(updates["completed_at"])

    if "result" in updates:
        update_fields.append("result = ?")
        update_values.append(json.dumps(updates["result"]))

    update_values.append(scan_id)

    cursor.execute(f"""
    UPDATE scans SET {", ".join(update_fields)} WHERE scan_id = ?
    """, update_values)

    conn.commit()
    conn.close()

def get_scan(scan_id):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_FILE = os.path.join(DATA_DIR, "scans.db")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE scan_id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "scan_id": row[0],
        "domain": row[1],
        "created_at": row[2],
        "completed_at": row[3],
        "status": row[4],
        "result": json.loads(row[5]) if row[5] else None,
    }

def get_all_scans():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_FILE = os.path.join(DATA_DIR, "scans.db")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()


    result = [
        {
            "scan_id": row[0],
            "domain": row[1],
            "created_at": row[2],
            "completed_at": row[3],
            "status": row[4],
            "result": json.loads(row[5]) if row[5] else None,
        }
        for row in rows
    ]
    print(result)
    return result

