import argparse

import pytest

from arrival import cli


def _ns(tmp_path, **kw):
    d = dict(room="nope_room", scans="scans", out=str(tmp_path), families="counter_to_sink", episodes=1, people=0,
             policy="scripted", res=32, seed=0, save_preview=False, planner="rule", split="train",
             instructions="template", tavily=False, holdout=False, query=None)
    d.update(kw)
    return argparse.Namespace(**d)


def test_sim_missing_room_is_usage_error(tmp_path, capsys):
    pytest.importorskip("mujoco")
    assert cli.cmd_sim(_ns(tmp_path)) == cli.EXIT_USAGE
    assert "no scan for room" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--people", "--seed"])
def test_sim_negative_people_or_seed_is_a_usage_error_and_keeps_the_old_dataset(tmp_path, capsys, monkeypatch, flag):
    pytest.importorskip("mujoco")
    monkeypatch.chdir(tmp_path)  # resolve_scans falls back to the repo's scans/
    old = tmp_path / "datasets" / "hero_kitchen_sim" / "meta" / "info.json"
    old.parent.mkdir(parents=True)
    old.write_text("{}")
    assert cli.main(["sim", flag, "-1", "--episodes", "1", "--families", "open_drawer",
                     "--out", str(tmp_path)]) == cli.EXIT_USAGE
    assert f"{flag} must be >= 0" in capsys.readouterr().err
    assert old.is_file()


def test_research_missing_room_is_usage_error(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("arrival.tasks.tavily_research.TavilyResearchAgent", lambda *a, **k: object())
    assert cli.cmd_research(_ns(tmp_path)) == cli.EXIT_USAGE


def test_sim_vla_not_configured_is_usage_error(tmp_path, capsys, monkeypatch):
    pytest.importorskip("mujoco")
    monkeypatch.delenv("GR00T_POLICY_URL", raising=False)
    monkeypatch.chdir(tmp_path)  # resolve_scans falls back to the repo's scans/
    assert cli.cmd_sim(_ns(tmp_path, room="hero_kitchen", policy="vla")) == cli.EXIT_USAGE
    assert "policy vla" in capsys.readouterr().err


def test_fanout_reports_invalid_merged_dataset(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("arrival.jobs.fanout.run_fanout",
                        lambda rec, cfg, out: {"dataset": str(tmp_path / "ds"), "ran": [0], "skipped": []})
    monkeypatch.setattr("arrival.export.validate.validate", lambda d: ["meta/info.json: missing"])
    a = _ns(tmp_path, backend="local", run_id="r", shards=1)
    assert cli.cmd_fanout(a) == cli.EXIT_INVALID
    assert "INVALID: meta/info.json: missing" in capsys.readouterr().err


def _room(tmp_path):
    import json
    import os
    import shutil

    from conftest import REPO

    scans = tmp_path / "scans"
    shutil.copytree(REPO / "scans" / "hero_kitchen", scans / "hero_kitchen")
    twin = tmp_path / "out" / "twins" / "hero_kitchen" / "twin.json"
    twin.parent.mkdir(parents=True)
    twin.write_text(json.dumps({"cached": True}))
    return scans, twin, scans / "hero_kitchen" / "scan.json", os


def _twin(tmp_path, scans):
    pytest.importorskip("mujoco")
    fams, twin = cli._sim_args(_ns(tmp_path / "out", base="fixed", arm="procedural", room="hero_kitchen", scans=str(scans)))
    return twin


def test_cached_twin_is_used_while_it_is_newer_than_the_scan(tmp_path):
    scans, twin, scan, os = _room(tmp_path)
    os.utime(scan, (1_000_000, 1_000_000))
    assert _twin(tmp_path, scans) == {"cached": True}


def test_cached_twin_is_recompiled_after_the_scan_changes(tmp_path):
    scans, twin, scan, os = _room(tmp_path)
    os.utime(twin, (1_000_000, 1_000_000))
    assert "cached" not in _twin(tmp_path, scans)


def test_sim_exits_1_when_every_task_errors(tmp_path, capsys, monkeypatch):
    """A renderer that cannot start fails every task at build; that run must not exit 0 with an empty dataset."""
    pytest.importorskip("mujoco")
    import arrival.sim.collect as collect

    def broken(*a, **k):
        raise RuntimeError("gladLoadGL error")

    monkeypatch.setattr(collect, "SimEnv", broken)
    monkeypatch.chdir(tmp_path)  # resolve_scans falls back to the repo's scans/
    assert cli.cmd_sim(_ns(tmp_path, room="hero_kitchen")) == cli.EXIT_INVALID
    assert "every task errored" in capsys.readouterr().err

def test_cost_cli_runs_and_reports(tmp_path, capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["cost", "--out", str(tmp_path)])
    rc = cli.cmd_cost(args)
    assert rc == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "| source | room | family |" in out
    assert "| dollars | usd | measured | note |" in out
