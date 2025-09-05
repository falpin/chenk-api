import json
import sqlite3

def SQL_request(query, params=(), fetch='one', jsonify_result=False):
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