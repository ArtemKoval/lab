"""Rebuild the database from the pack, with: uv run -m backend.seed"""

from backend.database import database_path, seed


def main() -> None:
    """Rebuild the database and say what it holds."""
    path = database_path()
    counts = seed(path)
    print(
        f"Seeded {counts['cases']} cases, {counts['contracts']} contracts, "
        f"{counts['customers']} customers and {counts['workers']} workers "
        f"into {path.name}"
    )


if __name__ == "__main__":
    main()
