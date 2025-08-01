import random
from model import (
    create_db,
    get_db_connection,
    get_or_create_client,
    get_or_create_solution,
    get_or_create_product,
    get_or_create_environment,
    add_or_get_feature,
    save_deployment
)

# 🔁 Reset DB: drop all tables
def reset_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS deployments;
        DROP TABLE IF EXISTS environments;
        DROP TABLE IF EXISTS features;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS solutions;
        DROP TABLE IF EXISTS clients;
    """)
    conn.commit()
    conn.close()

# ▶️ Ejecutar reinicio y creación
reset_db()
create_db()

# 📦 Datos dummy
clientes = {
    "Cliente ACME": ["Facturación", "Logística"],
    "TechSoft": ["Portal Clientes", "Monitoreo"]
}

ambientes = ["DEV", "UAT", "PPD", "PRD"]
repositorio = "Repo1"
release_manager = "Elizabet RC"
app = "AppX"
script = "deploy.sql"

# 🧠 Generar jerarquía y datos
for cliente, soluciones in clientes.items():
    client_id = get_or_create_client(cliente)
    for solucion in soluciones:
        solution_id = get_or_create_solution(client_id, solucion)
        for i in range(random.randint(1, 3)):
            prod_name = f"{solucion}-Prod{i+1}"
            product_id = get_or_create_product(solution_id, prod_name)

            for env in ambientes:
                get_or_create_environment(product_id, env)

            # Agregar una feature
            feat_name = f"{solucion}-Feature{i+1}"
            feat_data = {
                "name": feat_name,
                "repositorio": repositorio,
                "type": "feature",
                "application": app,
                "tenancy": cliente,
                "master": script
            }
            feat_id = add_or_get_feature(product_id, feat_data)

            for env in ambientes:
                save_deployment(feat_id, {
                    "ambiente": env,
                    "estado": random.choice(["Valid", "Failed"]),
                    "fecha": "2025-08-01",
                    "release_manager": release_manager
                })

print("✅ Datos dummy generados con éxito.")
