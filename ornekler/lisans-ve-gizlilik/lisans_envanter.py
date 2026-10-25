#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lisans envanteri: bu makinedeki yerel model yığınının VE bu deponun lisans kayıtlarını dök'er.

Ne ölçer:
  1. Yerel Ollama modelleri: /api/tags listesinden her model için `ollama show --modelfile`
     çıktısındaki LICENSE bloğunun adı, boyu, kısıt maddeleri ve şablon-artığı (placeholder) durumu.
  2. Depo: örnek betiklerdeki/sayfalardaki lisans atıfları (CC BY-SA, MIT, Apache...) ve
     Örnek 6'nın Vikipedi korpusu için üretilen atıf satırı.

Çıkarım isteği YOKTUR; sadece yerel dosya okuma + Ollama'nın model liste ucu.
Koşum:  PYTHONUTF8=1 ../../.venv/Scripts/python.exe -u lisans_envanter.py > cikti/lisans-envanter.txt 2>&1
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

OS = "http://127.0.0.1:11434"
DEPO = Path(__file__).resolve().parents[2]

# Kısıt/koğul taraması: anahtar sözcük -> etiket. Büyük/küçük harf duyarsız.
KISITLAR = [
    (r"non-?commercial", "TICARI-KULLANIM-KAPALI"),
    (r"research\s+(only|purposes)", "ARASTIRMA-KOSULLU"),
    (r"commercially\s+using", "TICARI-ICIN-AYRILI-IZIN"),
    (r"built with|improved using", "URETIM-DIKEY-ATIF-ZORUNLU"),
    (r"acceptable use", "KULLANIM-POLITIKASI-VAR"),
    (r"responsible use", "SORUMLU-KULLANIM-VAR"),
    (r"export\s+control", "IHRACAT-KONTROLU"),
    (r"trademark", "MARKA-KOSULU"),
    (r'"notice" text file|attribution notice', "ATIF-DOSYASI-ZORUNLU"),
    (r"prominent(?:ly)? notice", "GORUNUR-IKAR-ZORUNLU"),
    (r"indemnif", "TAZMIN-YUKUMLULUGU"),
    (r"without\s+restriction", "KISITSIZ"),
]

SABLONLAR = [r"\[year\]", r"\[fullname\]", r"your name here", r"\<\s*company name", r"\[name of copyright"]


def ayrinti(*satirlar: str) -> None:
    for s in satirlar:
        print(s, flush=True)


def modelleri_listele() -> list[dict]:
    with urllib.request.urlopen(f"{OS}/api/tags", timeout=10) as yanit:
        return json.loads(yanit.read().decode("utf-8")).get("models", [])


def modelfile(ad: str) -> str:
    cp = subprocess.run(["ollama", "show", "--modelfile", ad], capture_output=True, text=True, encoding="utf-8")
    if cp.returncode != 0:
        raise RuntimeError(f"ollama show başaramadı: {ad}: {cp.stderr[:200]}")
    return cp.stdout


def lisans_blogu(cf: str) -> str | None:
    m = re.search(r'^LICENSE """([\s\S]*?)"""', cf, re.M)
    return m.group(1) if m else None


def siniflandir(metin: str) -> tuple[str, list[str], list[str]]:
    ad = ""
    for satir in metin.splitlines():
        if satir.strip():
            ad = satir.strip()
            break
    kullar = []
    for desen, etiket in KISITLAR:
        if re.search(desen, metin, re.I):
            kullar.append(etiket)
    sablon = [d for d in SABLONLAR if re.search(d, metin, re.I)]
    return ad, kullar, sablon


def madde_no_ver(metin: str, desen: str, sinir: int = 240) -> list[str]:
    """Kısıt cümlesini, içindeki madde numarasiyla birlikte döndür (log'da alintilamak için)."""
    bulunan = []
    for satir in metin.splitlines():
        if re.search(desen, satir, re.I):
            temiz = re.sub(r"\s+", " ", satir).strip()
            bulunan.append(temiz[:sinir])
    return bulunan


