import sqlite3

DB_NAME = "deployments.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            repositorio TEXT,
            type TEXT,
            application TEXT,
            tenancy TEXT,
            master TEXT,
            UNIQUE(name, repositorio)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id INTEGER NOT NULL,
            ambiente TEXT,
            estado TEXT,
            fecha TEXT,
            release_manager TEXT,
            UNIQUE(feature_id, ambiente),
            FOREIGN KEY(feature_id) REFERENCES features(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def add_or_get_feature(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM features WHERE name = ? AND repositorio = ?', (data["name"], data["repositorio"]))
    row = cursor.fetchone()
    if row:
        feature_id = row["id"]
    else:
        cursor.execute('''
            INSERT INTO features (name, repositorio, type, application, tenancy, master)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data["name"], data["repositorio"], data["type"], data["application"], data["tenancy"], data["master"]))
        feature_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feature_id

def save_deployment(feature_id, deployment_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    ''', (feature_id, deployment_data["ambiente"], deployment_data["estado"], deployment_data["fecha"], deployment_data["release_manager"]))
    conn.commit()
    conn.close()

def get_all_features(filtro=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT f.id as feature_id, f.name, f.repositorio, f.type, f.application, f.master,
               d.ambiente, d.estado, d.fecha, d.release_manager
        FROM features f
        LEFT JOIN deployments d ON f.id = d.feature_id
    '''
    params = []
    if filtro:
        query += ' WHERE f.name LIKE ? OR f.repositorio LIKE ? OR d.estado LIKE ?'
        pattern = f"%{filtro}%"
        params = [pattern, pattern, pattern]
    query += ' ORDER BY f.name, d.ambiente'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_env_status(feature_id, ambiente, estado):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
        VALUES (?, ?, ?, DATE('now'), '')
    ''', (feature_id, ambiente, estado))
    conn.commit()
    conn.close()

def update_full_deployment(feature_id, ambiente, estado, fecha, release_manager):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    ''', (feature_id, ambiente, estado, fecha, release_manager))
    conn.commit()
    conn.close()

def get_all_feature_names():
    conn = get_db_connection()
    cursor = conn.execute('SELECT DISTINCT name FROM features')
    names = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return names

def get_all_deployment_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.name, d.ambiente, d.estado, d.fecha, d.release_manager
        FROM features f
        LEFT JOIN deployments d ON f.id = d.feature_id
    ''')
    rows = cursor.fetchall()
    conn.close()

    deployments = {}
    for row in rows:
        name = row["name"]
        env = row["ambiente"]
        if name not in deployments:
            deployments[name] = {}
        if env:
            deployments[name][env] = {
                "estado": row["estado"],
                "fecha": row["fecha"],
                "release_manager": row["release_manager"]
            }
    return deployments
