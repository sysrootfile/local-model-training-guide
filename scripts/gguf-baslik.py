#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GGUF dosyasının başlık üstverisini okur; modeli belleğe yüklemez.

Kullanım:
    python scripts/gguf-baslik.py <blob-dosyasi> [anahtar-regex | token-numarasi]

Model eğitim ayarlarının (temperature, top_p, top_k, min_p ...) dosyaya
gömülü olup olmadığını görmek için anahtar-regex olarak "sampl|temp" verin.
İkinci değişken bir sayıysa (ör. 151645) o token numarasının sözlükteki
yazısı basılır; EOS ve şablon işaretlerini tanımlamanın yolu bu.
Ollama blob dosyaları .ollama/models/blobs/ altındadır; hangi blob'un hangi
modele ait olduğunu `ollama show --modelfile <model>` çıktısındaki FROM
satırı söyler.
"""
import re
import struct
import sys

TIPLER = {
    0: ("<B", 1, "uint8"), 1: ("<b", 1, "int8"),
    2: ("<H", 2, "uint16"), 3: ("<h", 2, "int16"),
    4: ("<I", 4, "uint32"), 5: ("<i", 4, "int32"),
    6: ("<f", 4, "float32"), 7: ("<?>", 1, "bool"),
    10: ("<Q", 8, "uint64"), 11: ("<q", 8, "int64"), 12: ("<d", 8, "float64"),
}


def oku_veri(dosya, tip):
    if tip == 7:
        return dosya.read(1)[0] != 0
    if tip == 8:
        return oku_dize(dosya)
    if tip == 9:
        alt = struct.unpack("<I", dosya.read(4))[0]
        adet = struct.unpack("<Q", dosya.read(8))[0]
        return [oku_veri(dosya, alt) for _ in range(adet)]
    biçim, boyut, _ad = TIPLER[tip]
    return struct.unpack(biçim, dosya.read(boyut))[0]


def oku_dize(dosya):
    boyut = struct.unpack("<Q", dosya.read(8))[0]
    return dosya.read(boyut).decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    yol = sys.argv[1]
    kalan = sys.argv[2:]
    numaralar = [int(x) for x in kalan if x.isdigit()]
    regexler = [x for x in kalan if not x.isdigit()]
    if regexler:
        filtre = re.compile("|".join(regexler), re.I)
    elif numaralar:
        filtre = re.compile(r"(^$)")
    else:
        filtre = None
    with open(yol, "rb") as d:
        if d.read(4) != b"GGUF":
            print("! GGUF değil:", yol)
            return 1
        surum = struct.unpack("<I", d.read(4))[0]
        tensör = struct.unpack("<Q", d.read(8))[0]
        adet = struct.unpack("<Q", d.read(8))[0]
        print("GGUF sürüm %d | tensör %d | üstveri anahtarı %d" % (surum, tensör, adet))
        isten = dict((no, False) for no in numaralar)
        gorulen = 0
        for _ in range(adet):
            ad = oku_dize(d)
            tip = struct.unpack("<I", d.read(4))[0]
            deger = oku_veri(d, tip)
            if isinstance(deger, list) and ad in ("tokenizer.ggml.tokens",
                                                  "tokenizer.ggml.added_tokens"):
                for no in list(isten):
                    if no < len(deger):
                        print("  token %-7d -> %s" % (no, deger[no]))
                        isten[no] = True
            if filtre is None or filtre.search(ad):
                gorulen += 1
                if isinstance(deger, list) and len(deger) > 8:
                    deger = "[zincir %d oge, ilk 3: %s]" % (len(deger), deger[:3])
                if isinstance(deger, str) and len(deger) > 90:
                    deger = deger[:90] + "..."
                print("  %-42s %s" % (ad, deger))
        if regexler and gorulen == 0:
            print("  (eşleşen anahtar yok)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
