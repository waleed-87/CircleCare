import sqlite3

DB_NAME = "carecircle.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time_hhmm TEXT NOT NULL,
            notes TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dose_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            scheduled_date TEXT NOT NULL,
            taken_at TEXT,
            FOREIGN KEY (medication_id) REFERENCES medications(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            mood TEXT,
            note TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

    print("Database and tables created successfully.")


if __name__ == "__main__":
    create_tables()