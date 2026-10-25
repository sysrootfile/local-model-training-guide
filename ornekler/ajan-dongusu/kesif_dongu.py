"""Ikinci kesif: arac sonucunu modele geri verme + arac taniminin token fiyati.

Alan adlari dokumandan degil, sunucunun kabul edip etmemesinden dogrulanir.
Uc soru:
  1) rol="tool" mesajinda `tool_name` sart mi, `tool_call_id` taniniyor mu?
  2) Model araç sonucundan sonra nihai cevabi üretebiliyor mu?
  3) Araç tanimi isteme kac token ekliyor (tools'siz ayni istekle fark)?
"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_IZINLI_ANA_MAKINE = ("127.0.0.1",)


def _url_dogrula(url):
    # Kosum hijyeni: yalniz izinli ana makineler; sabitler de tanim aninda denetlenir.
    from urllib.parse import urlparse

    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _IZINLI_ANA_MAKINE:
        raise ValueError("izinli ana makine degil: %s" % url)
    return url


UÇ = _url_dogrula("http://127.0.0.1:11434/api/chat")
MODEL = "qwen2.5:3b-instruct-q4_K_M"

ARAÇLAR = [
    {
        "type": "function",
        "function": {
            "name": "sehir_nufusu",
            "description": "Bir sehirin guncel nufusunu dondurur.",
            "parameters": {
                "type": "object",
                "properties": {"sehir": {"type": "string", "description": "Sehir adi"}},
                "required": ["sehir"],
            },
        },
    }
]


def gonder(mesajlar, ek=None):
    yük = {"model": MODEL, "messages": mesajlar, "stream": False,
           "options": {"temperature": 0, "num_predict": 120}}
    if ek:
        yük.update(ek)
    istek = urllib.request.Request(
        _url_dogrula(UÇ), data=json.dumps(yük).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(istek, timeout=600) as yanıt:
        return json.loads(yanıt.read().decode("utf-8"))


def yaz(başlık, yanıt):
    mesaj = yanıt.get("message", {})
    print("=" * 70)
    print(başlık)
    print("  content   :", repr((mesaj.get("content") or "")[:200]))
    print("  tool_calls:", json.dumps(mesaj.get("tool_calls"), ensure_ascii=False)[:200])
    print("  token     : girdi %s çıktı %s önbellek %s" % (
        yanıt.get("prompt_eval_count"), yanıt.get("eval_count"),
        yanıt.get("prompt_eval_cached_count")))
    print("  süre (sn) : toplam %.2f | ön-yük %.2f | çözme %.2f" % (
        yanıt.get("total_duration", 0) / 1e9, yanıt.get("prompt_eval_duration", 0) / 1e9,
        yanıt.get("eval_duration", 0) / 1e9))


taban = [{"role": "user", "content": "Izmir'in nufusu kac? Bu soru icin sehir_nufusu aracini kullan."}]
çağrı = {"id": "call_kesif1", "type": "function",
         "function": {"name": "sehir_nufusu", "arguments": {"sehir": "Izmir"}}}
asistan = [{"role": "assistant", "content": "", "tool_calls": [çağrı]}]

# 3) arac taniminin token gideri: ayni istek, tools'suz
yaz("A) toolsSUZ ayni istek (taban token sayisi)", gonder(taban))
yaz("B) toolsLU ayni istek", gonder(taban, {"tools": ARAÇLAR}))

# 1+2) rol="tool" mesajinin bicimi
yaz("C) tool mesaji: tool_name ile", gonder(
    taban + asistan + [{"role": "tool", "tool_name": "sehir_nufusu",
                        "content": "4425000"}], {"tools": ARAÇLAR}))

yaz("D) tool mesaji: yalniz content (ad yok)", gonder(
    taban + asistan + [{"role": "tool", "content": "4425000"}], {"tools": ARAÇLAR}))

yaz("E) tool mesaji: tool_call_id ile", gonder(
    taban + asistan + [{"role": "tool", "tool_call_id": "call_kesif1",
                        "content": "4425000"}], {"tools": ARAÇLAR}))

# ara turlarda onbellege ne oluyor (ajan dongusunun gerçek maliyeti)
yaz("F) ayni gecmis, ikinci tur (onbellek isi?)", gonder(
    taban + asistan + [{"role": "tool", "tool_name": "sehir_nufusu",
                        "content": "4425000"}], {"tools": ARAÇLAR}))

print("=" * 70)
print("kesif bitti.")
