from commute_analyzer import CommuteAnalyzer


def _make_analyzer():
    """Create an instance of CommuteAnalyzer without running __init__."""
    return CommuteAnalyzer.__new__(CommuteAnalyzer)


def test_format_time_seconds_only():
    ca = _make_analyzer()
    assert ca._format_time(0.5) == "30s"


def test_format_time_minutes_only():
    ca = _make_analyzer()
    assert ca._format_time(5) == "5m"


def test_format_time_hours_with_minutes():
    ca = _make_analyzer()
    assert ca._format_time(130) == "2h 10m"


def test_format_time_days_case():
    ca = _make_analyzer()
    # 1 day 12 hours = 2160 minutes
    assert ca._format_time(2160) == "1d 12h"


def test_format_time_years_case():
    ca = _make_analyzer()
    # 1 year 2 days = 365 days + 2 days
    minutes = (365 + 2) * 24 * 60
    assert ca._format_time(minutes) == "1y 2d"
