import sqlite3

DB_NAME = "refactored_deployments.db"

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
            type TEXT,
            application TEXT,
            tenancy TEXT,
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
