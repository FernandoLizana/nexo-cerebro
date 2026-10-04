"""The fly link stays closed until the connectivity file exists."""

from nexo.demo.fly_bridge import pulse, status


def test_status_names_missing_parquet():
    info = status()
    assert "mosca" in info["root"].replace("\\", "/")
    assert info["code"] is True
    if not info["ok"]:
        assert "connectivity parquet" in info["missing"]


def test_pulse_does_not_start_without_parquet():
    info = status()
    if info["ok"]:
        return
    result = pulse([720575940619593284], duration_ms=5000)
    assert result["ok"] is False
    assert result["status"]["missing"]
