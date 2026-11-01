# dataset-api

Static JSON datasets from KCT, served as a free, read-only **API over public CDNs**. There is no server to run: every file in this repository is reachable through jsDelivr, Statically, and raw GitHub as soon as it is pushed to `main`.

| Dataset | Folder | What it contains | Format docs |
|---|---|---|---|
| AksaraGo question bank | [`aksara-go/`](aksara-go/) | 4,718 questions and answers across 15 learning games for SD, SMP, and SMA (dataset version 1.1.0) | [`aksara-go/README.md`](aksara-go/README.md) |

The numbers above are a snapshot. [`aksara-go/manifest.json`](aksara-go/manifest.json) is always the source of truth for which files exist, their question counts, SHA-256 checksums, and review status.

---

## Getting a CDN URL for any file

Every file has one canonical GitHub URL:

```
https://github.com/KCTOfficial/dataset-api/blob/main/<path-to-file>.json
```

From it, three CDN URLs serve the same file:

| # | CDN | URL pattern | Freshness after a push |
|---|---|---|---|
| 1 | jsDelivr | `https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/<path>` | Up to 12 hours at the edge, unless purged (see [Publishing](#publishing-changes)) |
| 2 | Statically | `https://cdn.statically.io/gh/KCTOfficial/dataset-api@main/<path>` | Cached; no purge API. **Blocked by some Indonesian ISPs** (DNS redirects it to a block host) |
| 3 | raw GitHub | `https://raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/<path>` | About 5 minutes. Served as `text/plain`, so parse the body as JSON regardless of `Content-Type` |

**Example** for `aksara-go/aksara-nusantara/sd-b.json`:

```
https://github.com/KCTOfficial/dataset-api/blob/main/aksara-go/aksara-nusantara/sd-b.json   (canonical)
https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/aksara-go/aksara-nusantara/sd-b.json
https://cdn.statically.io/gh/KCTOfficial/dataset-api@main/aksara-go/aksara-nusantara/sd-b.json
https://raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/aksara-go/aksara-nusantara/sd-b.json
```

### Generate the links with GitCDN Generator

[**GitCDN Generator**](https://gitcdn-generator.vercel.app/) turns a GitHub file URL into these CDN URLs, so you don't have to build them by hand:

1. Open a JSON file in this repository on GitHub and copy its URL. It must contain `/blob/` and end with `.json`, e.g. `https://github.com/KCTOfficial/dataset-api/blob/main/aksara-go/manifest.json`.
2. Paste it into [gitcdn-generator.vercel.app](https://gitcdn-generator.vercel.app/).
3. Copy the jsDelivr, Statically, or raw GitHub URL it generates.

You can also open the generator with the URL pre-filled by passing it, URL-encoded, as the `q` parameter:

```
https://gitcdn-generator.vercel.app/?q=<URL-encoded GitHub file URL>
```

Ready-made links for the main entry points:

- [`aksara-go/manifest.json`](https://gitcdn-generator.vercel.app/?q=https%3A%2F%2Fgithub.com%2FKCTOfficial%2Fdataset-api%2Fblob%2Fmain%2Faksara-go%2Fmanifest.json) — start here: lists every game and file
- [`aksara-go/hitung-cepat/meta.json`](https://gitcdn-generator.vercel.app/?q=https%3A%2F%2Fgithub.com%2FKCTOfficial%2Fdataset-api%2Fblob%2Fmain%2Faksara-go%2Fhitung-cepat%2Fmeta.json) — one game's title, instruction, and segments
- [`aksara-go/aksara-nusantara/sd-b.json`](https://gitcdn-generator.vercel.app/?q=https%3A%2F%2Fgithub.com%2FKCTOfficial%2Fdataset-api%2Fblob%2Fmain%2Faksara-go%2Faksara-nusantara%2Fsd-b.json) — one segment's questions

---

## Using the API in an app

### Quick check

```sh
curl -s https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/aksara-go/manifest.json | head -c 300
```

### Recommended client behavior

The CDNs are not equally reliable for every user, so a client should not depend on a single URL:

1. **Try the CDNs in order** (jsDelivr, then Statically, then raw GitHub). Move to the next one on a connection error or timeout (keep the connect timeout short, about 5 s), on a non-2xx status, or on an invalid body.
2. **Validate the body.** It must parse as a JSON object or array. An ISP block page can arrive with HTTP 200 and an HTML body; treat that as a failure.
3. **Read `manifest.json` first, then verify each file** against its `sha256` in the manifest. A mismatch means that CDN still holds an older copy, so try the next CDN.
4. **Only adopt a newer `datasetVersion`.** Ignore a manifest whose version is equal to or lower than the one you already have, since a stale CDN edge can serve an old manifest.
5. **Cache what you verified** and keep using it when every CDN is unreachable.

Minimal fallback in JavaScript:

```js
const CDNS = [
  (path) => `https://cdn.jsdelivr.net/gh/KCTOfficial/dataset-api@main/${path}`,
  (path) => `https://cdn.statically.io/gh/KCTOfficial/dataset-api@main/${path}`,
  (path) => `https://raw.githubusercontent.com/KCTOfficial/dataset-api/refs/heads/main/${path}`,
];

async function fetchDataset(path) {
  for (const cdn of CDNS) {
    try {
      const res = await fetch(cdn(path), { signal: AbortSignal.timeout(5000) });
      if (!res.ok) continue;
      const data = JSON.parse(await res.text()); // raw GitHub sends text/plain; block pages fail here
      if (data !== null && typeof data === "object") return data;
    } catch {
      // network error, timeout, or invalid JSON: try the next CDN
    }
  }
  throw new Error(`All CDNs failed for ${path}`);
}

const manifest = await fetchDataset("aksara-go/manifest.json");
```

The AksaraGo Android app implements all five rules (including SHA-256 verification and an offline snapshot bundled in the APK) in its CDN client.

---

## Repository layout

```
dataset-api/
+-- aksara-go/                 # AksaraGo question bank (served data only)
|   +-- manifest.json          # every game and file, with counts, SHA-256, and review status
|   +-- README.md              # data format: segments, question envelope, interactions
|   +-- <game-id>/
|       +-- meta.json          # title, instruction, category, interaction, segments
|       +-- <segment>.json     # sd-a, sd-b, sd-c, smp, sma
+-- tools/aksara-go/           # validator, manifest builder, generators (Python 3, stdlib only)
+-- .gitattributes             # keeps JSON line endings LF so checksums stay stable
```

## Publishing changes

Data changes go through the tools in [`tools/aksara-go/`](tools/aksara-go/README.md):

1. `python -I tools/aksara-go/validate.py` must exit 0.
2. Bump the version: `python -I tools/aksara-go/build_manifest.py --version <higher, e.g. 1.2.0>`. Apps only pick up a strictly higher `datasetVersion`.
3. Commit and push to `main`.
4. Purge jsDelivr for the manifest and each changed file, e.g. `curl -s https://purge.jsdelivr.net/gh/KCTOfficial/dataset-api@main/aksara-go/manifest.json`.

See [Publishing a dataset update](tools/aksara-go/README.md#publishing-a-dataset-update) for details.

## Notes

- The repository is public, so all answers are publicly readable. That is intended for learning content; the datasets contain no personal data or secrets.
- Curated (hand-written) files are marked `draft` in the manifest until a human review is recorded; machine-generated, machine-verified files are `reviewed`. Clients decide whether to show drafts.
