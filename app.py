from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
from datetime import datetime
from collections import defaultdict
from utils import calculate_kpis

from model import (
    create_db, add_or_get_feature, save_deployment,
    get_all_features, get_all_feature_names, update_env_status,
    update_full_deployment, get_all_deployment_details, get_db_connection
)

app = Flask(__name__)
today = date.today().isoformat()
create_db()

ambiente_options = ["PreDEV", "DEV", "UAT", "PPD", "PRD"]
estado_options = ["Valid", "Invalid", "Failed", "Archived", "In-PRD"]
type_options = ["PersDB", "App", "MDSGen", "MDSHealth"]
repos_options = ["Repo1", "Repo2"]
rm_options = ["Michel LF", "Elizabet RC", "Yasser F"]
app_options = ["INSIS", "Premium"]
tenancy_options = ["Uruguay", "Panama"]

@app.route('/api/tenants')
def api_tenants():
    conn = get_db_connection()
    rows = conn.execute('SELECT id, name FROM tenants ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/solutions/<int:tenant_id>')
def api_solutions(tenant_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT id, name FROM solutions WHERE tenant_id = ? ORDER BY name', (tenant_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/products/<int:solution_id>')
def api_products(solution_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT id, name FROM products WHERE solution_id = ? ORDER BY name', (solution_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form = request.form
        feature_data = {
            "name": form["name"],
            "repositorio": form["repositorio"],
            "product_id": form["product_id"],
            "master": form["master"]
        }
        feature_id = add_or_get_feature(feature_data)

        deployment_data = {
            "ambiente": form["ambiente"],
            "estado": form["estado"],
            "fecha": form["fecha"],
            "release_manager": form["release_manager"]
        }
        save_deployment(feature_id, deployment_data)
        return redirect(url_for("index"))

    # Get filters
    filtro = request.args.get("filtro", "").strip()
    filter_estado = request.args.get("filter_estado", "")
    filter_ambiente = request.args.get("filter_ambiente", "")

    # 🧩 Full dataset for matrix table (ALWAYS UNFILTERED)
    rows_all = get_all_features()

    # 🎯 Filtered list only for flat result table
    rows_filtered = get_all_features()
    filtered_deployments = [
        r for r in rows_filtered
        if (not filtro or
            filtro.lower() in r["name"].lower() or
            filtro.lower() in r["repositorio"].lower() or
            filtro.lower() in (r["estado"] or "").lower())
        and (not filter_estado or r["estado"] == filter_estado)
        and (not filter_ambiente or r["ambiente"] == filter_ambiente)
    ]

    # ✅ Build matrix view using full data
    grouped = defaultdict(lambda: {
        "repositorio": "", "type": "", "application": "", "master": "",
        "env_status": {env: "" for env in ambiente_options}
    })

    for row in rows_all:
        name = row["name"]
        grouped[name]["repositorio"] = row["repositorio"]
        grouped[name]["type"] = row["type"]
        grouped[name]["application"] = row["application"]
        grouped[name]["master"] = row["master"]
        if row["ambiente"]:
            grouped[name]["env_status"][row["ambiente"]] = row["estado"]

    deployment_details = get_all_deployment_details()
    kpis = calculate_kpis(filtered_deployments, ambiente_options)


    return render_template("index.html",
                           grouped_deployments=grouped,
                           deployment_details=deployment_details,
                           ambiente_options=ambiente_options,
                           estado_options=estado_options,
                           type_options=type_options,
                           repos_options=repos_options,
                           rm_options=rm_options,
                           app_options=app_options,
                           tenancy_options=tenancy_options,
                           feature_names=get_all_feature_names(),
                           today=today,
                           filtro=filtro,
                           filter_estado=filter_estado,
                           filter_ambiente=filter_ambiente,
                           filtered_deployments=filtered_deployments,
                           kpis=kpis)


@app.route("/update_full_deployment", methods=["POST"])
def update_full_deployment_route():
    data = request.get_json()
    feature_name = data.get("feature")
    ambiente = data.get("ambiente")
    estado = data.get("estado")
    fecha = data.get("fecha")
    release_manager = data.get("release_manager")

    rows = get_all_features()
    for row in rows:
        if row["name"] == feature_name:
            feature_id = row["feature_id"]
            update_full_deployment(feature_id, ambiente, estado, fecha, release_manager)
            return jsonify(success=True)

    return jsonify(success=False, message="Feature not found"), 400

@app.route("/get_deployment_details", methods=["POST"])
def get_deployment_details():
    data = request.get_json()
    feature_name = data.get("feature")
    ambiente = data.get("ambiente")

    rows = get_all_features()
    for row in rows:
        if row["name"] == feature_name and row["ambiente"] == ambiente:
            return jsonify(success=True,
                           estado=row["estado"],
                           fecha=row["fecha"],
                           release_manager=row["release_manager"])
    return jsonify(success=False)

@app.route("/reports", methods=["GET"])
def reports():
    filtro = request.args.get("filtro", "").strip()
    filter_estado = request.args.get("filter_estado", "")
    filter_ambiente = request.args.get("filter_ambiente", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    rows = get_all_features()

    def within_date_range(row):
        if not row["fecha"]:
            return False
        row_date = datetime.strptime(row["fecha"], "%Y-%m-%d")
        if start_date:
            if row_date < datetime.strptime(start_date, "%Y-%m-%d"):
                return False
        if end_date:
            if row_date > datetime.strptime(end_date, "%Y-%m-%d"):
                return False
        return True

    filtered_deployments = [
        r for r in rows
        if (not filtro or
            filtro.lower() in r["name"].lower() or
            filtro.lower() in r["repositorio"].lower() or
            filtro.lower() in (r["estado"] or "").lower())
        and (not filter_estado or r["estado"] == filter_estado)
        and (not filter_ambiente or r["ambiente"] == filter_ambiente)
        and within_date_range(r)
    ]
    

    return render_template("reports.html",
                           filtered_deployments=filtered_deployments,
                           ambiente_options=ambiente_options,
                           estado_options=estado_options,
                           filtro=filtro,
                           filter_estado=filter_estado,
                           filter_ambiente=filter_ambiente,
                           start_date=start_date,
                           end_date=end_date)

@app.route("/delete_feature", methods=["POST"])
def delete_feature():
    data = request.get_json()
    feature_name = data.get("feature")
    if not feature_name:
        return jsonify(success=False, message="No feature name provided"), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # Buscar todos los feature_id con ese nombre
    cursor.execute("SELECT id FROM features WHERE name = ?", (feature_name,))
    feature_ids = [row["id"] for row in cursor.fetchall()]
    if not feature_ids:
        conn.close()
        return jsonify(success=False, message="Feature not found"), 404

    # Eliminar despliegues asociados
    cursor.executemany("DELETE FROM deployments WHERE feature_id = ?", [(fid,) for fid in feature_ids])
    # Eliminar el feature
    cursor.executemany("DELETE FROM features WHERE id = ?", [(fid,) for fid in feature_ids])
    conn.commit()
    conn.close()
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
