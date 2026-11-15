# Sambung Titik content

Static JSON content for the Sambung Titik handwriting app (PAUD to grade 3): dot-to-dot letter and number shapes, cards and stages, word banks, missions, and the emoji used as placeholder pictures.

These files are **generated, not edited here**. The source lives in the app repository (`mini-game-pencil/dataset/sambung-titik/`) and is published with:

```sh
# from the mini-game-pencil repository root
python tools/dataset/build.py --terbit ../dataset-api/sambung-titik
```

The build validates the content, writes `manifest.json` with SHA-256 checksums, and refreshes the snapshot bundled in the app and in the HTML prototype, so all three always match.

## Layout

```
sambung-titik/
+-- manifest.json          <- start here: every file with its SHA-256 and review status
+-- glyph/angka.json       <- dot paths for 0-9
+-- glyph/kapital.json     <- dot paths for A-Z
+-- glyph/kecil.json       <- dot paths for a-z
+-- kartu.json             <- cards (Angka, Huruf kecil, Nama Hewan, ...) and their stages
+-- menulis-dasar.json     <- characters per assistance zone for the basic writing cards
+-- kata/<kartu>.json      <- word banks for the picture-word cards
+-- misi.json              <- Jagoan practice: writing missions and quizzes (jenis: susun-kata, susun-kalimat, lengkapi)
+-- gambar.json            <- emoji per word, example word per letter, counting objects
+-- ejaan.json             <- how letters and digits are read aloud
```

## Manifest

```json
{
  "schemaVersion": 1,
  "datasetVersion": "1.0.0",
  "files": [
    { "path": "glyph/kecil.json", "sha256": "…", "status": "reviewed" }
  ]
}
```

- `datasetVersion` is semver. The app only adopts a **strictly higher** version, so every publish must bump it (in `mini-game-pencil/dataset/dataset.json`).
- `status` is `draft` until a teacher has reviewed the file. Release builds hide `draft` files unless a teacher turns on "Tampilkan konten draf".
- Checksums are computed over the exact bytes in this folder (2-space indent, UTF-8, LF, trailing newline). `.gitattributes` keeps line endings LF so they stay valid.

## Data rules

- **Coordinates.** A glyph is a list of strokes in writing order; a stroke is a list of points `[x, y]` or `[x, y, 1]` (a sharp corner). `x` and `y` are in the range 0..1 of the writing area. For lowercase letters the top line is 0.15, the middle line 0.4, the baseline 0.85, and descenders reach 1.
- **Stable ids.** Every card, stage, mission, and mission word has an `id` (lowercase letters, digits, and hyphens). Saved progress is keyed by these ids, so a published id is never renamed or reused for different content. To remove an item, set `"retired": true`; it stops appearing but old progress stays readable.
- `legacyIndex` on stages and missions is the item's position in the original prototype. Only the prototype uses it, for progress saved before ids existed.
- Every word must use only letters that have a glyph in `glyph/kecil.json`, and every picture-word must have an emoji in `gambar.json`. The build rejects the dataset otherwise.

Rules (assistance-level tolerances, scoring, stars, unlocking) and arithmetic question generators are part of the app, not of this dataset.

## CDN URLs

Same pattern as every dataset in this repository, for example:

```
https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/sambung-titik/manifest.json
https://cdn.statically.io/gh/KCTOfficial/dataset-api@main/sambung-titik/manifest.json
https://raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/sambung-titik/manifest.json
```

After pushing, purge jsDelivr for `sambung-titik/manifest.json` and each changed file (see the root README).
