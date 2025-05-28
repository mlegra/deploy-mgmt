from datetime import datetime
from collections import Counter, defaultdict

def calculate_kpis(filtered_deployments, ambiente_options):
    total = len(filtered_deployments)
    failed = sum(1 for d in filtered_deployments if d["estado"] == "Failed")
    valid = sum(1 for d in filtered_deployments if d["estado"] == "Valid")
    success_rate = round((valid / total) * 100, 1) if total > 0 else 0

    env_counts = Counter(d["ambiente"] for d in filtered_deployments if d["ambiente"])
    most_active_env = env_counts.most_common(1)[0][0] if env_counts else "-"

    rm_counts = Counter(d["release_manager"] for d in filtered_deployments if d["release_manager"])
    top_rm = rm_counts.most_common(1)[0][0] if rm_counts else "-"

    dates = [datetime.strptime(d["fecha"], "%Y-%m-%d") for d in filtered_deployments if d["fecha"]]
    if dates:
        span = (max(dates) - min(dates)).days + 1
        avg_per_day = round(total / span, 2) if span > 0 else total
    else:
        avg_per_day = 0

    # ✅ Calculate fully deployed features
    valid_envs_by_feature = defaultdict(set)
    for row in filtered_deployments:
        if row["estado"] == "Valid" and row["ambiente"]:
            valid_envs_by_feature[row["name"]].add(row["ambiente"])

    required_envs = set(ambiente_options)
    fully_deployed_features = [
        f for f, envs in valid_envs_by_feature.items()
        if required_envs.issubset(envs)
    ]
    fully_deployed_count = len(fully_deployed_features)

    return {
        "total": total,
        "failed": failed,
        "success_rate": success_rate,
        "most_active_env": most_active_env,
        "top_rm": top_rm,
        "avg_per_day": avg_per_day,
        "fully_deployed": fully_deployed_count  # ✅ NEW KPI
    }
