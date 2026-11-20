# Sambung Titik dataset tools

Validation and manifest tool for the content in [`../../sambung-titik/`](../../sambung-titik/).
It uses only the **Python 3 standard library**. Run every command from the `dataset-api` repository root, with `python -I` (isolated mode).

## Layout

| Path | Purpose |
|---|---|
| `build.py` | Validates the whole dataset, normalizes the JSON format, writes `sambung-titik/manifest.json`, and updates `ids.lock.json`. Exits non-zero on any violation. |
| `dataset.json` | `datasetVersion` and the review status (`draft` / `reviewed`) of every file. A new file must get a status here. |
| `ids.lock.json` | Every id ever published, written by `build.py`. Do not edit by hand: it is how the build catches a removed id. |

## Commands

```sh
# Validate, normalize, and rebuild the manifest (keeps the current version).
python -I tools/sambung-titik/build.py

# Same, and bump the version. Only written when validation passes; must be strictly higher.
python -I tools/sambung-titik/build.py --version 1.7.0

# Check only: fails when the manifest or a file's format is out of date. Writes nothing.
python -I tools/sambung-titik/build.py --check
```

Violations are printed as `<file>: <message>`.

## What the build checks

- Every file parses, is at most 4 MB, and has `schemaVersion` 1. Every file has a status in `dataset.json`.
- Glyph points are inside 0..1, and every stroke has points.
- Every word uses only letters that have a glyph, and every picture-word has an emoji in `gambar.json`.
- Ids are lowercase, unique, and never disappear: use `"retired": true` instead of deleting.
- `hitung.json`:
  - every zone can produce `soalPos` different questions;
  - answers are single digits.
- `jagoan.json`:
  - practice ids exist;
  - levels never shrink;
  - `nilaiPilihan` never increases;
  - story templates only use `{a}`, `{b}`, `{benda}`.
- `kelompok.json` and `kartu.json` `sampul`:
  - known groups;
  - text lengths;
  - `#RRGGBB` colors.
- `aturan.json`:
  - `minBintangBuka` 1–3;
  - known Papan Bintang label ids, with `semangat` present;
  - each praise list has 1–10 phrases of at most 40 characters.

The app runs the same content checks when it downloads a new version. If one fails, it rejects that version and keeps the previous one.

## Publishing a dataset update

1. Edit `sambung-titik/*.json`.
2. `python -I tools/sambung-titik/build.py --version <strictly higher>`. Installed apps only adopt a **strictly higher** `datasetVersion`, so every publish must bump it.
3. Commit and push to `main`.
4. Purge jsDelivr for the manifest and every changed file:
   ```sh
   curl -s https://purge.jsdelivr.net/gh/KCTOfficial/dataset-api@main/sambung-titik/manifest.json
   curl -s https://purge.jsdelivr.net/gh/KCTOfficial/dataset-api@main/sambung-titik/<file>.json
   ```
   raw GitHub refreshes within about 5 minutes. A stale CDN copy is safe: the app checks every file's SHA-256 against the manifest and falls back to the next CDN.
5. Optional, before an app release: in the `mini-game-pencil` repository run `python tools/dataset/salin.py` to refresh the snapshot bundled in the APK and the HTML prototype.
