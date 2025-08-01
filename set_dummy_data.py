import random
from datetime import date
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

# Reinicia base eliminando todas las tablas
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

# Inicializar base
reset_db()
create_db()

# Datos base
clientes = {
    "Cliente ACME": ["Facturacion", "Logistica"],
    "TechSoft": ["PortalClientes", "Monitoreo"]
}
ambientes = ["DEV", "UAT", "PPD", "PRD"]
repositorio = "Repo1"
release_manager = "Elizabet RC"
hoy = date.today().isoformat()

# Generar jerarquía y features
for cliente, soluciones in clientes.items():
    client_id = get_or_create_client(cliente)
    for solucion in soluciones:
        solution_id = get_or_create_solution(client_id, solucion)
        for i in range(random.randint(1, 3)):
            producto = f"{solucion}-Prod{i+1}"
            product_id = get_or_create_product(solution_id, producto)

            # Ambientes
            for env in ambientes:
                get_or_create_environment(product_id, env)

            # Feature única
            feat_data = {
                "name": f"{solucion}-Feature{i+1}",
                "repositorio": repositorio,
                "master": "deploy.sql"
            }
            feat_id = add_or_get_feature(product_id, feat_data)

            for env in ambientes:
                save_deployment(feat_id, {
                    "ambiente": env,
                    "estado": random.choice(["Valid", "Failed"]),
                    "fecha": hoy,
                    "release_manager": release_manager
                })

print("✅ Base reiniciada y datos dummy cargados.")
