from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
from datetime import datetime
from collections import defaultdict
from utils import calculate_kpis, get_fully_deployed_features

from model import (
    create_db, add_or_get_feature, save_deployment,
    get_all_features, get_all_feature_names, update_env_status,
    update_full_deployment, get_all_deployment_details
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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form = request.form
        feature_data = {
            "name": form["name"],
            "repositorio": form["repositorio"],
            "type": form["type"],
            "application": form["application"],
            "tenancy": form["tenancy"],
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

        # === Prepare Daily Deployments Count ===
    from collections import Counter

    deployments_per_day = Counter()
    for row in filtered_deployments:
        if row["fecha"]:
            deployments_per_day[row["fecha"]] += 1

    daily_deployments_data = [
        {"date": date_str, "count": deployments_per_day[date_str]}
        for date_str in sorted(deployments_per_day.keys())
    ]

    # === Prepare Cumulative Fully-Deployed Over Time ===

    # First, get all valid deployments (those that affect "fully deployed")
    valid_rows = [row for row in filtered_deployments if row["estado"] == "Valid"]

    # Build list of all dates we want to plot
    dates = sorted(set(row["fecha"] for row in valid_rows if row["fecha"]))

    # For each date, compute "as of that day" fully deployed count
    cumulative_data = []
    for date_cutoff in dates:
        rows_up_to_date = [r for r in valid_rows if r["fecha"] <= date_cutoff]
        fully_deployed_features = get_fully_deployed_features(rows_up_to_date, ambiente_options)
        cumulative_data.append({"date": date_cutoff, "count": len(fully_deployed_features)})

    

    return render_template("reports.html",
                           filtered_deployments=filtered_deployments,
                           ambiente_options=ambiente_options,
                           estado_options=estado_options,
                           filtro=filtro,
                           filter_estado=filter_estado,
                           filter_ambiente=filter_ambiente,
                           start_date=start_date,
                           end_date=end_date,
                           daily_deployments_data=daily_deployments_data,
                           cumulative_fully_deployed_data=cumulative_data)



if __name__ == "__main__":
    app.run(debug=True)
