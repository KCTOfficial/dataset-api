"""Registry of procedural generators: gameId -> module/object with GAME_ID, TARGETS, generate(), featured()."""

from generators import aksara_nusantara, angka_romawi, banding_angka, cari_x, deret_angka, hitung_cepat
from generators.terbilang_games import KATA_KE_ANGKA, TEBAK_ANGKA

REGISTRY = {g.GAME_ID: g for g in (
    hitung_cepat, TEBAK_ANGKA, KATA_KE_ANGKA, deret_angka, banding_angka, angka_romawi, cari_x, aksara_nusantara,
)}
