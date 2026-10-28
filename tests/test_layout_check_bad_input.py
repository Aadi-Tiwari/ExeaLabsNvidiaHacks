"""scripts/check_layout.py exits 1 when a layout fails the check. An input it cannot read (a scan.json the scan checks
refuse, a RoomPlan export the normalizer refuses, a twin.json or layout.yaml that is not JSON or YAML) exited 1 too,
with a traceback, so a caller took it for a failed layout; like a missing room (#294) it is now exit 2 and one line."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_layout", ROOT / "scripts" / "check_layout.py")
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)


def _run(argv, capsys) -> str:
    with pytest.raises(SystemExit) as e:
        cl.main([str(x) for x in argv])
    assert e.value.code == 2
    return capsys.readouterr().err


def test_a_refused_scan_json(tmp_path, capsys):
    scan = json.loads((ROOT / "scans" / "hero_kitchen" / "scan.json").read_text(encoding="utf-8"))
    (tmp_path / "bad_room").mkdir()
    (tmp_path / "bad_room" / "scan.json").write_text(json.dumps({**scan, "units": "feet"}), encoding="utf-8")
    err = _run(["--room", "bad_room", "--scans", tmp_path], capsys)
    assert f"{tmp_path / 'bad_room' / 'scan.json'}: units must be 'meters', got 'feet'" in err


def test_a_refused_roomplan_export(tmp_path, capsys):
    (tmp_path / "rp.json").write_text('{"walls": [{"transform": 5}]}', encoding="utf-8")
    err = _run(["--roomplan", tmp_path / "rp.json"], capsys)
    assert f"{tmp_path / 'rp.json'}: wall 0" in err and "transform must be 16 finite numbers" in err


@pytest.mark.parametrize("bad, text", [("twin.json", "{"), ("layout.yaml", "room: [\n")])
def test_a_twin_folder_file_that_does_not_parse(tmp_path, capsys, bad, text):
    (tmp_path / "twin.json").write_text("{}", encoding="utf-8")
    (tmp_path / "layout.yaml").write_text("room: {}\n", encoding="utf-8")
    (tmp_path / bad).write_text(text, encoding="utf-8")
    assert f"{tmp_path / bad}: " in _run([tmp_path], capsys)
