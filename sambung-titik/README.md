# Sambung Titik content

Static JSON content for the Sambung Titik handwriting app (PAUD to grade 3): dot-to-dot letter and number shapes, cards and stages, word banks, missions, the emoji used as placeholder pictures, and the tunable rules (counting posts, Jagoan practice, unlock threshold, Papan Bintang, praise phrases). Changing these files changes the app **without a new app release**.

**This folder is the only source.** Edit the JSON files here, then validate and rebuild the manifest from the `dataset-api` root (see [`tools/sambung-titik/README.md`](../tools/sambung-titik/README.md)):

```sh
python -I tools/sambung-titik/build.py --version <strictly higher version>
```

The build validates the content, normalizes the file format, and writes `manifest.json` with SHA-256 checksums. The app repository keeps only a bundled snapshot, copied from here with `python tools/dataset/salin.py` before an app release.

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
+-- kelas.json             <- profile class options (id + label); misi.json `kelas` refers to these ids
+-- gambar.json            <- emoji per word, example word per letter, counting objects
+-- ejaan.json             <- how letters and digits are read aloud
+-- hitung.json            <- Penjelajah counting cards (Menghitung Benda, Tambah, Kurang): posts and number range per zone
+-- jagoan.json            <- Jagoan rules: Kata & Kalimat practice list and scoring, Berhitung practice list, levels, story templates
+-- kelompok.json          <- texts of the three groups on "Pilih Perjalananmu" (age, short line, spoken explanation)
+-- aturan.json            <- unlock threshold, Papan Bintang targets and labels, praise phrases
+-- suara.json             <- spoken help sentences on the dashboard (for children who cannot read yet)
```

Optional files (`kelas.json`, `hitung.json`, `jagoan.json`, `kelompok.json`, `aturan.json`, `suara.json`) may be missing from older dataset versions; the app then uses built-in defaults identical to the first published values.

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

## Tunable rules

These files hold numbers and texts the team may want to adjust after release. The build and the app both validate them; an invalid file makes the whole dataset version be rejected, and the app keeps the previous one.

### `hitung.json`: Penjelajah counting cards

```json
{ "soalPos": 5,
  "kartu": { "tambah": { "jenis": "tambah",
    "zona": { "krayon": { "pos": 3, "min": 2, "maks": 4, "gambar": true }, "pensil": {…}, "pulpen": {…} } } } }
```

- `soalPos`: questions per post (1–10).
- Per card (`bilang`, `tambah`, `kurang`) and zone: `pos` posts (1–9), answers from `min` to `maks` (single digit, max 9), `gambar` shows fruit pictures.
- The build rejects a zone that cannot produce `soalPos` different questions.

### `jagoan.json`: Jagoan practice

- `kataKalimat`:
  - `latihan`: ordered mission ids from `misi.json`.
  - `soalPerSesi`: questions per session.
  - `pilihan`: answer choices.
  - `ambangNaik`, `ambangTurun`: score % that suggests the next or previous practice.
  - `ambangDuaBintang`: score % for 2 stars.
  - `bonusArah`: 0–30 bonus when every letter is written in the right direction.
- `berhitung`:
  - `latihan`: ordered `{ id, label, ikon }`. `id` is one of `cerita`, `penjumlahan`, `pengurangan`, `perkalian`, `pembagian`. Leaving one out hides it; saved stars are kept.
  - `soalPerMisi`, `minTambahKurang`, `maksPenambah`.
  - `level` (`mudah`, `sedang`, `sulit`): `maksTambahKurang`, `maksKaliBagi`, `penambahSatuDigit`. Levels must not get smaller.
  - `nilaiPilihan`: score for a correct answer on the 1st, 2nd, 3rd+ try, for example `[100, 70, 40]`. Never increasing.
  - `cerita`: story templates with `{a}`, `{b}`, `{benda}` and `op` `+` or `-`.

### `kelompok.json`: group texts

`kenalan` (Pemula), `menulis` (Penjelajah), `jagoan` (Jagoan): `usia` (≤ 20 chars), `ringkas` (≤ 60), `penjelasan` (≤ 300, read aloud). If `penjelasan` is left out for Penjelajah, the app builds it from the card list. Group names stay in the app.

### `suara.json`: spoken help on the dashboard

```json
{ "dashboard": { "sapa": "Halo, {nama}! Ketuk tombol biru, Ayo Main, untuk mulai belajar.",
                 "sapaLanjut": "Atau ketuk Lanjutkan belajar.", "pemula": "Pemula. Kamu sudah melihat {n} dari {total} huruf dan angka.", … } }
