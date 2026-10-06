import sqlite3
from datetime import date, datetime, timedelta

DB_NAME = "carecircle.db"

# Used for demo/testing instead of relying on the real clock
DEMO_NOW = None


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


def confirm_dose(medication_id: int) -> dict:
    """Confirm that today's medication dose was taken."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute(
        """
        SELECT id, taken_at
        FROM dose_log
        WHERE medication_id = ?
          AND scheduled_date = ?
          AND taken_at IS NOT NULL
        """,
        (medication_id, today),
    )

    existing_dose = cursor.fetchone()

    if existing_dose:
        conn.close()

        return {
            "success": False,
            "message": "Dose already confirmed for today.",
        }

    taken_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO dose_log (medication_id, scheduled_date, taken_at)
        VALUES (?, ?, ?)
        """,
        (medication_id, today, taken_at),
    )

    dose_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "dose_id": dose_id,
        "medication_id": medication_id,
        "scheduled_date": today,
        "taken_at": taken_at,
        "message": "Dose confirmed successfully.",
    }


def create_alert(alert_type: str, message: str) -> dict:
    """Create an alert."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO alerts (created_at, type, message, resolved)
        VALUES (?, ?, ?, 0)
        """,
        (created_at, alert_type, message),
    )

    alert_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "id": alert_id,
        "type": alert_type,
        "message": message,
        "resolved": 0,
    }


def missed_doses() -> list:
    """Find today's medications that were scheduled but not confirmed."""

    now = DEMO_NOW if DEMO_NOW is not None else datetime.now()

    today = now.date().isoformat()
    current_time = now.strftime("%H:%M")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, time_hhmm
        FROM medications
        WHERE active = 1
          AND time_hhmm < ?
        ORDER BY time_hhmm
        """,
        (current_time,),
    )

    medications = cursor.fetchall()

    missed = []

    for medication_id, name, time_hhmm in medications:

        cursor.execute(
            """
            SELECT id
            FROM dose_log
            WHERE medication_id = ?
              AND scheduled_date = ?
              AND taken_at IS NOT NULL
            """,
            (medication_id, today),
        )

        confirmed = cursor.fetchone()

        if confirmed is None:
            message = f"Missed dose: {name} scheduled for {time_hhmm}."

            cursor.execute(
                """
                SELECT id
                FROM alerts
                WHERE type = 'missed_dose'
                  AND message = ?
                  AND resolved = 0
                """,
                (message,),
            )

            existing_alert = cursor.fetchone()

            if existing_alert is None:
                cursor.execute(
                    """
                    INSERT INTO alerts
                    (created_at, type, message, resolved)
                    VALUES (?, ?, ?, 0)
                    """,
                    (datetime.now().isoformat(), "missed_dose", message),
                )

            missed.append(
                {
                    "medication_id": medication_id,
                    "name": name,
                    "time_hhmm": time_hhmm,
                    "message": message,
                }
            )

    conn.commit()
    conn.close()

    return missed


def daily_checkin(mood: str, note: str = "") -> dict:
    """Record today's daily check-in."""

    today = date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO checkins (date, mood, note)
        VALUES (?, ?, ?)
        """,
        (today, mood, note),
    )

    checkin_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "id": checkin_id,
        "date": today,
        "mood": mood,
        "note": note,
    }


def check_three_bad_days() -> dict:
    """Create an alert if the last three calendar days all have bad moods."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = date.today()

    required_dates = [
        (today - timedelta(days=2)).isoformat(),
        (today - timedelta(days=1)).isoformat(),
        today.isoformat(),
    ]

    moods = []

    for checkin_date in required_dates:
        cursor.execute(
            """
            SELECT mood
            FROM checkins
            WHERE date = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (checkin_date,),
        )

        row = cursor.fetchone()

        if row is None:
            conn.close()

            return {
                "alert_created": False,
                "message": "Not enough consecutive daily check-ins.",
            }

        moods.append(row[0].lower())

    bad_moods = {"bad", "sad", "very bad", "poor"}

    three_bad_days = all(
        mood in bad_moods
        for mood in moods
    )

    if not three_bad_days:
        conn.close()

        return {
            "alert_created": False,
            "message": "Three bad days condition not met.",
        }

    message = "Three consecutive bad days detected."

    cursor.execute(
        """
        SELECT id
        FROM alerts
        WHERE type = 'three_bad_days'
          AND message = ?
          AND resolved = 0
        """,
        (message,),
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()

        return {
            "alert_created": False,
            "message": "Three-bad-days alert already exists.",
        }

    cursor.execute(
        """
        INSERT INTO alerts
        (created_at, type, message, resolved)
        VALUES (?, ?, ?, 0)
        """,
        (datetime.now().isoformat(), "three_bad_days", message),
    )

    alert_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "alert_created": True,
        "alert_id": alert_id,
        "message": message,
    }

def get_family_summary() -> dict:
    """Return a summary of medications, check-ins, and alerts."""

    today = date.today().isoformat()

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

    medications = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, type, message, resolved
        FROM alerts
        WHERE resolved = 0
        ORDER BY id DESC
        """
    )

    alerts = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, date, mood, note
        FROM checkins
        ORDER BY date DESC
        LIMIT 7
        """
    )

    checkins = cursor.fetchall()

    conn.close()

    return {
        "date": today,
        "medications": [
            {
                "id": row[0],
                "name": row[1],
                "time_hhmm": row[2],
                "notes": row[3],
            }
            for row in medications
        ],
        "alerts": [
            {
                "id": row[0],
                "type": row[1],
                "message": row[2],
                "resolved": row[3],
            }
            for row in alerts
        ],
        "recent_checkins": [
            {
                "id": row[0],
                "date": row[1],
                "mood": row[2],
                "note": row[3],
            }
            for row in checkins
        ],
    }