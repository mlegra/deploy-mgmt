from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
from model import (
    create_db, get_or_create_client, get_all_clients,
    get_or_create_product, get_products_by_client,
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
    client_name = request.args.get("client")
    product_name = request.args.get("product")

    selected_client_id = get_or_create_client(client_name) if client_name else None
    selected_product_id = get_or_create_product(selected_client_id, product_name) if selected_client_id and product_name else None

    products = get_products_by_client(selected_client_id) if selected_client_id else []
    features = get_features_by_product(selected_product_id) if selected_product_id else []
    deployments = get_all_deployments_by_product(selected_product_id) if selected_product_id else []
    ambiente_options = get_environments_by_product(selected_product_id) if selected_product_id else []

    if request.method == "POST":
        form = request.form

        # Create or get feature
        feature_data = {
            "name": form["feature_name"],
            "repositorio": form["repositorio"],
            "master": form["master"]
        }
        feature_id = add_or_get_feature(selected_product_id, feature_data)

        # Create deployment
        deployment_data = {
            "ambiente": form["ambiente"],
            "estado": form["estado"],
            "fecha": form["fecha"],
            "release_manager": form["release_manager"]
        }
        save_deployment(feature_id, deployment_data)

        return redirect(url_for("index", client=client_name, product=product_name))

    return render_template("index.html",
        clients=clients,
        selected_client=client_name,
        products=products,
        selected_product=product_name,
        features=features,
        deployments=deployments,
        ambiente_options=ambiente_options,
        repos_options=repos_options,
        rm_options=rm_options,
        today=today
    )

@app.route("/get_products", methods=["POST"])
def get_products():
    data = request.get_json()
    client_name = data.get("client")
    client_id = get_or_create_client(client_name)
    products = get_products_by_client(client_id)
    return jsonify([{"name": p["name"]} for p in products])

@app.route("/get_features", methods=["POST"])
def get_features():
    data = request.get_json()
    client_name = data.get("client")
    product_name = data.get("product")

    client_id = get_or_create_client(client_name)
    product_id = get_or_create_product(client_id, product_name)
    features = get_features_by_product(product_id)
    return jsonify([{"name": f["name"]} for f in features])

@app.route("/get_environments", methods=["POST"])
def get_environments():
    data = request.get_json()
    client_name = data.get("client")
    product_name = data.get("product")

    client_id = get_or_create_client(client_name)
    product_id = get_or_create_product(client_id, product_name)
    ambientes = get_environments_by_product(product_id)
    return jsonify(ambientes)

@app.route("/update_full_deployment", methods=["POST"])
def update_deployment():
    data = request.get_json()
    client_id = get_or_create_client(data["client"])
    product_id = get_or_create_product(client_id, data["product"])

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
