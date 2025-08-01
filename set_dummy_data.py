from model import (
    create_db,
    get_or_create_client,
    get_or_create_solution,
    get_or_create_product,
    get_or_create_environment,
    add_or_get_feature,
    save_deployment
)

# 1. Inicializar base
create_db()

# 2. Datos jerárquicos
client_name = "Cliente ACME"
solution_name = "Gestión de Pedidos"
product_name = "Portal Web"
ambientes = ["DEV", "QA", "PROD"]
features = [
    {"name": "Login OAuth", "type": "feature"},
    {"name": "Checkout", "type": "feature"},
    {"name": "Notificaciones", "type": "bugfix"}
]
repositorio = "Repo1"
release_manager = "Michel LF"
application = "PedidoApp"
script = "deploy.sql"

# 3. Crear jerarquía
client_id = get_or_create_client(client_name)
solution_id = get_or_create_solution(client_id, solution_name)
product_id = get_or_create_product(solution_id, product_name)

# 4. Crear ambientes
for env in ambientes:
    get_or_create_environment(product_id, env)

# 5. Insertar features y despliegues
for feature in features:
    f_data = {
        "name": feature["name"],
        "repositorio": repositorio,
        "type": feature["type"],
        "application": application,
        "tenancy": client_name,
        "master": script
    }
    f_id = add_or_get_feature(product_id, f_data)

    for env in ambientes:
        save_deployment(f_id, {
            "ambiente": env,
            "estado": "Valid",
            "fecha": "2025-08-01",
            "release_manager": release_manager
        })

print("✅ Datos de prueba insertados correctamente.")
