"""Validate the whole AksaraGo dataset. Exits 1 on any violation (or failing golden test)."""

import argparse
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from lib import validator  # noqa: E402

DEFAULT_ROOT = os.path.normpath(os.path.join(TOOLS_DIR, "..", "..", "aksara-go"))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate the AksaraGo question dataset.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="dataset root (default: aksara-go/)")
    args = parser.parse_args(argv)

    import golden_test

    if not golden_test.run_golden():
        print("golden tests failed: refusing to validate the dataset", file=sys.stderr)
        return 1

    report = validator.validate(args.root)
    for line in report.lines():
        print(line)
    print()
    total = 0
    for game_id in sorted(report.counts):
        per_segment = report.counts[game_id]
        game_total = sum(per_segment.values())
        total += game_total
        detail = ", ".join(f"{s}={n}" for s, n in per_segment.items())
        print(f"{game_id:18} {game_total:5}  ({detail})")
    print(f"{'TOTAL':18} {total:5}")
    print(f"\n{len(report.violations)} violation(s)" if report.violations else "\nOK: no violations")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
