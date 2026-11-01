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

## Publishing a dataset update

The app (`add-cdn-dataset-client`) reads the dataset from three CDNs, in order: jsDelivr
(`cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/...`), Statically (`cdn.statically.io/gh/...@main/...`),
and raw GitHub (`raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/...`). It only adopts a
manifest whose `datasetVersion` is **strictly higher** than the one it already holds (from a previous sync or
from the snapshot bundled in the APK). One version number therefore always means one content: **every publish
must bump the version**, or installed apps will keep their current data.

1. Validate: `python -I tools/aksara-go/validate.py` must exit 0.
2. Bump the version and rebuild the manifest:
   `python -I tools/aksara-go/build_manifest.py --version <strictly higher, e.g. 1.2.0>`, then validate again.
3. Commit and push to `main`.
4. Purge jsDelivr, which otherwise keeps serving the old `@main` for up to 12 hours. Purge the manifest and every
   changed file:
   ```sh
   curl -s https://purge.jsdelivr.net/gh/KCTOfficial/dataset-api@main/aksara-go/manifest.json
   curl -s https://purge.jsdelivr.net/gh/KCTOfficial/dataset-api@main/aksara-go/<game-id>/<segment>.json
   ```
   raw GitHub refreshes on its own within about 5 minutes. Statically has no purge API. A stale file is still
   safe: the app checks every file's SHA-256 against the manifest and falls back to the next CDN.
5. Optional: refresh the app's bundled snapshot by copying `manifest.json` plus every file it lists into
   `AksaraGo/app/src/main/assets/dataset/aksara-go/`. The app's `DatasetSnapshotTest` fails the build if any
   copied checksum is off.
