"""Validasi dan buat manifest dataset Sambung Titik (sumber satu-satunya: sambung-titik/ di repo ini).

File:
  sambung-titik/*.json                 konten; diedit langsung di sini
  sambung-titik/manifest.json          dibuat oleh skrip ini (checksum SHA-256 dan status)
  tools/sambung-titik/dataset.json     versi dataset dan status draft/reviewed per file
  tools/sambung-titik/ids.lock.json    semua id yang pernah terbit (dibuat skrip ini, jangan diedit manual)

Pemakaian (dari akar repo dataset-api):
  python -I tools/sambung-titik/build.py                   validasi, rapikan format, tulis manifest
  python -I tools/sambung-titik/build.py --version 1.7.0   sama, sekaligus menaikkan versi
  python -I tools/sambung-titik/build.py --check           hanya memeriksa; gagal kalau ada yang belum diperbarui
Format file: indent 2, UTF-8 tanpa BOM, LF, baris baru di akhir (sama dengan tools/aksara-go/lib/jsonio).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sambung-titik"
TOOLS = ROOT / "tools" / "sambung-titik"
CONFIG = TOOLS / "dataset.json"
LOCK = TOOLS / "ids.lock.json"
ZONES = ("krayon", "pensil", "pulpen")
JENIS_LATIHAN = ("tulis", "susun-kata", "susun-kalimat", "lengkapi")
GLYPH_SETS = ("angka", "kapital", "kecil")
SUPPORTED_SCHEMA = 1
MAX_FILE_BYTES = 4 * 1024 * 1024
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
# Jenis latihan Berhitung Jagoan yang dikenal aplikasi (Berhitung.MisiHitung); dataset mengatur urutan, nama, ikon.
JENIS_HITUNG_JAGOAN = ("cerita", "penjumlahan", "pengurangan", "perkalian", "pembagian")
KELOMPOK = ("kenalan", "menulis", "jagoan")
# Label kelebihan Papan Bintang yang dikenal aplikasi (AturanPapan); dataset mengatur urutan, syarat, ikon, teks.
KELEBIHAN = ("rajin", "teliti", "tekun", "susun", "hitung", "kenal", "semangat")
PUJIAN = ("hebat", "bagus", "cobaLagi", "benar", "salahHitung")


class Problems:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, where: str, msg: str) -> None:
        self.items.append(f"{where}: {msg}")


def load(rel: str) -> dict:
    return json.loads((SRC / rel).read_text(encoding="utf-8"))


def check_glyphs(p: Problems, data: dict[str, dict]) -> dict[str, set[str]]:
    chars: dict[str, set[str]] = {}
    for s in GLYPH_SETS:
        rel = f"glyph/{s}.json"
        doc = data[rel]
        if doc.get("set") != s:
            p.add(rel, f"set harus '{s}'")
        chars[s] = set()
        for ch, strokes in doc.get("glyphs", {}).items():
            chars[s].add(ch)
            if not isinstance(strokes, list) or not strokes:
                p.add(rel, f"glyph '{ch}' tidak punya goresan")
                continue
            for i, stroke in enumerate(strokes):
                if not isinstance(stroke, list) or not stroke:
                    p.add(rel, f"glyph '{ch}' goresan {i + 1} kosong")
                    continue
                for pt in stroke:
                    ok = isinstance(pt, list) and len(pt) in (2, 3) and all(isinstance(v, (int, float)) for v in pt)
                    if not ok:
                        p.add(rel, f"glyph '{ch}' titik tidak sah: {pt}")
                    elif not (0 <= pt[0] <= 1 and 0 <= pt[1] <= 1):
                        p.add(rel, f"glyph '{ch}' titik di luar 0..1: {pt}")
                    elif len(pt) == 3 and pt[2] != 1:
                        p.add(rel, f"glyph '{ch}' penanda belok harus 1: {pt}")
    return chars


def check_writable(p: Problems, where: str, text: str, kecil: set[str]) -> None:
    bad = sorted({c for c in text if c not in " -" and c not in kecil})
    if bad:
        p.add(where, f"'{text}' memakai huruf tanpa glyph: {' '.join(bad)}")


def unique(p: Problems, where: str, ids: list[str]) -> None:
    seen: set[str] = set()
    for i in ids:
        if not ID_RE.match(i):
            p.add(where, f"id tidak sah: '{i}' (huruf kecil, angka, tanda hubung)")
        if i in seen:
            p.add(where, f"id ganda: '{i}'")
        seen.add(i)


def collect_ids(p: Problems, data: dict[str, dict], chars: dict[str, set[str]]) -> dict[str, list[str]]:
    """Semua id per ruang nama, dan validasi isi yang merujuk ke glyph."""
    ids: dict[str, list[str]] = {}
    kecil = chars["kecil"]

    kartu = data["kartu.json"]["kartu"]
    unique(p, "kartu.json", [k["id"] for k in kartu])
    ids["kartu"] = [k["id"] for k in kartu if not k.get("retired")]
    ids["kartu.all"] = [k["id"] for k in kartu]
    for k in kartu:
        stages = k.get("stages", [])
        unique(p, f"kartu.json {k['id']}", [s["id"] for s in stages])
        ids[f"stage.{k['id']}"] = [s["id"] for s in stages]
        for s in stages:
            glyph_set = "angka" if k["id"] == "angka" else k["id"]
            for ch in s.get("chars", []):
                if glyph_set in chars and ch not in chars[glyph_set]:
                    p.add("kartu.json", f"stage {k['id']}/{s['id']} memakai '{ch}' tanpa glyph")

    dasar = data["menulis-dasar.json"]
    for cat, zones in dasar["zona"].items():
        for z, lst in zones.items():
            if z not in ZONES:
                p.add("menulis-dasar.json", f"zona tidak dikenal: {z}")
            for ch in lst:
                if ch not in chars.get(cat, set()):
                    p.add("menulis-dasar.json", f"{cat}/{z} memakai '{ch}' tanpa glyph")

    for rel, doc in data.items():
        if not rel.startswith("kata/"):
            continue
        words: set[str] = set()
        groups = [doc.get("zona", {})] if doc["mode"] == "tetap" else [doc.get("pool", {}), doc.get("wajib", {})]
        for g in groups:
            for z, lst in g.items():
                if z not in ZONES:
                    p.add(rel, f"zona tidak dikenal: {z}")
                for w in lst:
                    words.add(w)
                    check_writable(p, rel, w, kecil)
                    if w not in data["gambar.json"]["pic"]:
                        p.add(rel, f"kata '{w}' tidak punya gambar di gambar.json")
        if doc["mode"] == "acak":
            for z, n in doc["jumlah"].items():
                if n > len(doc["pool"].get(z, [])):
                    p.add(rel, f"zona {z} butuh {n} kata, pool hanya {len(doc['pool'].get(z, []))}")
                for w in doc.get("wajib", {}).get(z, []):
                    if w not in doc["pool"].get(z, []):
                        p.add(rel, f"kata wajib '{w}' tidak ada di pool zona {z}")
        ids[f"kata.{doc['kartu']}"] = sorted(words)

    check_hitung(p, data)
    check_jagoan(p, data)
    check_tampilan(p, data)
    check_aturan(p, data)

    # Daftar kelas (kelas.json): id angka unik dan label; dirujuk oleh `kelas` di misi.json dan kelas profil.
    kelas_ids: set[int] = set()
    for k in data.get("kelas.json", {}).get("kelas", []):
        if not isinstance(k.get("id"), int) or k["id"] in kelas_ids:
            p.add("kelas.json", f"id kelas harus angka unik: {k.get('id')}")
        if not str(k.get("label", "")).strip():
            p.add("kelas.json", f"kelas {k.get('id')} tanpa label")
        kelas_ids.add(k.get("id"))

    misi = data["misi.json"]["misi"]
    unique(p, "misi.json", [m["id"] for m in misi])
    idx = [m["legacyIndex"] for m in misi]
    if sorted(idx) != list(range(len(idx))):
        p.add("misi.json", "legacyIndex harus 0..n-1 tanpa celah")
    ids["misi"] = [m["id"] for m in misi]
    for m in misi:
        unique(p, f"misi.json {m['id']}", [w["id"] for w in m["words"]])
        ids[f"misi.{m['id']}"] = [w["id"] for w in m["words"]]
        jenis = m.get("jenis", "tulis")
        if jenis not in JENIS_LATIHAN:
            p.add(f"misi.json {m['id']}", f"jenis tidak dikenal: {jenis}")
        for k in m.get("kelas", []):
            if k not in kelas_ids:
                p.add(f"misi.json {m['id']}", f"kelas {k} tidak ada di kelas.json")
        for w in m["words"]:
            if w.get("retired"):
                continue
            where = f"misi.json {m['id']} '{w['text']}'"
            check_writable(p, f"misi.json {m['id']}", w["text"], kecil)
            # Latihan soal (feature-jagoan-latihan-soal): 2 sampai 4 kepingan. Kata dengan kepingan kembar
            # ("su-su") tetap sah untuk menulis, tapi dilewati aplikasi saat membuat soal susun (tidak bisa diacak).
            if jenis == "susun-kata" and not 2 <= len(w["text"].split("-")) <= 4:
                p.add(where, "susun kata butuh 2 sampai 4 suku kata")
            elif jenis == "susun-kalimat" and not 2 <= len(w["text"].split()) <= 4:
                p.add(where, "susun kalimat butuh 2 sampai 4 kata")
            elif jenis == "lengkapi":
                kata = w["text"].split()
                pengecoh = w.get("pengecoh", [])
                if w.get("blank") not in kata:
                    p.add(where, "blank harus salah satu kata di kalimat")
                if len(pengecoh) < 2 or w.get("blank") in pengecoh or len(set(pengecoh)) != len(pengecoh):
                    p.add(where, "lengkapi butuh minimal 2 pengecoh yang berbeda dari jawaban")
                for x in pengecoh:
                    check_writable(p, where, x, kecil)
    return ids


def soal_unik(jenis: str, lo: int, hi: int, buah: int) -> int:
    """Jumlah soal berbeda yang bisa dibuat satu pos (kunci soal sama dengan Berhitung.soalPos di aplikasi)."""
    if jenis == "hitung":
        return (hi - lo + 1) * buah            # kunci: jumlah + nama buah
    return sum(n - 1 for n in range(lo, hi + 1))  # tambah: a+b=n, kurang: n-b, dengan a, b >= 1


def check_hitung(p: Problems, data: dict[str, dict]) -> None:
    """hitung.json (feature-penjelajah-tiga-pos): aturan pos kartu hitung Penjelajah."""
    kartu_hitung = {k["id"] for k in data["kartu.json"]["kartu"] if k.get("hitung") and not k.get("retired")}
    doc = data.get("hitung.json")
    if doc is None:
        if kartu_hitung:
            p.add("hitung.json", f"tidak ada, padahal kartu.json punya kartu hitung: {', '.join(sorted(kartu_hitung))}")
        return
    rel = "hitung.json"
    soal = doc.get("soalPos")
    if not isinstance(soal, int) or not 1 <= soal <= 10:
        p.add(rel, f"soalPos harus angka 1 sampai 10: {soal}")
        soal = 1
    buah = len(data["gambar.json"].get("buahHitung", []))
    aturan = doc.get("kartu", {})
    for kid in sorted(kartu_hitung - set(aturan)):
        p.add(rel, f"kartu hitung '{kid}' belum punya aturan")
    for kid, k in aturan.items():
        where = f"{rel} {kid}"
        if kid not in kartu_hitung:
            p.add(where, "tidak ada di kartu.json sebagai kartu hitung (hitung: true)")
        jenis = k.get("jenis")
        if jenis not in ("hitung", "tambah", "kurang"):
            p.add(where, f"jenis harus hitung, tambah, atau kurang: {jenis}")
            continue
        zona = k.get("zona", {})
        if sorted(zona) != sorted(ZONES):
            p.add(where, f"zona harus tepat {', '.join(ZONES)}")
        for z, r in zona.items():
            wz = f"{where}/{z}"
            pos, lo, hi = r.get("pos"), r.get("min"), r.get("maks")
            if not isinstance(pos, int) or not 1 <= pos <= 9:
                p.add(wz, f"pos harus angka 1 sampai 9: {pos}")
            if not isinstance(r.get("gambar"), bool):
                p.add(wz, "gambar harus true atau false")
            if not all(isinstance(v, int) for v in (lo, hi)):
                p.add(wz, "min dan maks harus angka")
                continue
            # Jawaban ditulis satu digit; tambah dan kurang butuh dua bilangan >= 1 (angka 1 tidak bisa dipecah).
            terkecil = 1 if jenis == "hitung" else 2
            if not terkecil <= lo <= hi <= 9:
                p.add(wz, f"butuh {terkecil} <= min <= maks <= 9 (sekarang {lo} sampai {hi})")
                continue
            n = soal_unik(jenis, lo, hi, buah)
            if n < soal:
                p.add(wz, f"hanya {n} soal berbeda, kurang dari soalPos {soal}")


def check_jagoan(p: Problems, data: dict[str, dict]) -> None:
    """jagoan.json (feature-jagoan-dataset): daftar latihan Kata & Kalimat dan aturan Berhitung Jagoan."""
    doc = data.get("jagoan.json")
    if doc is None:
        return
    rel = "jagoan.json"

    def angka(where: str, v, lo: int, hi: int) -> bool:
        if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
            p.add(rel, f"{where} harus angka {lo} sampai {hi}: {v}")
            return False
        return True

    kk = doc.get("kataKalimat", {})
    misi = {m["id"]: m for m in data["misi.json"]["misi"]}
    latihan = kk.get("latihan", [])
    if not latihan:
        p.add(rel, "kataKalimat.latihan kosong")
    if len(set(latihan)) != len(latihan):
        p.add(rel, "kataKalimat.latihan punya id kembar")
    for i in latihan:
        if i not in misi:
            p.add(rel, f"kataKalimat.latihan: '{i}' tidak ada di misi.json")
        elif misi[i].get("retired"):
            p.add(rel, f"kataKalimat.latihan: '{i}' sudah retired")
    angka("kataKalimat.soalPerSesi", kk.get("soalPerSesi"), 1, 10)
    angka("kataKalimat.pilihan", kk.get("pilihan"), 2, 4)
    ok = [angka(f"kataKalimat.{k}", kk.get(k), 0, 100) for k in ("ambangNaik", "ambangTurun", "ambangDuaBintang")]
    if all(ok) and kk["ambangTurun"] > kk["ambangNaik"]:
        p.add(rel, "kataKalimat.ambangTurun lebih besar dari ambangNaik")

    bh = doc.get("berhitung", {})
    angka("berhitung.soalPerMisi", bh.get("soalPerMisi"), 1, 10)
    ok_min = angka("berhitung.minTambahKurang", bh.get("minTambahKurang"), 2, 99)
    ok_pen = angka("berhitung.maksPenambah", bh.get("maksPenambah"), 1, 9)
    # Penambah satu digit: bilangan lain = hasil - penambah harus tetap >= 1.
    if ok_min and ok_pen and bh["minTambahKurang"] <= bh["maksPenambah"]:
        p.add(rel, "berhitung.minTambahKurang harus lebih besar dari maksPenambah")
    level = bh.get("level", {})
    urut = ("mudah", "sedang", "sulit")
    if sorted(level) != sorted(urut):
        p.add(rel, f"berhitung.level harus tepat {', '.join(urut)}")
    sebelum: dict | None = None
    for nama in urut:
        lv = level.get(nama)
        if lv is None:
            continue
        w = f"berhitung.level.{nama}"
        ok_tk = angka(f"{w}.maksTambahKurang", lv.get("maksTambahKurang"), 2, 99)
        ok_kb = angka(f"{w}.maksKaliBagi", lv.get("maksKaliBagi"), 9, 81)  # faktor 9 harus tetap punya pasangan >= 1
        if not isinstance(lv.get("penambahSatuDigit"), bool):
            p.add(rel, f"{w}.penambahSatuDigit harus true atau false")
        if ok_tk and ok_min and lv["maksTambahKurang"] < bh["minTambahKurang"]:
            p.add(rel, f"{w}.maksTambahKurang lebih kecil dari minTambahKurang")
        if ok_tk and ok_kb and sebelum is not None:
            if lv["maksTambahKurang"] < sebelum["maksTambahKurang"] or lv["maksKaliBagi"] < sebelum["maksKaliBagi"]:
                p.add(rel, f"{w}: batas lebih kecil dari level sebelumnya")
        if ok_tk and ok_kb:
            sebelum = lv
    # Daftar latihan Berhitung (feature-dataset-lanjutan): jenis soal tetap di aplikasi, dataset mengatur urutan, nama, ikon.
    latihan_h = bh.get("latihan", [])
    if not latihan_h:
        p.add(rel, "berhitung.latihan kosong")
    ids_h = [x.get("id") for x in latihan_h]
    if len(set(ids_h)) != len(ids_h):
        p.add(rel, "berhitung.latihan punya id kembar")
    for x in latihan_h:
        if x.get("id") not in JENIS_HITUNG_JAGOAN:
            p.add(rel, f"berhitung.latihan: id '{x.get('id')}' tidak dikenal ({', '.join(JENIS_HITUNG_JAGOAN)})")
        if not str(x.get("label", "")).strip() or len(str(x.get("label"))) > 30:
            p.add(rel, f"berhitung.latihan {x.get('id')}: label kosong atau lebih dari 30 karakter")
        if not str(x.get("ikon", "")).strip():
            p.add(rel, f"berhitung.latihan {x.get('id')}: ikon kosong")
    nilai = bh.get("nilaiPilihan", [])
    if not (isinstance(nilai, list) and 1 <= len(nilai) <= 4 and all(isinstance(v, int) and 0 <= v <= 100 for v in nilai)):
        p.add(rel, "berhitung.nilaiPilihan harus 1 sampai 4 angka 0 sampai 100")
    elif any(a < b for a, b in zip(nilai, nilai[1:])):
        p.add(rel, "berhitung.nilaiPilihan tidak boleh naik (percobaan berikutnya bernilai lebih kecil atau sama)")
    angka("kataKalimat.bonusArah", kk.get("bonusArah"), 0, 30)
    cerita = bh.get("cerita", [])
    if not cerita:
        p.add(rel, "berhitung.cerita kosong")
    for i, c in enumerate(cerita, 1):
        if c.get("op") not in ("+", "-"):
            p.add(rel, f"berhitung.cerita {i}: op harus + atau -")
        teks = c.get("teks", "")
        if "{a}" not in teks or "{b}" not in teks:
            p.add(rel, f"berhitung.cerita {i}: teks harus memuat {{a}} dan {{b}}")
        sisa = re.sub(r"\{(a|b|benda)\}", "", teks)
        if "{" in sisa or "}" in sisa:
            p.add(rel, f"berhitung.cerita {i}: penanda yang dikenal hanya {{a}}, {{b}}, {{benda}}")


def check_tampilan(p: Problems, data: dict[str, dict]) -> None:
    """kelompok.json dan sampul kartu (feature-dataset-lanjutan)."""
    doc = data.get("kelompok.json")
    if doc is not None:
        batas = {"usia": 20, "ringkas": 60, "penjelasan": 300}
        for gid, g in doc.get("kelompok", {}).items():
            w = f"kelompok.json {gid}"
            if gid not in KELOMPOK:
                p.add(w, f"kelompok tidak dikenal ({', '.join(KELOMPOK)})")
            for f, n in batas.items():
                v = g.get(f)
                if v is None and f == "penjelasan":
                    continue  # boleh kosong: Penjelajah dibuat dari daftar kartu, lainnya memakai teks bawaan
                if not isinstance(v, str) or not v.strip() or len(v) > n:
                    p.add(w, f"{f} harus teks 1 sampai {n} karakter")
    for k in data["kartu.json"]["kartu"]:
        s = k.get("sampul")
        if s is None:
            continue
        for f in ("bg", "ink", "bayangan"):
            if not isinstance(s.get(f), str) or not HEX_RE.match(s[f]):
                p.add("kartu.json", f"{k['id']}: sampul.{f} harus warna #RRGGBB")


def check_aturan(p: Problems, data: dict[str, dict]) -> None:
    """aturan.json (feature-aturan-dataset): ambang buka, Papan Bintang, kalimat pujian."""
    doc = data.get("aturan.json")
    if doc is None:
        return
    rel = "aturan.json"

    def angka(where: str, v, lo: int, hi: int) -> None:
        if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
            p.add(rel, f"{where} harus angka {lo} sampai {hi}: {v}")

    angka("minBintangBuka", doc.get("minBintangBuka"), 1, 3)
    pb = doc.get("papanBintang", {})
    angka("papanBintang.targetPerProfil", pb.get("targetPerProfil"), 1, 200)
    angka("papanBintang.maksLabel", pb.get("maksLabel"), 1, 4)
    ids = [k.get("id") for k in pb.get("kelebihan", [])]
    if len(set(ids)) != len(ids):
        p.add(rel, "papanBintang.kelebihan punya id kembar")
    if "semangat" not in ids:
        p.add(rel, "papanBintang.kelebihan wajib punya 'semangat' (label cadangan)")
    for k in pb.get("kelebihan", []):
        w = f"papanBintang.kelebihan {k.get('id')}"
        if k.get("id") not in KELEBIHAN:
            p.add(rel, f"{w}: id tidak dikenal ({', '.join(KELEBIHAN)})")
        angka(f"{w}.min", k.get("min"), 1, 1000)
        if k.get("id") == "teliti":
            angka(f"{w}.persen", k.get("persen"), 1, 100)
        t = k.get("teks")
        if not isinstance(t, str) or not t.strip() or len(t) > 30:
            p.add(rel, f"{w}: teks harus 1 sampai 30 karakter")
        elif "{" in t.replace("{n}", ""):
            p.add(rel, f"{w}: penanda yang dikenal hanya {{n}}")
        if not isinstance(k.get("ikon"), str) or not k["ikon"].strip():
            p.add(rel, f"{w}: ikon kosong")
    pj = doc.get("pujian", {})
    for key in PUJIAN:
        v = pj.get(key)
        if not isinstance(v, list) or not 1 <= len(v) <= 10:
            p.add(rel, f"pujian.{key} harus berisi 1 sampai 10 kalimat")
            continue
        for t in v:
            if not isinstance(t, str) or not t.strip() or len(t) > 40:
                p.add(rel, f"pujian.{key}: kalimat harus 1 sampai 40 karakter: {t!r}")
    for key in pj:
        if key not in PUJIAN:
            p.add(rel, f"pujian.{key} tidak dikenal ({', '.join(PUJIAN)})")


def check_lock(p: Problems, ids: dict[str, list[str]], data: dict[str, dict]) -> dict[str, list[str]]:
    """Id yang pernah terbit tidak boleh hilang; pakai retired untuk menyembunyikan."""
    if not LOCK.exists():
        return ids
    old = json.loads(LOCK.read_text(encoding="utf-8"))
    merged: dict[str, list[str]] = {}
    for ns in sorted(set(old) | set(ids)):
        before, now = old.get(ns, []), ids.get(ns, [])
        if ns in ("kartu",):
            now_all = ids.get("kartu.all", [])
            missing = [i for i in before if i not in now_all]
        else:
            missing = [i for i in before if i not in now]
        # Kata kartu bergambar boleh keluar dari pool: posnya hilang dari peta, bintang lamanya tetap tersimpan.
        if missing and not ns.startswith("kata."):
            p.add("ids.lock.json", f"{ns}: id hilang tanpa retired: {', '.join(missing)}")
        merged[ns] = before + [i for i in now if i not in before]
    return merged


def validate(version: str | None = None) -> tuple[dict[str, dict], dict[str, list[str]], dict]:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if version is not None:
        if semver(version) <= semver(cfg["datasetVersion"]):
            raise SystemExit(f"Versi harus lebih tinggi dari {cfg['datasetVersion']}: aplikasi hanya mengambil versi yang lebih baru.")
        cfg["datasetVersion"] = version
    p = Problems()
    if not SEMVER_RE.match(cfg.get("datasetVersion", "")):
        p.add("dataset.json", "datasetVersion harus semver, misalnya 1.0.0")
    files = sorted(f.relative_to(SRC).as_posix() for f in SRC.rglob("*.json") if f.name != "manifest.json" or f.parent != SRC)
    for rel in files:
        if rel not in cfg["status"]:
            p.add("dataset.json", f"status untuk {rel} belum diisi")
    for rel, st in cfg["status"].items():
        if st not in ("draft", "reviewed"):
            p.add("dataset.json", f"status {rel} harus draft atau reviewed")
        if rel not in files:
            p.add("dataset.json", f"{rel} tidak ada di sumber")
    data: dict[str, dict] = {}
    for rel in files:
        raw = (SRC / rel).read_bytes()
        if len(raw) > MAX_FILE_BYTES:
            p.add(rel, "lebih dari 4 MB")
        try:
            data[rel] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            p.add(rel, f"JSON tidak sah: {e}")
            continue
        if data[rel].get("schemaVersion") != SUPPORTED_SCHEMA:
            p.add(rel, f"schemaVersion harus {SUPPORTED_SCHEMA}")
    if p.items:
        fail(p)
    chars = check_glyphs(p, data)
    ids = collect_ids(p, data, chars)
    merged = check_lock(p, ids, data)
    if p.items:
        fail(p)
    return data, merged, cfg


def fail(p: Problems) -> None:
    print("Dataset tidak lolos validasi:", file=sys.stderr)
    for i in p.items:
        print(f"  - {i}", file=sys.stderr)
    sys.exit(1)


def canonical(doc: dict) -> bytes:
    """Bentuk terbit, sama dengan lib/jsonio.dumps di dataset-api: indent 2, UTF-8 tanpa BOM, LF, baris baru di akhir.
    Checksum dihitung dari bentuk ini, jadi tidak bergantung pada spasi di file sumber."""
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_outputs(data: dict[str, dict], cfg: dict) -> dict[Path, bytes]:
    outputs: dict[Path, bytes] = {}
    entries = []
    for rel in sorted(data):
        body = canonical(data[rel])
        entries.append({"path": rel, "sha256": hashlib.sha256(body).hexdigest(), "status": cfg["status"][rel]})
        outputs[Path(rel)] = body
    manifest = {"schemaVersion": SUPPORTED_SCHEMA, "datasetVersion": cfg["datasetVersion"], "files": entries}
    outputs[Path("manifest.json")] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    return outputs


def show(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sync_dir(target: Path, outputs: dict[Path, bytes], check: bool) -> list[str]:
    """Samakan file .json di [target] dengan [outputs]; file lain (README.md) dibiarkan."""
    stale = []
    existing = {f.relative_to(target) for f in target.rglob("*.json") if f.is_file()} if target.exists() else set()
    for rel, body in outputs.items():
        f = target / rel
        if not f.exists() or f.read_bytes() != body:
            stale.append(show(f))
            if not check:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(body)
    for rel in existing - set(outputs):
        stale.append(f"{show(target / rel)} (sisa)")
        if not check:
            (target / rel).unlink()
    return stale


def semver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def parse_args(argv: list[str]) -> tuple[bool, str | None]:
    check, version = False, None
    it = iter(argv)
    for a in it:
        if a == "--check":
            check = True
        elif a == "--version":
            version = next(it, "")
            if not SEMVER_RE.match(version):
                raise SystemExit(f"--version harus semver, misalnya 1.7.0: {version!r}")
        else:
            raise SystemExit(f"Argumen tidak dikenal: {a}")
    if check and version:
        raise SystemExit("--check tidak bisa dipakai bersama --version")
    return check, version


def main() -> None:
    check, version = parse_args(sys.argv[1:])
    stale = []
    # Versi baru ditulis hanya setelah validasi lolos.
    data, merged_ids, cfg = validate(version)
    if version is not None:
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        stale.append(show(CONFIG))
    outputs = build_outputs(data, cfg)
    stale += sync_dir(SRC, outputs, check)

    lock = {k: merged_ids[k] for k in sorted(merged_ids) if k != "kartu.all"}
    lock_body = json.dumps(lock, ensure_ascii=False, indent=2) + "\n"
    if not LOCK.exists() or LOCK.read_text(encoding="utf-8") != lock_body:
        stale.append(show(LOCK))
        if not check:
            LOCK.write_text(lock_body, encoding="utf-8", newline="\n")

    total = sum(len(b) for b in outputs.values())
    if check:
        if stale:
            print("Manifest atau format belum diperbarui. Jalankan: python -I tools/sambung-titik/build.py", file=sys.stderr)
            for x in stale:
                print(f"  - {x}", file=sys.stderr)
            sys.exit(1)
        print(f"Dataset {cfg['datasetVersion']} valid dan manifest sudah terbaru.")
        return
    print(f"Dataset {cfg['datasetVersion']}: {len(outputs) - 1} file, {total / 1024:.1f} KB. Diperbarui: {len(stale)}.")
    for x in stale:
        print(f"  - {x}")
    print("Berikutnya: commit dan push, lalu purge jsDelivr (lihat tools/sambung-titik/README.md).")


if __name__ == "__main__":
    main()
