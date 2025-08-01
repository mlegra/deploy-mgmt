import sqlite3

DB_NAME = "deployments.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Drop existing tables (in reverse dependency order)
    c.execute("DROP TABLE IF EXISTS deployments")
    c.execute("DROP TABLE IF EXISTS features")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS clients")

    # Create clients
    c.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Create products linked to clients
    c.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(name, client_id),
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)

    # Create features linked to products
    c.execute("""
        CREATE TABLE features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            repositorio TEXT,
            tenancy TEXT,
            master TEXT,
            UNIQUE(name, product_id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # Create deployments linked to features
    c.execute("""
        CREATE TABLE deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id INTEGER NOT NULL,
            ambiente TEXT,
            estado TEXT,
            fecha TEXT,
            release_manager TEXT,
            UNIQUE(feature_id, ambiente),
            FOREIGN KEY(feature_id) REFERENCES features(id)
        )
    """)

    c.execute("DROP TABLE IF EXISTS product_environments")

    c.execute("""
        CREATE TABLE product_environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(product_id, name),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)


    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# === CLIENTS ===
def get_or_create_client(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clients WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        client_id = row["id"]
    else:
        cursor.execute("INSERT INTO clients (name) VALUES (?)", (name,))
        client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return client_id

def get_all_clients():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM clients ORDER BY name")
    clients = cursor.fetchall()
    conn.close()
    return clients

# === PRODUCTS ===
def get_or_create_product(client_id, product_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE name = ? AND client_id = ?", (product_name, client_id))
    row = cursor.fetchone()
    if row:
        product_id = row["id"]
    else:
        cursor.execute("INSERT INTO products (name, client_id) VALUES (?, ?)", (product_name, client_id))
        product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def get_products_by_client(client_id):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM products WHERE client_id = ?", (client_id,))
    products = cursor.fetchall()
    conn.close()
    return products

# === FEATURES ===
def add_or_get_feature(product_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM features WHERE name = ? AND product_id = ?", (data["name"], product_id))
    row = cursor.fetchone()
    if row:
        feature_id = row["id"]
    else:
        cursor.execute("""
            INSERT INTO features (product_id, name, repositorio, tenancy, master)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, data["name"], data["repositorio"], data["tenancy"], data["master"]))
        feature_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feature_id

def get_features_by_product(product_id):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM features WHERE product_id = ?", (product_id,))
    features = cursor.fetchall()
    conn.close()
    return features

# === DEPLOYMENTS ===
def save_deployment(feature_id, deployment_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    """, (feature_id, deployment_data["ambiente"], deployment_data["estado"],
          deployment_data["fecha"], deployment_data["release_manager"]))
    conn.commit()
    conn.close()

def get_deployments_by_feature(feature_id):
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT * FROM deployments
        WHERE feature_id = ?
        ORDER BY ambiente
    """, (feature_id,))
    deployments = cursor.fetchall()
    conn.close()
    return deployments

def get_all_deployments_by_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.name as feature_name, d.*
        FROM features f
        LEFT JOIN deployments d ON f.id = d.feature_id
        WHERE f.product_id = ?
    """, (product_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_full_deployment(feature_id, ambiente, estado, fecha, release_manager):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
        VALUES (?, ?, ?, ?, ?)
    """, (feature_id, ambiente, estado, fecha, release_manager))
    conn.commit()
    conn.close()

# === PRODUCT ENVIRONMENTS ===
def add_environment_to_product(product_id, env_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO product_environments (product_id, name)
        VALUES (?, ?)
    """, (product_id, env_name))
    conn.commit()
    conn.close()

def get_environments_by_product(product_id):
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT name FROM product_environments
        WHERE product_id = ?
        ORDER BY id
    """, (product_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

