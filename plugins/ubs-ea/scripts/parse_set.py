#!/usr/bin/env python3
"""Parse MT5 .set files for the Ultimate Breakout System (UBS) EA. Lines are either:
  Name=value||start||step||stop||optimizeFlag   (numeric/bool input)
  Name=value                                     (string input / separator / comment)
Only the first field after '=' is the live value; rest are optimizer ranges.

Modes:
  parse_set.py FILE.set                     print name=value table for one file
  parse_set.py --csv out.csv FILE1 FILE2 .. wide matrix, one row per file (globs OK, quote them)
  parse_set.py --diff A.set B.set           print only inputs that differ
"""
import sys
import os
import csv
import glob

TIMEFRAME_MAP = {
    0: "CURRENT", 1: "M1", 2: "M2", 3: "M3", 4: "M4", 5: "M5", 6: "M6",
    10: "M10", 12: "M12", 15: "M15", 20: "M20", 30: "M30",
    16385: "H1", 16386: "H2", 16387: "H3", 16388: "H4", 16390: "H6",
    16392: "H8", 16396: "H12", 16408: "D1", 32769: "W1", 49153: "MN1",
}


def read_text(path):
    """Read a .set file: UTF-16 (BOM either order) with UTF-8 fallback for oddballs."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("utf-16")  # no BOM but still UTF-16


def parse_set(path):
    """Return {name: (value, start, step, stop, optimize)}; missing range fields -> None."""
    result = {}
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        name, _, rest = line.partition("=")
        if not name:
            continue  # e.g. "=== d.set (2025.08.27) ===" banner lines (no real input name)
        if name in result:
            print(f"warning: duplicate input {name!r} — last wins", file=sys.stderr)
        parts = rest.split("||") + [None] * 4
        result[name] = tuple(parts[:5])
    return result


def decode_tf(raw_value):
    try:
        n = int(float(raw_value))
    except (TypeError, ValueError):
        return ""
    return TIMEFRAME_MAP.get(n, f"UNKNOWN({n})")


def build_csv(file_list, out_path):
    rows, all_names, seen, failed = [], [], set(), []
    for f in file_list:
        try:
            inputs = parse_set(f)
        except Exception as exc:
            failed.append((f, str(exc)))
            continue
        rows.append((f, inputs))
        for name in inputs:
            if name not in seen:
                seen.add(name)
                all_names.append(name)

    fieldnames = ["file", "folder", "symbol", "entry_tf_decoded", "exit_tf_decoded"]
    for name in all_names:
        fieldnames += [name, name + "__optimize"]

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for f, inputs in rows:
            stem = os.path.splitext(os.path.basename(f))[0]
            row = {
                "file": f,
                "folder": os.path.basename(os.path.dirname(f)),
                "symbol": inputs.get("ForceSymbol", (None,))[0] or stem,
                "entry_tf_decoded": decode_tf(inputs.get("ST1_Timeframe", (None,))[0]),
                "exit_tf_decoded": decode_tf(inputs.get("Exit_Timing", (None,))[0]),
            }
            for name in all_names:
                v = inputs.get(name)
                row[name] = "" if v is None else v[0]
                row[name + "__optimize"] = "" if v is None or v[4] is None else v[4]
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows, {len(all_names)} unique inputs -> {out_path}")
    if failed:
        print(f"FAILED to parse {len(failed)} file(s):")
        for f, err in failed:
            print(f"  {f}: {err}")
    return failed


def cmd_diff(path_a, path_b):
    a, b = parse_set(path_a), parse_set(path_b)
    print(f"{'input':40s} {'A':>20s} {'B':>20s}")
    for name in sorted(set(a) | set(b)):
        va, vb = a.get(name, (None,))[0], b.get(name, (None,))[0]
        if va != vb:
            print(f"{name:40s} {str(va):>20s} {str(vb):>20s}")


def expand_globs(args):
    files = []
    for a in args:
        files.extend(glob.glob(a, recursive=True) if any(c in a for c in "*?[") else [a])
    return files


USAGE = (
    "usage: parse_set.py FILE.set\n"
    "       parse_set.py --csv OUT FILE1 FILE2 ..\n"
    "       parse_set.py --diff A.set B.set"
)


def main(argv):
    if not argv:
        print(USAGE)
        return 1
    if argv[0] == "--csv":
        if len(argv) < 3:
            print(USAGE, file=sys.stderr)
            return 1
        return 1 if build_csv(expand_globs(argv[2:]), argv[1]) else 0
    if argv[0] == "--diff":
        if len(argv) != 3:
            print(USAGE, file=sys.stderr)
            return 1
        cmd_diff(argv[1], argv[2])
        return 0
    for name, (value, start, step, stop, opt) in parse_set(argv[0]).items():
        print(f"{name}={value}  [range {start}/{step}/{stop} opt={opt}]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
