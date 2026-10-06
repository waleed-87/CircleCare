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