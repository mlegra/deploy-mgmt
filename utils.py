from datetime import datetime
from collections import Counter, defaultdict

def calculate_kpis(filtered_deployments, ambiente_options):
    # ...normalización igual...
    norm_deployments = []
    for d in filtered_deployments:
        d_norm = dict(d)
        if d_norm.get("ambiente"):
            d_norm["ambiente"] = d_norm["ambiente"].strip().upper()
        norm_deployments.append(d_norm)
    print("Ambientes en norm_deployments:", [d["ambiente"] for d in norm_deployments])
    ambiente_options_norm = [a.strip().upper() for a in ambiente_options]

    # SOLO CUENTA LOS QUE TIENEN AMBIENTE
    total = len([d for d in norm_deployments if d.get("ambiente")])
    failed = sum(1 for d in norm_deployments if d["estado"] == "Failed" and d.get("ambiente"))
    valid = sum(1 for d in norm_deployments if d["estado"] == "Valid" and d.get("ambiente"))
    success_rate = round((valid / total) * 100, 1) if total > 0 else 0

    env_counts = Counter(d["ambiente"] for d in norm_deployments if d["ambiente"])
    most_active_env = env_counts.most_common(1)[0][0] if env_counts else "-"

    rm_counts = Counter(d["release_manager"] for d in norm_deployments if d["release_manager"] and d.get("ambiente"))
    top_rm = rm_counts.most_common(1)[0][0] if rm_counts else "-"

    dates = [datetime.strptime(d["fecha"], "%Y-%m-%d") for d in norm_deployments if d["fecha"] and d.get("ambiente")]
    if dates:
        span = (max(dates) - min(dates)).days + 1
        avg_per_day = round(total / span, 2) if span > 0 else total
    else:
        avg_per_day = 0

    # ✅ Calculate fully deployed features
    valid_envs_by_feature = defaultdict(set)
    for row in norm_deployments:
        if row["estado"] == "Valid" and row.get("ambiente"):
            valid_envs_by_feature[row["name"]].add(row["ambiente"])

    required_envs = set(ambiente_options_norm)
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
        "fully_deployed": fully_deployed_count
    }
