"""Rebuild the database from data/, with: uv run -m backend.seed"""

from backend.database import engine, location, seed


def main() -> None:
    """Rebuild the database and say what it holds."""
    db = engine()
    counts = seed(db)
    print(
        f"Seeded {counts['cases']} cases, {counts['contracts']} contracts, "
        f"{counts['customers']} customers and {counts['workers']} workers "
        f"into {location(db)}, with {counts['held_out_cases']} held-out cases "
        f"and {counts['worker_decisions']} workers' decisions for evaluations"
    )


if __name__ == "__main__":
    main()
