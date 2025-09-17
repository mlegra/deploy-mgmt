import sqlite3
import hashlib

DB_NAME = "deployments.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solution_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (solution_id) REFERENCES solutions(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS features_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            repositorio TEXT,
            master TEXT,
            UNIQUE(name, repositorio),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            repositorio TEXT,
            type TEXT,
            application TEXT,
            tenancy TEXT,
            master TEXT,
            product_id INTEGER,
            UNIQUE(name, repositorio),
            FOREIGN KEY (product_id) REFERENCES products(id)
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
    # Tabla de usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- 'admin', 'release_manager', 'viewer'
        )
    ''')
    conn.commit()
    conn.close()

def migrate_features_to_normalized():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM features')
    old_rows = c.fetchall()

    for row in old_rows:
        tenancy = row['tenancy']
        application = row['application']
        tipo = row['type']

        # Tenant
        c.execute('SELECT id FROM tenants WHERE name = ?', (tenancy,))
        tenant = c.fetchone()
        tenant_id = tenant['id'] if tenant else c.execute('INSERT INTO tenants (name) VALUES (?)', (tenancy,)).lastrowid

        # Solution
        c.execute('SELECT id FROM solutions WHERE name = ? AND tenant_id = ?', (application, tenant_id))
        solution = c.fetchone()
        solution_id = solution['id'] if solution else c.execute('INSERT INTO solutions (name, tenant_id) VALUES (?, ?)', (application, tenant_id)).lastrowid

        # Product
        c.execute('SELECT id FROM products WHERE name = ? AND solution_id = ?', (tipo, solution_id))
        product = c.fetchone()
        product_id = product['id'] if product else c.execute('INSERT INTO products (name, solution_id) VALUES (?, ?)', (tipo, solution_id)).lastrowid

        # Insert into new features
        c.execute('''
            INSERT OR IGNORE INTO features_new (name, repositorio, master, product_id)
            VALUES (?, ?, ?, ?)
        ''', (row['name'], row['repositorio'], row['master'], product_id))

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
            INSERT INTO features (name, repositorio, product_id, master)
            VALUES (?, ?, ?, ?)
        ''', (data["name"], data["repositorio"], data["product_id"], data["master"]))
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
        SELECT 
            f.id AS feature_id,
            f.name,
            f.repositorio,
            f.master,
            p.name AS type,
            s.name AS application,
            t.name AS tenancy,
            d.ambiente,
            d.estado,
            d.fecha,
            d.release_manager
        FROM features f
        JOIN products p ON f.product_id = p.id
        JOIN solutions s ON p.solution_id = s.id
        JOIN tenants t ON s.tenant_id = t.id
        LEFT JOIN deployments d ON f.id = d.feature_id
    '''
    params = []
    if filtro:
        query += '''
            WHERE f.name LIKE ? 
               OR f.repositorio LIKE ? 
               OR d.estado LIKE ?
               OR p.name LIKE ? 
               OR s.name LIKE ?
               OR t.name LIKE ?
        '''
        pattern = f"%{filtro}%"
        params = [pattern] * 6

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

# --- USUARIOS Y AUTENTICACIÓN ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
              (username, hash_password(password), role))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, role FROM users ORDER BY username')
    users = c.fetchall()
    conn.close()
    return users

def update_user_role(user_id, new_role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()