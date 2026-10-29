"""CLI: python -m lead_leak_check {check FILE.json | describe "text" | history FILE.csv [--interval MIN] | serve}"""
from __future__ import annotations

import argparse
import json
import sys

from .rules import analyze_history, check_config, check_description


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lead-leak-check")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a JSON pipeline config"); c.add_argument("file")
    d = sub.add_parser("describe", help="check a plain-English description"); d.add_argument("text")
    h = sub.add_parser("history", help="analyze a run-history CSV"); h.add_argument("file"); h.add_argument("--interval", type=float)
    sub.add_parser("serve", help="run the MCP server on stdio")
    p.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    a = p.parse_args(argv)
    if a.cmd == "serve":
        from .server import main as serve
        serve(); return 0
    if a.cmd == "check":
        rep = check_config(json.load(open(a.file)))
    elif a.cmd == "describe":
        rep = check_description(a.text)
    else:
        rep = analyze_history(open(a.file).read(), a.interval)
    print(json.dumps(rep.as_dict(), indent=2) if a.json else rep.markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
