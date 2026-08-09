#!/usr/bin/env python3
"""Append-only PortfolioManager backtest job manifest — makes a campaign
resumable across crashes/restarts. campaign.md is the human log; this is the
machine record the orchestrator reconciles against on resume.

This manifest is a local annotation log. PortfolioManager job IDs and
get_backtest_history are the authoritative job state; on any doubt, re-query
PM and reconcile.

One manifest per campaign: <campaign-dir>/manifest.jsonl (one JSON object/line).

Usage:
    # record the exact request BEFORE enqueue (idempotency anchor):
    python campaign_manifest.py <campaign-dir> enqueued --key <idempotencyKey> \
        --spec-file spec.json [--label L]
    # record a state transition returned by PM:
    python campaign_manifest.py <campaign-dir> state --key <idempotencyKey> \
        --job <jobId> --status running|completed|failed|cancelled
    # record collection of a finished report (verifies size, records hash):
    python campaign_manifest.py <campaign-dir> collected --key <idempotencyKey> \
        --job <jobId> --report <path>
    # reconcile on resume — print what is unfinished / unverified:
    python campaign_manifest.py <campaign-dir> reconcile

Records are append-only: a later record supersedes earlier ones for the same
(key, job). reconcile() folds the log to the latest state per key.

Timestamps come from the OS clock here (this is a CLI, not a workflow script).
Report hashing is sha256 of the file bytes; a report smaller than
MIN_REPORT_BYTES is flagged suspect (a ghost/failed MT5 run report is tiny).
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MIN_REPORT_BYTES = 20_000  # ~22KB valid MT5 report; below this is suspect
MANIFEST_NAME = "manifest.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(campaign_dir: Path, record: dict) -> None:
    record["ts"] = now_iso()
    mpath = campaign_dir / MANIFEST_NAME
    mpath.parent.mkdir(parents=True, exist_ok=True)
    with mpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{record['event']} {record.get('key','')} {record.get('job','')}".strip())


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load(campaign_dir: Path) -> list[dict]:
    mpath = campaign_dir / MANIFEST_NAME
    if not mpath.is_file():
        return []
    lines = mpath.read_text(encoding="utf-8").splitlines()
    out = []
    last_index = len(lines) - 1
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            if i == last_index:
                # a torn trailing line means a crash mid-write; skip it rather
                # than lose the whole manifest to one truncated record.
                print(f"WARNING: skipping unparseable trailing line in {mpath} "
                      f"(likely a crash mid-write)", file=sys.stderr)
                continue
            raise
    return out


def reconcile(campaign_dir: Path) -> int:
    """Fold the append-only log to latest state per idempotency key and print an
    action list. Exit non-zero if anything is unfinished or unverified."""
    records = load(campaign_dir)
    if not records:
        print("no manifest — nothing to reconcile")
        return 0

    latest: dict[str, dict] = {}
    for r in records:
        key = r.get("key", "")
        latest.setdefault(key, {"key": key})
        latest[key].update({k: v for k, v in r.items() if k != "ts"})
        latest[key]["last_ts"] = r["ts"]

    problems = 0
    for key, s in latest.items():
        ev, status = s.get("event"), s.get("status")
        report = s.get("report")
        report_ok = s.get("report_ok")
        if ev == "collected" and report_ok:
            print(f"OK    {key}: collected + verified ({report})")
        elif status in ("failed", "cancelled"):
            print(f"DONE  {key}: {status} (terminal, no report expected)")
        elif ev == "collected" and not report_ok:
            print(f"CHECK {key}: report collected but SUSPECT — {report}")
            problems += 1
        elif status in ("completed", "completed_with_warning"):
            print(f"ACT   {key}: PM says {status} but report not collected — collect it")
            problems += 1
        else:
            print(f"ACT   {key}: not terminal (event={ev}, status={status}) — "
                  f"re-query PM by idempotencyKey before re-enqueuing (avoids duplicates)")
            problems += 1
    print(f"\n{len(latest)} keys, {problems} needing action")
    return 1 if problems else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign_dir", type=Path)
    sub = ap.add_subparsers(dest="event", required=True)

    e = sub.add_parser("enqueued")
    e.add_argument("--key", required=True)
    e.add_argument("--spec-file", type=Path, required=True)
    e.add_argument("--label", default=None)

    s = sub.add_parser("state")
    s.add_argument("--key", required=True)
    s.add_argument("--job", required=True)
    s.add_argument("--status", required=True,
                   choices=["pending", "running", "completed", "completed_with_warning",
                            "failed", "cancelled"])

    c = sub.add_parser("collected")
    c.add_argument("--key", required=True)
    c.add_argument("--job", required=True)
    c.add_argument("--report", type=Path, required=True)

    sub.add_parser("reconcile")

    args = ap.parse_args()
    cdir = args.campaign_dir
    if not cdir.is_dir():
        print(f"ERROR: campaign dir not found: {cdir}", file=sys.stderr)
        sys.exit(2)

    if args.event == "enqueued":
        if not args.spec_file.is_file():
            print(f"ERROR: spec file not found: {args.spec_file}", file=sys.stderr)
            sys.exit(2)
        spec = json.loads(args.spec_file.read_text(encoding="utf-8"))
        append(cdir, {"event": "enqueued", "key": args.key, "label": args.label,
                      "request": spec})
    elif args.event == "state":
        append(cdir, {"event": "state", "key": args.key, "job": args.job,
                      "status": args.status})
    elif args.event == "collected":
        rpath = args.report
        size = rpath.stat().st_size if rpath.is_file() else 0
        ok = size >= MIN_REPORT_BYTES
        rec = {"event": "collected", "key": args.key, "job": args.job,
               "report": str(rpath), "report_bytes": size, "report_ok": ok}
        if rpath.is_file():
            rec["report_sha256"] = sha256_file(rpath)
        append(cdir, rec)
        if not ok:
            print(f"WARNING: report is {size} bytes (< {MIN_REPORT_BYTES}) — "
                  f"likely a ghost/failed run, not results", file=sys.stderr)
    elif args.event == "reconcile":
        sys.exit(reconcile(cdir))


if __name__ == "__main__":
    main()
