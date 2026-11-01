"""Fixed vocabularies and the first-wave game catalog (see specs/question-bank-content)."""

SCHEMA_VERSION = 1

SEGMENTS = {
    "sd-a": "SD",
    "sd-b": "SD",
    "sd-c": "SD",
    "smp": "SMP",
    "sma": "SMA",
}
SEGMENT_ORDER = list(SEGMENTS)

INTERACTIONS = {"NUMPAD", "TILE_BANK", "FILL_GAP", "MULTI_CHOICE", "MATCH_PAIRS", "COMPARE"}
CATEGORIES = {"numerasi", "literasi", "budaya"}
CONTENT_KINDS = {"procedural", "curated"}
COLOR_TOKENS = {"teal", "yellow", "blue", "green", "purple", "magenta", "orange", "pink"}

PROCEDURAL_MIN_PER_FILE = 100
CURATED_MIN_PER_GAME = 100
CURATED_MIN_PER_FILE = 20
MIN_DISTINCT_DIFFICULTIES = 3


def _game(category, kind, interaction, segments, title, description, instruction, emoji, color):
    return {
        "category": category,
        "contentKind": kind,
        "interaction": interaction,
        "segments": segments,
        "title": title,
        "description": description,
        "instruction": instruction,
        "emoji": emoji,
        "colorToken": color,
    }


ALL = ["sd-a", "sd-b", "sd-c", "smp", "sma"]

CATALOG = {
    "hitung-cepat": _game(
        "numerasi", "procedural", "NUMPAD", ALL,
        "Hitung Cepat", "Hitung hasil operasi bilangan dengan cepat dan tepat.",
        "Berapa hasilnya?", "➕", "teal"),
    "tebak-angka": _game(
        "numerasi", "procedural", "TILE_BANK", ALL,
        "Tebak Angka", "Tuliskan angka menjadi kata bilangan (terbilang).",
        "Tulis angka ini dengan kata!", "🔢", "blue"),
    "kata-ke-angka": _game(
        "numerasi", "procedural", "NUMPAD", ["sd-a", "sd-b", "sd-c", "smp"],
        "Kata ke Angka", "Ubah kata bilangan menjadi angka.",
        "Angka berapakah ini?", "🔤", "yellow"),
    "deret-angka": _game(
        "numerasi", "procedural", "NUMPAD", ALL,
        "Deret Angka", "Temukan pola dan lengkapi angka yang hilang.",
        "Angka berapa yang hilang?", "🧩", "green"),
    "banding-angka": _game(
        "numerasi", "procedural", "COMPARE", ALL,
        "Banding Angka", "Bandingkan dua nilai: lebih besar, lebih kecil, atau sama.",
        "Pilih tanda yang tepat: <, >, atau =", "⚖️", "orange"),
    "angka-romawi": _game(
        "numerasi", "procedural", "NUMPAD", ["sd-b", "sd-c", "smp"],
        "Angka Romawi", "Ubah angka Romawi ke angka biasa dan sebaliknya.",
        "Ubah angka ini!", "🏛️", "purple"),
    "cari-x": _game(
        "numerasi", "procedural", "NUMPAD", ["sd-b", "sd-c", "smp", "sma"],
        "Cari X", "Temukan nilai yang belum diketahui dalam persamaan.",
        "Berapa nilai yang dicari?", "🔍", "magenta"),
    "lengkapi-kata": _game(
        "literasi", "curated", "FILL_GAP", ALL,
        "Lengkapi Kata", "Lengkapi huruf yang hilang hingga menjadi kata yang benar.",
        "Lengkapi huruf yang hilang!", "✏️", "green"),
    "susun-huruf": _game(
        "literasi", "curated", "TILE_BANK", ["sd-a", "sd-b", "sd-c"],
        "Susun Huruf", "Susun huruf acak menjadi kata yang benar.",
        "Susun huruf menjadi kata!", "🔀", "yellow"),
    "kata-baku": _game(
        "literasi", "curated", "MULTI_CHOICE", ["sd-c", "smp", "sma"],
        "Kata Baku", "Pilih penulisan kata yang baku sesuai KBBI.",
        "Mana kata yang baku?", "📖", "blue"),
    "sinonim-antonim": _game(
        "literasi", "curated", "MATCH_PAIRS", ["sd-b", "sd-c", "smp", "sma"],
        "Sinonim & Antonim", "Cari pasangan kata yang sama arti atau berlawanan arti.",
        "Pilih pasangan kata yang tepat!", "🔁", "teal"),
    "imbuhan": _game(
        "literasi", "curated", "MULTI_CHOICE", ["sd-b", "sd-c", "smp"],
        "Imbuhan", "Gabungkan kata dasar dengan imbuhan menjadi kata yang benar.",
        "Apa hasil gabungannya?", "🧱", "orange"),
    "peribahasa": _game(
        "literasi", "curated", "MULTI_CHOICE", ["sd-c", "smp", "sma"],
        "Peribahasa", "Lengkapi peribahasa Indonesia dan pahami maknanya.",
        "Lengkapi peribahasa ini!", "💬", "pink"),
    "susun-kalimat": _game(
        "literasi", "curated", "TILE_BANK", ["sd-a", "sd-b", "sd-c"],
        "Susun Kalimat", "Susun kata-kata menjadi kalimat yang benar.",
        "Susun kata menjadi kalimat!", "🧾", "purple"),
    "aksara-nusantara": _game(
        "budaya", "curated", "MULTI_CHOICE", ["sd-b", "sd-c", "smp"],
        "Aksara Nusantara", "Kenali aksara Jawa dan bacaannya dalam huruf Latin.",
        "Bagaimana cara membacanya?", "ꦲ", "magenta"),
}

NUMERASI_GAMES = {g for g, spec in CATALOG.items() if spec["category"] == "numerasi"}
