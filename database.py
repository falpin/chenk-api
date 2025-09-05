import json
import sqlite3
import os
import config
from pathlib import Path

DB_PATH = config.DB_PATH

db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

def SQL_request(query, params=(), fetch='one', jsonify_result=False):
    print(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)

            if fetch == 'all':
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [
                    {
                        col: json.loads(row[i]) if isinstance(row[i], str) and row[i].startswith('{') else row[i]
                        for i, col in enumerate(columns)
                    }
                    for row in rows
                ]

            elif fetch == 'one':
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = {
                        col: json.loads(row[i]) if isinstance(row[i], str) and row[i].startswith('{') else row[i]
                        for i, col in enumerate(columns)
                    }
                else:
                    result = None
            else:
                conn.commit()
                result = None

        except sqlite3.Error as e:
            print(f"Ошибка SQL: {e}")
            raise

    if jsonify_result and result is not None:
        return json.dumps(result, ensure_ascii=False, indent=2)
    return result

SQL_request("""CREATE TABLE IF NOT EXISTS api_keys (
    key TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")