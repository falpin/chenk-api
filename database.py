from FlaskAPIServer.utils.database import SQL_request

ROLES = {"user":10, "admin":20}

SQL_request("""CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name VARCHAR(255) NOT NULL,
    link TEXT,
    complex_name TEXT,
    course INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);""")

def create_group(group):
    SQL_request(f"""CREATE TABLE IF NOT EXISTS {group} (
        week_id INTEGER,
        timetable JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        time_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    );""")

def delete_group(group):
    SQL_request(f"""DROP TABLE IF EXISTS {group};""")    

SQL_request("UPDATE key_roles SET priority=? WHERE name=?;", (50, "api_key"), None)


existing_roles = SQL_request(query="SELECT name FROM key_roles;", fetch='all')
existing_names = [role['name'] for role in existing_roles] if existing_roles else []
roles_to_insert = [(name, priority) for name, priority in ROLES.items() if name not in existing_names]

if roles_to_insert:
    for name, priority in roles_to_insert:
        SQL_request(query="INSERT INTO key_roles (name, priority) VALUES (?, ?);", params=(name, priority), fetch=None)