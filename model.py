import sqlite3

DB_NAME = "deployments.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(client_id, name),
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solution_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(solution_id, name),
            FOREIGN KEY(solution_id) REFERENCES solutions(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(product_id, name),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            repositorio TEXT,
            master TEXT,
            UNIQUE(product_id, name, repositorio),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id INTEGER NOT NULL,
            environment_id INTEGER NOT NULL,
            estado TEXT,
            fecha TEXT,
            release_manager TEXT,
            UNIQUE(feature_id, environment_id),
            FOREIGN KEY(feature_id) REFERENCES features(id),
            FOREIGN KEY(environment_id) REFERENCES environments(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_client(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        client_id = row["id"]
    else:
        cur.execute("INSERT INTO clients (name) VALUES (?)", (name,))
        client_id = cur.lastrowid
    conn.commit()
    conn.close()
    return client_id

def get_all_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY name")
    clients = cur.fetchall()
    conn.close()
    return clients

def get_or_create_solution(client_id, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM solutions WHERE client_id = ? AND name = ?", (client_id, name))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO solutions (client_id, name) VALUES (?, ?)", (client_id, name))
    solution_id = cur.lastrowid
    conn.commit()
    conn.close()
    return solution_id

def get_solutions_by_client(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM solutions WHERE client_id = ? ORDER BY name", (client_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_or_create_product(solution_id, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE solution_id = ? AND name = ?", (solution_id, name))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO products (solution_id, name) VALUES (?, ?)", (solution_id, name))
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id

def get_products_by_solution(solution_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE solution_id = ? ORDER BY name", (solution_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_environments_by_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM environments WHERE product_id = ? ORDER BY name", (product_id,))
    envs = [row["name"] for row in cur.fetchall()]
    conn.close()
    return envs

def get_or_create_environment(product_id, name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM environments WHERE product_id = ? AND name = ?", (product_id, name))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("INSERT INTO environments (product_id, name) VALUES (?, ?)", (product_id, name))
    env_id = cur.lastrowid
    conn.commit()
    conn.close()
    return env_id

def add_or_get_feature(product_id, data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id FROM features WHERE product_id = ? AND name = ? AND repositorio = ?
    ''', (product_id, data["name"], data["repositorio"]))
    row = cur.fetchone()
    if row:
        feature_id = row["id"]
    else:
        cur.execute('''
            INSERT INTO features (product_id, name, repositorio, master)
            VALUES (?, ?, ?, ?)
        ''', (product_id, data["name"], data["repositorio"], data["master"]))
        feature_id = cur.lastrowid
    conn.commit()
    conn.close()
    return feature_id

def get_features_by_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM features WHERE product_id = ? ORDER BY name", (product_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_deployment(feature_id, data):
    conn = get_db_connection()
    cur = conn.cursor()
    product_id = get_product_id_by_feature(feature_id)
    env_id = get_or_create_environment(product_id, data["ambiente"])
    cur.execute('''
        INSERT OR REPLACE INTO deployments (feature_id, environment_id, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    ''', (feature_id, env_id, data["estado"], data["fecha"], data["release_manager"]))
    conn.commit()
    conn.close()

def update_full_deployment(feature_id, ambiente, estado, fecha, release_manager):
    conn = get_db_connection()
    cur = conn.cursor()
    product_id = get_product_id_by_feature(feature_id)
    env_id = get_or_create_environment(product_id, ambiente)
    cur.execute('''
        INSERT OR REPLACE INTO deployments (feature_id, environment_id, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    ''', (feature_id, env_id, estado, fecha, release_manager))
    conn.commit()
    conn.close()

def get_all_deployments_by_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT f.id as feature_id, f.name as feature_name, f.repositorio, f.master,
               e.name as ambiente, d.estado, d.fecha, d.release_manager
        FROM features f
        LEFT JOIN deployments d ON f.id = d.feature_id
        LEFT JOIN environments e ON d.environment_id = e.id
        WHERE f.product_id = ?
        ORDER BY f.name, e.name
    ''', (product_id,))
    rows = cur.fetchall()
    conn.close()

    grouped = {}
    for row in rows:
        name = row["feature_name"]
        if name not in grouped:
            grouped[name] = {
                "repositorio": row["repositorio"],
                "master": row["master"],
                "env_status": {}
            }
        if row["ambiente"]:
            grouped[name]["env_status"][row["ambiente"]] = row["estado"]
    return grouped

def get_product_id_by_feature(feature_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_id FROM features WHERE id = ?", (feature_id,))
    row = cur.fetchone()
    conn.close()
    return row["product_id"] if row else None