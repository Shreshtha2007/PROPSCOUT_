
import sqlite3
import pandas as pd
from pathlib import Path

# Project folder and file paths
PROJECT_FOLDER = Path(__file__).parent
DB_PATH = PROJECT_FOLDER / "safenest.db"
CSV_PATH = PROJECT_FOLDER / "house_prices.csv"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def load_dataset():
    """Load the complete Kaggle CSV dataset."""

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}\n"
            "Place house_prices.csv in the same folder as database.py."
        )

    df = pd.read_csv(CSV_PATH)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    if df.empty:
        raise ValueError("The Kaggle CSV contains no data rows.")

    return df


def create_database():
    """Create a table to store the original Kaggle records."""

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS kaggle_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def import_dataset():
    """Import all CSV rows into SQLite without changing their columns."""

    df = load_dataset()
    create_database()

    # Store each complete original row as JSON.
    # This preserves the dataset's original column names.
    records = df.to_json(orient="records", force_ascii=False)

    import json
    data = json.loads(records)

    connection = get_connection()

    try:
        # Replace previously imported Kaggle rows
        connection.execute("DELETE FROM kaggle_properties")

        connection.executemany(
            "INSERT INTO kaggle_properties (data) VALUES (?)",
            [
                (json.dumps(row, ensure_ascii=False, default=str),)
                for row in data
            ]
        )

        connection.commit()

    finally:
        connection.close()

    print("Kaggle dataset imported successfully!")
    print("CSV rows:", len(df))
    print("Database rows:", len(data))
    print("Dataset columns:", df.columns.tolist())


def get_all_properties():
    """Return all imported Kaggle records as a DataFrame."""

    connection = get_connection()

    try:
        rows = connection.execute(
            "SELECT data FROM kaggle_properties"
        ).fetchall()
    finally:
        connection.close()

    import json

    records = [json.loads(row["data"]) for row in rows]

    return pd.DataFrame(records)


if __name__ == "__main__":
    try:
        import_dataset()

        properties = get_all_properties()

        print("\nFirst five imported rows:")
        print(properties.head().to_string(index=False))

    except Exception as error:
        print("ERROR:", error)
