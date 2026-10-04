from datetime import date

import journal


# Send the log to a temporary file so tests never touch your real mood_log.json.
def _use_temp_log(monkeypatch, tmp_path):
    monkeypatch.setattr(journal, "LOG_PATH", tmp_path / "mood_log.json")


def test_summary_when_nothing_logged(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    assert journal.daily_summary() == "Your pet has no mood changes logged today."


def test_summary_counts_one_mood(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    for _ in range(3):
        journal.log_mood_change("panicking")
    assert journal.daily_summary() == "Your pet panicked 3 times today."


def test_summary_uses_singular_for_one(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    journal.log_mood_change("sweating")
    assert journal.daily_summary() == "Your pet sweated 1 time today."


def test_summary_joins_two_and_three_moods(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    journal.log_mood_change("panicking")
    journal.log_mood_change("sleeping")
    assert journal.daily_summary() == "Your pet panicked 1 time and fell asleep 1 time today."
    journal.log_mood_change("happy")
    assert journal.daily_summary() == (
        "Your pet panicked 1 time, fell asleep 1 time, and was happy 1 time today."
    )


def test_summary_ignores_other_days(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    journal.log_mood_change("panicking")
    assert journal.daily_summary(day=date(2000, 1, 1)) == "Your pet has no mood changes logged today."


def test_broken_log_file_does_not_crash(monkeypatch, tmp_path):
    _use_temp_log(monkeypatch, tmp_path)
    (tmp_path / "mood_log.json").write_text("{not valid json", encoding="utf-8")
    assert journal.daily_summary() == "Your pet has no mood changes logged today."
    journal.log_mood_change("happy")   # and logging still works afterwards
    assert journal.daily_summary() == "Your pet was happy 1 time today."
