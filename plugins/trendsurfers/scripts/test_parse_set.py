import csv
import subprocess, sys
from pathlib import Path
SCRIPT = Path(__file__).parent / "parse_set.py"

def make_set(tmp_path, name="a.set", body=None):
    lines = body if body is not None else [
        "; saved on 2026.04.17 07:53:42",
        "Risk=0||0||0||20||N",
        "StartLots=0.1||0.01||0.01||1||Y",
        "Sets_Folder=MySets",
        "filters_=--------- trading filters ---------",
    ]
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-16")   # utf-16 writes the BOM
    return p

def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]],
                          capture_output=True, text=True)

def test_parse_basic(tmp_path):
    r = run([make_set(tmp_path)])
    assert r.returncode == 0
    assert "Risk" in r.stdout and "StartLots" in r.stdout and "Sets_Folder" in r.stdout

def test_banner_line_not_an_input(tmp_path):
    p = make_set(tmp_path, body=["Ultimate Breakout System settings", "Risk=0||0||0||20||N"])
    r = run([p])
    assert r.returncode == 0 and "Risk" in r.stdout

def test_diff_reports_changed_input(tmp_path):
    a = make_set(tmp_path, "a.set")
    b = make_set(tmp_path, "b.set",
                 body=["; x", "Risk=0||0||0||20||N", "StartLots=0.2||0.01||0.01||1||Y",
                       "Sets_Folder=MySets", "filters_=---"])
    r = run(["--diff", a, b])
    assert r.returncode == 0 and "StartLots" in r.stdout and "Sets_Folder" not in r.stdout

def test_csv_matrix(tmp_path):
    a, b = make_set(tmp_path, "a.set"), make_set(tmp_path, "b.set")
    out = tmp_path / "m.csv"
    r = run(["--csv", out, a, b])
    assert r.returncode == 0
    with open(out, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    files_seen = {row["file"] for row in rows}
    assert str(a) in files_seen and str(b) in files_seen

def test_duplicate_name_warns(tmp_path):
    p = make_set(tmp_path, body=["Risk=0||0||0||20||N", "Risk=123||0||0||20||N"])
    r = run([p])
    assert r.returncode == 0 and "duplicate" in r.stderr.lower()

def test_missing_args_usage_not_traceback():
    for args in ([], ["--diff"], ["--diff", "only-one.set"], ["--csv"]):
        r = run(args)
        assert r.returncode == 1
        assert "Traceback" not in r.stderr
        assert "usage" in (r.stdout + r.stderr).lower()

def test_reparse_stability(tmp_path):
    p = make_set(tmp_path)
    r1, r2 = run([p]), run([p])
    assert r1.stdout == r2.stdout
