from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo import format_demo, run_demo
from .ledger import HashLedger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="latch", description="Governed adoption and reliance for AI-generated judgement.")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run the bounded candidate -> adoption -> reliance demo.")
    demo.add_argument("--ledger", default=None, help="Optional JSONL path for durable demo evidence.")

    verify = sub.add_parser("verify", help="Verify a Latch JSONL ledger hash chain.")
    verify.add_argument("ledger", help="Path to ledger JSONL.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        print(format_demo(run_demo(args.ledger)))
        return
    if args.command == "verify":
        ledger = HashLedger(Path(args.ledger))
        ok, message = ledger.verify()
        print(json.dumps({"ok": ok, "message": message}, indent=2))
        raise SystemExit(0 if ok else 1)
