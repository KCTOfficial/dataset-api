"""Rebuild aksara-go/manifest.json from the files on disk and each game's review records."""

import argparse
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

from lib import jsonio, manifest, validator  # noqa: E402

DEFAULT_ROOT = os.path.normpath(os.path.join(TOOLS_DIR, "..", "..", "aksara-go"))


def build_and_write(root, version=None, **flags):
    """Validate (without the manifest check), then write the manifest. Returns (manifest, report)."""
    report = validator.validate(root, check_manifest=False, **flags)
    invalid = {path for path, _, _ in report.violations}
    data = manifest.build(root, invalid, version=version or manifest.existing_version(root))
    jsonio.write(os.path.join(root, "manifest.json"), data)
    return data, report


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Rebuild aksara-go/manifest.json.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="dataset root (default: aksara-go/)")
    parser.add_argument("--version", help="datasetVersion to write (default: keep the current one, else 1.0.0)")
    args = parser.parse_args(argv)
    if args.version and not manifest.SEMVER.match(args.version):
        parser.error("--version must look like 1.2.3")

    data, report = build_and_write(args.root, args.version)
    files = [f for g in data["games"] for f in g["files"]]
    drafts = [f["path"] for f in files if f["status"] == "draft"]
    print(f"manifest.json: {len(data['games'])} games, {len(files)} files, "
          f"{sum(f['questionCount'] for f in files)} questions, datasetVersion {data['datasetVersion']}")
    if drafts:
        print(f"{len(drafts)} draft file(s): {', '.join(drafts)}")
    if report.violations:
        print(f"warning: {len(report.violations)} violation(s); run validate.py for details")
    return 0


if __name__ == "__main__":
    sys.exit(main())
