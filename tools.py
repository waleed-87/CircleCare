import sqlite3
from datetime import date

DB_NAME = "carecircle.db"


def add_medication(name: str, time_hhmm: str, notes: str = "") -> dict:
    """Add a medication to the database."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO medications (name, time_hhmm, notes, active)
        VALUES (?, ?, ?, 1)
        """,
        (name, time_hhmm, notes),
    )

    medication_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "id": medication_id,
        "name": name,
        "time_hhmm": time_hhmm,
        "notes": notes,
        "active": 1,
    }


def get_today_schedule() -> list:
    """Get all active medications scheduled for today."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, time_hhmm, notes
        FROM medications
        WHERE active = 1
        ORDER BY time_hhmm
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "time_hhmm": row[2],
            "notes": row[3],
            "date": date.today().isoformat(),
        }
        for row in rows
    ]