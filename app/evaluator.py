import math
from typing import Dict
from app.tools import ArchitectureBlueprint

def calculate_completeness(blueprint: ArchitectureBlueprint) -> float:
    """
    Score 0-100 indicating how thoroughly the required fields were populated.
    """
    score = 0

    if blueprint.recommended_stack.cache or blueprint.recommended_stack.message_queue:
        score += 20
    if len(blueprint.api_routes) >= 3:
        score += 20
    if len(blueprint.database_schema) >= 2:
        score += 20
    if len(blueprint.folder_structure) >= 4:
        score += 20
    deployment_ok = len(blueprint.deployment_recommendations.strip()) > 50
    scaling_ok = len(blueprint.scaling_recommendations.strip()) > 50
    if deployment_ok and scaling_ok:
        score += 20

    return float(score)


def calculate_scalability_awareness(blueprint: ArchitectureBlueprint) -> float:
    """
    Score 0-100 indicating quality of scaling/deployment recommendations via keyword heuristics.
    """
    text = (blueprint.deployment_recommendations + " " + blueprint.scaling_recommendations).lower()
    keywords = [
        "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
        "load balance", "cdn", "redis", "cache", "replica", "sharding", "microservices",
    ]
    matches = sum(1 for kw in keywords if kw in text)
    return float(min(matches * 20, 100))


def calculate_api_quality(blueprint: ArchitectureBlueprint) -> float:
    if not blueprint.api_routes:
        return 0.0

    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    points_per_route = 100.0 / len(blueprint.api_routes)
    total_score = 0.0

    for route in blueprint.api_routes:
        route_score = 0.0
        # Half the per-route points for a valid HTTP method
        if route.method.upper() in valid_methods:
            route_score += points_per_route * 0.5
        # Half the per-route points for a proper path
        if route.path.startswith("/"):
            route_score += points_per_route * 0.5
        total_score += route_score

    return min(round(total_score, 2), 100.0)


def calculate_structure_accuracy(blueprint: ArchitectureBlueprint) -> float:
    checks = [
        bool(blueprint.recommended_stack.language.strip()),
        bool(blueprint.recommended_stack.framework.strip()),
        bool(blueprint.recommended_stack.database.strip()),
        len(blueprint.api_routes) > 0,
        len(blueprint.database_schema) > 0,
        all(len(entity.fields) > 0 for entity in blueprint.database_schema)
        if blueprint.database_schema else False,
        len(blueprint.folder_structure) > 0,
        len(blueprint.deployment_recommendations.strip()) > 10,
        len(blueprint.scaling_recommendations.strip()) > 10,
    ]
    passed = sum(1 for c in checks if c)
    return round((passed / len(checks)) * 100, 2)


def calculate_latency_score(latency_seconds: float) -> float:
    if latency_seconds <= 2.0:
        return 100.0
    elif latency_seconds >= 20.0:
        return 0.0
    else:
        return round(max(0.0, 100.0 - ((latency_seconds - 2.0) * (100.0 / 18.0))), 2)


def evaluate_blueprint(blueprint: ArchitectureBlueprint, latency_seconds: float) -> Dict[str, float]:
    completeness     = calculate_completeness(blueprint)
    scalability      = calculate_scalability_awareness(blueprint)
    api_quality      = calculate_api_quality(blueprint)
    structure        = calculate_structure_accuracy(blueprint)
    latency_score    = calculate_latency_score(latency_seconds)

    raw = (
        (completeness  * 0.30) +
        (scalability   * 0.25) +
        (api_quality   * 0.20) +
        (structure     * 0.15) +
        (latency_score * 0.10)
    )

    final_score = max(1, math.floor(raw * 100))

    return {
        "completeness_score":        round(completeness, 2),
        "scalability_score":         round(scalability, 2),
        "api_quality_score":         round(api_quality, 2),
        "structure_accuracy_score":  round(structure, 2),
        "latency_score":             round(latency_score, 2),
        "latency_seconds":           round(latency_seconds, 3),
        "final_metric_score":        final_score,
    }
