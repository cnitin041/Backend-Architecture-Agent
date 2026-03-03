import asyncio
from app.agent import generate_architecture
from app.evaluator import evaluate_blueprint
from app.utils import logger
from app.scenarios import SCENARIOS 


async def run_benchmarks():
    logger.info("Starting benchmarking suite...")
    results = {}

    for name, requirement in SCENARIOS.items():
        logger.info(f"--- Running Benchmark: {name} ---")
        blueprint, latency, usage = await generate_architecture(requirement)

        if not blueprint:
            logger.error(f"Failed to generate blueprint for '{name}'")
            results[name] = {"error": "Failed to generate"}
            continue

        metrics = evaluate_blueprint(blueprint, latency)
        results[name] = {
            "metrics": metrics,
            "usage": usage,
            "recommended_framework": blueprint.recommended_stack.framework,
            "database": blueprint.recommended_stack.database,
        }

        logger.info(f"Score for '{name}': {metrics['final_metric_score']}/10000")
        logger.info(f"Latency: {latency:.2f}s | Tokens: {usage['total_tokens']}")

    # ── Final comparison report ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  BENCHMARK COMPARISON REPORT")
    print("=" * 60)
    for name, data in results.items():
        if "error" in data:
            print(f"\n[FAILED] {name}")
            continue

        m = data["metrics"]
        print(f"\nScenario   : {name}")
        print(f"  Framework : {data['recommended_framework']}")
        print(f"  Database  : {data['database']}")
        print(f"  Latency   : {m['latency_seconds']}s")
        print(f"  Tokens    : {data['usage'].get('total_tokens', 0)}")
        print(f"  SCORE     : {m['final_metric_score']} / 10000")
        print("  Breakdown :")
        print(f"    Completeness  : {m['completeness_score']}")
        print(f"    Scalability   : {m['scalability_score']}")
        print(f"    API Quality   : {m['api_quality_score']}")
        print(f"    Structure Acc : {m['structure_accuracy_score']}")
        print(f"    Latency Score : {m['latency_score']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
