import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "campaign_manifest.py"


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                           capture_output=True, text=True)


def _spec_file(tmp_path):
    p = tmp_path / "spec.json"
    p.write_text(json.dumps({"symbol": "XAUUSD"}), encoding="utf-8")
    return p


def test_enqueue_appends_jsonl(tmp_path):
    spec = _spec_file(tmp_path)
    r = run([str(tmp_path), "enqueued", "--key", "k1", "--spec-file", str(spec)], tmp_path)
    assert r.returncode == 0
    lines = (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["key"] == "k1"


def test_append_is_append_only(tmp_path):
    spec = _spec_file(tmp_path)
    run([str(tmp_path), "enqueued", "--key", "k1", "--spec-file", str(spec)], tmp_path)
    run([str(tmp_path), "enqueued", "--key", "k2", "--spec-file", str(spec)], tmp_path)
    lines = (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(l)["key"] for l in lines] == ["k1", "k2"]


def test_completed_with_warning_is_accepted_and_needs_collection(tmp_path):
    spec = _spec_file(tmp_path)
    run([str(tmp_path), "enqueued", "--key", "k1", "--spec-file", str(spec)], tmp_path)
    r = run([str(tmp_path), "state", "--key", "k1", "--job", "j1",
             "--status", "completed_with_warning"], tmp_path)
    assert r.returncode == 0, r.stderr
    rec = run([str(tmp_path), "reconcile"], tmp_path)
    assert rec.returncode == 1
    assert "ACT   k1: PM says completed_with_warning but report not collected" in rec.stdout


def test_torn_last_line_tolerated(tmp_path):
    spec = _spec_file(tmp_path)
    run([str(tmp_path), "enqueued", "--key", "k1", "--spec-file", str(spec)], tmp_path)
    run([str(tmp_path), "state", "--key", "k1", "--job", "j1", "--status", "failed"], tmp_path)
    with open(tmp_path / "manifest.jsonl", "a", encoding="utf-8") as fh:
        fh.write('{"key": "torn')   # simulated crash mid-write
    r = run([str(tmp_path), "reconcile"], tmp_path)
    assert r.returncode == 0        # reader skips the torn line, does not crash
