from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
from model import (
    create_db, get_or_create_client, get_all_clients,
    get_or_create_solution, get_solutions_by_client,
    get_or_create_product, get_products_by_solution,
    add_or_get_feature, get_features_by_product,
    save_deployment, get_all_deployments_by_product,
    update_full_deployment, get_environments_by_product
)

app = Flask(__name__)
create_db()

repos_options = ["Repo1", "Repo2"]
rm_options = ["Michel LF", "Elizabet RC", "Yasser F"]
today = date.today().isoformat()

@app.route("/", methods=["GET", "POST"])
def index():
    clients = get_all_clients()
    client_name = request.args.get("client") or request.form.get("client")
    solution_name = request.args.get("solution") or request.form.get("solution")
    product_name = request.args.get("product") or request.form.get("product")

    selected_client_id = get_or_create_client(client_name) if client_name else None
    selected_solution_id = get_or_create_solution(selected_client_id, solution_name) if selected_client_id and solution_name else None
    selected_product_id = get_or_create_product(selected_solution_id, product_name) if selected_solution_id and product_name else None

    solutions = get_solutions_by_client(selected_client_id) if selected_client_id else []
    products = get_products_by_solution(selected_solution_id) if selected_solution_id else []
    ambiente_options = get_environments_by_product(selected_product_id) if selected_product_id else []
    deployments = get_all_deployments_by_product(selected_product_id) if selected_product_id else {}

    if request.method == "POST" and selected_product_id:
        form = request.form

        feature_data = {
            "name": form.get("name"),
            "repositorio": form.get("repositorio"),
            "master": form.get("master")
        }
        try:
            feature_id = add_or_get_feature(selected_product_id, feature_data)
            deployment_data = {
                "ambiente": form.get("ambiente"),
                "estado": form.get("estado"),
                "fecha": form.get("fecha"),
                "release_manager": form.get("release_manager")
            }
            save_deployment(feature_id, deployment_data)
        except Exception as e:
            return f"Error al guardar el despliegue: {e}", 500

        return redirect(url_for("index", client=client_name, solution=solution_name, product=product_name))

    return render_template("index.html",
        clients=clients,
        selected_client=client_name,
        solutions=solutions,
        selected_solution=solution_name,
        products=products,
        selected_product=product_name,
        ambiente_options=ambiente_options,
        repos_options=repos_options,
        rm_options=rm_options,
        deployments=deployments,
        today=today
    )

@app.route("/get_solutions", methods=["POST"])
def get_solutions():
    data = request.get_json()
    client_id = get_or_create_client(data.get("client"))
    return jsonify([{"name": s["name"]} for s in get_solutions_by_client(client_id)])

@app.route("/get_products", methods=["POST"])
def get_products():
    data = request.get_json()
    client_id = get_or_create_client(data.get("client"))
    solution_id = get_or_create_solution(client_id, data.get("solution"))
    return jsonify([{"name": p["name"]} for p in get_products_by_solution(solution_id)])

@app.route("/get_environments", methods=["POST"])
def get_environments():
    data = request.get_json()
    client_id = get_or_create_client(data.get("client"))
    solution_id = get_or_create_solution(client_id, data.get("solution"))
    product_id = get_or_create_product(solution_id, data.get("product"))
    return jsonify(get_environments_by_product(product_id))

@app.route("/get_deployment_details", methods=["POST"])
def get_deployment_details():
    data = request.get_json()
    client_id = get_or_create_client(data["client"])
    solution_id = get_or_create_solution(client_id, data["solution"])
    product_id = get_or_create_product(solution_id, data["product"])

    features = get_features_by_product(product_id)
    for f in features:
        if f["name"] == data["feature"]:
            feature_id = f["id"]
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT d.estado, d.fecha, d.release_manager
                FROM deployments d
                JOIN environments e ON d.environment_id = e.id
                WHERE d.feature_id = ? AND e.name = ?
            """, (feature_id, data["ambiente"]))
            row = cur.fetchone()
            conn.close()
            if row:
                return jsonify({
                    "estado": row["estado"],
                    "fecha": row["fecha"],
                    "release_manager": row["release_manager"]
                })
            else:
                return jsonify({})
    return jsonify({}), 404

@app.route("/update_full_deployment", methods=["POST"])
def update_deployment():
    data = request.get_json()
    client_id = get_or_create_client(data["client"])
    solution_id = get_or_create_solution(client_id, data["solution"])
    product_id = get_or_create_product(solution_id, data["product"])
    features = get_features_by_product(product_id)
    for f in features:
        if f["name"] == data["feature"]:
            update_full_deployment(
                feature_id=f["id"],
                ambiente=data["ambiente"],
                estado=data["estado"],
                fecha=data["fecha"],
                release_manager=data["release_manager"]
            )
            return jsonify(success=True)
    return jsonify(success=False, message="Feature not found"), 400

if __name__ == '__main__':
    app.run(debug=True)