def yereller() -> None:
    ayrinti("=" * 78)
    ayrinti("BÖLÜM 1: YEREL OLLAMA MODEL YIGINI (modelfile LICENSE alani)")
    ayrinti("=" * 78)
    modeller = modelleri_listele()
    ayrinti(f"Ollama'nın bildirdiği model sayısı: {len(modeller)}")
    for model in modeller:
        ad = model["name"]
        basla = time.perf_counter()
        try:
            cf = modelfile(ad)
        except Exception as hata:  # noqa: BLE001
            ayrinti(f"\n### {ad}\n  [HATA] {hata}")
            continue
        sure = time.perf_counter() - basla
        detay = model.get("details", {})
        ayrinti(f"\n### {ad}")
        ayrinti(
            f"  aile={detay.get('family')} parametre={detay.get('parameter_size')} "
            f"nicemleme={detay.get('quantization_level')} boyut={model.get('size', 0) / 1e6:.0f} MB "
            f"(ollama show: {sure:.2f} sn)"
        )
        bloklar = re.findall(r"^(\w+) \"\"\"", cf, re.M)
        ayrinti(f"  modelfile bloklari: {', '.join(bloklar)}")
        lis = lisans_blogu(cf)
        if lis is None:
            ayrinti("  LICENSE ALANI YOK — dağıtım paketi lisans metni taşımıyor.")
            continue
        ad1, kullar, sablon = siniflandir(lis)
        ayrinti(f"  lisans başlığı   : {ad1}")
        ayrinti(f"  lisans metni     : {len(lis.encode('utf-8'))} bayt, {len(lis.splitlines())} satır")
        ayrinti(f"  sınıflandırma    : {'; '.join(kullar) if kullar else 'etikitlenmemiş'}")
        ayrinti(f"  şablon artığı    : {'VAR -> ' + ', '.join(sablon) if sablon else 'yok'}")
        for desen in ["non-?commercial", "commercially", "built with", '"notice" text file', "export\\s+control"]:
            for madde in madde_no_ver(lis, desen)[:2]:
                ayrinti(f"  maddeler [{desen}]: {madde}")
        sistem = re.search(r'^SYSTEM (.*)$', cf, re.M)
        if sistem:
            ayrinti(f"  SYSTEM satırı  : {sistem.group(1)[:120]}")


def depo() -> None:
    ayrinti("")
    ayrinti("=" * 78)
    ayrinti("BÖLÜM 2: DEPO KAYITLARI (bu rehberin kendi lisans izleri)")
    ayrinti("=" * 78)
    hedefler = []
    for uzv in ("py", "md", "mdx"):
        hedefler += sorted(DEPO.glob(f"ornekler/**/*.{uzv}")) + sorted(DEPO.glob(f"src/content/docs/**/*.{uzv}"))
    # denetimi yapan klasör kendi anahtar sözcüklerini sayar: denetlenen kümeden çıkar
    disarda = (DEPO / "ornekler" / "lisans-ve-gizlilik").resolve()
    hedefler = [y for y in hedefler if disarda not in y.resolve().parents]
    kalip = re.compile(r"(CC BY-SA|CC-BY-SA|CC0|ODC-By|Apache-2\.0|Apache License|MIT|Llama Community|Qwen RESEARCH|qwen-research|GPL)", re.I)
    sayim: dict[str, int] = {}
    vurus_dosya = 0
    for yol in hedefler:
        if "__pycache__" in str(yol) or "/cikti/" in str(yol).replace("\\", "/"):
            continue
        metin = yol.read_text(encoding="utf-8", errors="replace")
        bulunan = kalip.findall(metin)
        if bulunan:
            vurus_dosya += 1
        for b in bulunan:
            sayim[b.upper()] = sayim.get(b.upper(), 0) + 1
    ayrinti(f"taranan dosya      : {len(hedefler)} (py/md/mdx; __pycache__, cikti/ ve lisans-ve-gizlilik/ dışarıda)")
    ayrinti(f"en az bir lisans sözcüğü geçen dosya: {vurus_dosya}")
    for anahtar, adet in sorted(sayim.items(), key=lambda kv: -kv[1]):
        ayrinti(f"  {anahtar:22s} {adet}")

    viki = DEPO / "ornekler" / "viki-rag" / "viki_rag.py"
    if viki.exists():
        metin = viki.read_text(encoding="utf-8")
        satirlar = [s.strip() for s in metin.splitlines() if "CC BY" in s or "User-Agent" in s or " userAgent" in s.lower()]
        ayrinti("")
        ayrinti("  Örnek 6 (viki_rag.py) atıf/erişim izleri:")
        for s in satirlar[:8]:
            ayrinti(f"    - {s[:150]}")
    urun = DEPO / "ornekler" / "turkce-asistan" / "cikti" / "egitim.jsonl"
    kaynak = DEPO / "ornekler" / "turkce-asistan" / "hazirla.py"
    if kaynak.exists():
        metin = kaynak.read_text(encoding="utf-8")
        satirlar = [s.strip() for s in metin.splitlines() if re.search(r"dataset|lisens|MIT|apache", s, re.I)][:6]
        ayrinti("")
        ayrinti("  Örnek 3 (hazirla.py) veri kaynağı satırları:")
        for s in satirlar:
            ayrinti(f"    - {s[:150]}")
    if urun.exists():
        ayrinti("")
        ayrinti(f"  Örnek 3 türetilmiş ürün: {urun.relative_to(DEPO)} -> {sum(1 for _ in urun.open(encoding='utf-8'))} satır")


def main() -> None:
    print(f"koşum başlangıcı: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    yereller()
    depo()
    print(f"\nkoşum bitişi: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--depo":
        depo()
    else:
        main()
