#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kafesin dört kolunu sırayla koşurur, her kolun kaydını ayrı dosyaya yazar.

Kullanım:
    python -u kos.py                 # a, b, c, d sırayla
    python -u kos.py --duman         # her kolun 8 adımlık hızlı hâli
    python -u kos.py --kollar b      # yalnızca bir kol

Kayıtlar: cikti/kol-a.txt ... cikti/kol-d.txt. Çıktı doğrudan dosyaya
yazdırılır ('| tee' bu projede uzun bir koşumun kaydını kaybetmişti).
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BURADA = Path(__file__).resolve().parent
CIKTI = BURADA / "cikti"


def main():
    ayristirici = argparse.ArgumentParser()
    ayristirici.add_argument("--duman", action="store_true")
    ayristirici.add_argument("--kollar", default="abcd")
    args = ayristirici.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)
    print(f"koşum başlangıcı: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    for kol in args.kollar:
        if kol not in "abcde":
            raise ValueError("bilinmeyen kol: %s (kayitlar kol-a..kol-e)" % kol)
        kok = CIKTI.resolve()
        yol = (CIKTI / f"kol-{kol}.txt").resolve()
        if not str(yol).startswith(str(kok) + os.sep):
            raise ValueError("kol kaydi cikti dizininin disina yaziliyor: %s" % yol)
        t0 = time.time()
        akis = yol.open("w", encoding="utf-8")
        try:
            durum = subprocess.run(
                [sys.executable, "-u", str(BURADA / "gomme_egit.py"), "--kol", kol]
                + (["--duman"] if args.duman else []),
                stdout=akis, stderr=subprocess.STDOUT)
        finally:
            akis.close()
        print(f"kol {kol}: çıkış kodu {durum.returncode}, "
              f"{time.time() - t0:.0f} sn -> {yol.name}", flush=True)
    print(f"koşum bitişi: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == "__main__":
    main()