```

Sentences the app speaks on the dashboard. The app falls back to its built-in sentence for any missing key.

| key | spoken when | placeholders |
|---|---|---|
| `sapa` | greeting on entering the dashboard (once per profile per app start) or tapping the blue card | `{nama}` |
| `sapaLanjut` | appended to `sapa` when "Lanjutkan belajar" is available | |
| `sapaTanpaNama` | greeting when there is no player yet | |
| `main`, `lanjut`, `buku`, `pemain`, `papan` | tapping Ayo Main!, Lanjutkan belajar, Buku Tulisanku, the player chip, Papan Bintang | |
| `perjalanan`, `karya` | tapping the "Perjalananku" and "Karyaku" headings | |
| `pemula` / `pemulaNol` | tapping the Pemula row (letters seen / none yet) | `{n}`, `{total}` / none |
| `penjelajah` / `penjelajahNol` | tapping the Penjelajah row (writing stars / none yet) | `{n}` / none |
| `jagoan` / `jagoanNol` | tapping the Jagoan row (Jagoan stars / none yet) | `{n}` / none |

### `aturan.json`: unlock threshold, Papan Bintang, praise

```json
{ "minBintangBuka": 2,
  "papanBintang": { "targetPerProfil": 20, "maksLabel": 2,
    "kelebihan": [ { "id": "rajin", "ikon": "✏️", "teks": "Rajin menulis", "min": 10 }, … ] },
  "pujian": { "hebat": ["Hebat!", "Hebat sekali!"], "bagus": […], "cobaLagi": […], "benar": […], "salahHitung": […] } }
```

- **`minBintangBuka`** (1–3) is the stars needed to open the next post, zone, practice, or level. It is also the stars for a "passed" result. Raising it never re-locks content a child already has stars in.
- **`papanBintang`**:
  - `targetPerProfil` (1–200): the shared jar target is this × number of profiles.
  - `maksLabel` (1–4): labels shown per child.
  - `kelebihan`: labels in priority order. Ids:

    | id | earned when |
    |---|---|
    | `rajin` | ≥ `min` writings this week, or the most writings among profiles |
    | `teliti` | ≥ `min` practices and ≥ `persen`% correct |
    | `tekun` | played on ≥ `min` days |
    | `susun` | ≥ `min` correct arrange answers |
    | `hitung` | ≥ `min` counting sessions |
    | `kenal` | ≥ `min` letters or digits seen in Pemula |
    | `semangat` | fallback when nothing else applies (required) |

  - `teks` may use `{n}` for the number (≤ 30 chars).
  - Leaving an id out hides that label.
- **`pujian`**: each situation lists 1–10 phrases (≤ 40 chars). The app picks one at random each time.
  - `hebat`: 3 stars or passed.
  - `bagus`: 2 stars.
  - `cobaLagi`: not passed.
  - `benar`: correct counting answer.
  - `salahHitung`: wrong counting answer.

What stays in the app:
- writing tolerances and stroke scoring;
- question generators;
- the meaning of each label id and practice id;
- screen layout.

## CDN URLs

Same pattern as every dataset in this repository, for example:

```
https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/sambung-titik/manifest.json
https://cdn.statically.io/gh/KCTOfficial/dataset-api@main/sambung-titik/manifest.json
https://raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/sambung-titik/manifest.json
```

After pushing, purge jsDelivr for `sambung-titik/manifest.json` and each changed file (see the root README).
