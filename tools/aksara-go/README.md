# AksaraGo dataset tools

Authoring and validation tools for the question bank in [`../../aksara-go/`](../../aksara-go/).
They use only the **Python 3 standard library**: no `pip install`, no third-party packages.
Run every command from the `dataset-api` repository root, with `python -I` (isolated mode).

## Layout

| Path | Purpose |
|---|---|
| `validate.py` | Validates the whole dataset (format, content rules, recomputed answers, manifest). Exits non-zero on any violation. |
| `build_manifest.py` | Rebuilds `aksara-go/manifest.json` from the files on disk and each game's `meta.json` review records. |
| `generate.py` | Generates or extends procedural game files, append-only. |
| `golden_test.py` | Hand-verified known answers (terbilang, arithmetic, Roman numerals, Javanese script, ...). `validate.py` runs these first. |
| `lib/` | Shared code: deterministic JSON I/O, ids, catalog, and the computation libraries used by both generators and the validator. |
| `generators/` | One module per procedural game. |
| `tests/` | Unit and fixture tests: `python -I -m unittest discover -s tools/aksara-go/tests -t tools/aksara-go` |

## Commands

```sh
# Validate everything (runs golden tests first). Exit code 1 on any violation.
python -I tools/aksara-go/validate.py

# Rebuild the manifest after any data change (keeps datasetVersion unless --version is given).
python -I tools/aksara-go/build_manifest.py
python -I tools/aksara-go/build_manifest.py --version 1.1.0

# Golden tests and unit/fixture tests on their own.
python -I tools/aksara-go/golden_test.py
python -I -m unittest discover -s tools/aksara-go/tests -t tools/aksara-go
```

Violations are printed as `<path>#<question id>: <message>`, followed by a per-game count summary.

### Recording a curated review

When a reviewer approves a curated file, add its current SHA-256 (from `manifest.json`) to the game's `meta.json`,
then rebuild the manifest. The file becomes `reviewed`, and it returns to `draft` automatically if it changes later:

```json
"review": {"smp": {"sha256": "<sha256 of kata-baku/smp.json>", "date": "2026-11-01", "role": "guru Bahasa Indonesia"}}
```

## Generating procedural content

```sh
# Generate or extend every procedural game to its default target (append-only).
python -I tools/aksara-go/generate.py

# One game, one segment, a higher target.
python -I tools/aksara-go/generate.py hitung-cepat --segment sd-a --target 150
```

Generation is **append-only**: existing questions and ids are never changed or removed. The candidate stream is
seeded from `gameId:segment` and replayed from the start, so re-running with the same target leaves files
byte-identical, and raising the target only appends questions with new ids. Files stay sorted by
(difficulty, id sequence). Changing a generator therefore only affects questions appended later. To rebuild a
file from scratch you must delete it explicitly, which is only acceptable before that file is first published.
