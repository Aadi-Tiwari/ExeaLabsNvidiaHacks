"""scripts/scan_accuracy.py on a room folder that has measurements.json but no scan.json or roomplan.json.

It died with a FileNotFoundError traceback at that room, so every room after it went unchecked (the default run walks
all of scans/). Now that room is an ERROR line counted as failing, and the others are still measured.
"""

import shutil
import sys

from conftest import REPO, SCANS

sys.path.insert(0, str(REPO / "scripts"))
import scan_accuracy  # noqa: E402

HERO_FIXTURE = REPO / "tests" / "fixtures" / "measurements" / "hero_kitchen.json"


def _measured(tmp_path, name, scan=True):
    d = tmp_path / name
    d.mkdir()
    if scan:
        shutil.copy(SCANS / "hero_kitchen" / "scan.json", d / "scan.json")
    shutil.copy(HERO_FIXTURE, d / "measurements.json")
    return d


def test_room_without_a_scan_is_an_error_and_the_next_room_is_still_measured(tmp_path, capsys):
    empty, ok = _measured(tmp_path, "a_no_scan", scan=False), _measured(tmp_path, "b_ok")
    assert scan_accuracy.main([str(empty), str(ok)]) == 1
    out = capsys.readouterr().out
    assert "a_no_scan: ERROR no scan.json or roomplan.json" in out
    assert "b_ok  (tolerance 5.0 cm" in out and "counter_length_m" in out
    assert "2 room(s) measured, 1 failing" in out


def test_room_without_a_scan_alone_fails(tmp_path, capsys):
    assert scan_accuracy.main([str(_measured(tmp_path, "no_scan", scan=False))]) == 1
    assert "1 room(s) measured, 1 failing" in capsys.readouterr().out
