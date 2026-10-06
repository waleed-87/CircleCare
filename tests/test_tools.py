import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tools


def test_add_medication():
    result = tools.add_medication(
        name="Paracetamol",
        time_hhmm="14:00",
        notes="After lunch"
    )

    assert result["name"] == "Paracetamol"
    assert result["time_hhmm"] == "14:00"
    assert result["notes"] == "After lunch"
    assert result["active"] == 1


def test_get_today_schedule():
    tools.add_medication(
        name="Vitamin D",
        time_hhmm="09:00",
        notes="Morning"
    )

    schedule = tools.get_today_schedule()

    assert len(schedule) > 0
    assert any(
        medication["name"] == "Vitamin D"
        for medication in schedule
    )



def test_confirm_dose_double_guard():
    medication = tools.add_medication(
        name="Test Medicine",
        time_hhmm="10:00",
        notes="Test dose"
    )

    medication_id = medication["id"]

    # First confirmation should succeed
    first = tools.confirm_dose(medication_id)

    assert first["success"] is True

    # Second confirmation should be refused
    second = tools.confirm_dose(medication_id)

    assert second["success"] is False
    assert second["message"] == "Dose already confirmed for today."   


def test_missed_doses_creates_alert():
    tools.DEMO_NOW = __import__("datetime").datetime.now().replace(
        hour=23,
        minute=59
    )

    medication = tools.add_medication(
        name="Missed Medicine",
        time_hhmm="08:00",
        notes="Morning"
    )

    missed = tools.missed_doses()

    assert any(
        dose["medication_id"] == medication["id"]
        for dose in missed
    )


def test_daily_checkin():
    result = tools.daily_checkin(
        mood="good",
        note="Feeling fine"
    )

    assert result["mood"] == "good"
    assert result["note"] == "Feeling fine"


def test_three_bad_days_alert():
    conn = __import__("sqlite3").connect(tools.DB_NAME)
    cursor = conn.cursor()

    today = __import__("datetime").date.today()

    for days_ago, note in [
        (2, "Day 1"),
        (1, "Day 2"),
        (0, "Day 3"),
    ]:
        checkin_date = (today - __import__("datetime").timedelta(days=days_ago)).isoformat()

        cursor.execute(
            """
            INSERT INTO checkins (date, mood, note)
            VALUES (?, ?, ?)
            """,
            (checkin_date, "bad", note),
        )

    conn.commit()
    conn.close()

    result = tools.check_three_bad_days()

    assert result["alert_created"] is True


def test_family_summary():
    result = tools.get_family_summary()

    assert "medications" in result
    assert "alerts" in result
    assert "recent_checkins" in result   