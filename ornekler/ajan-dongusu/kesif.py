"""Tek isteklik kesif: bu makinedeki Ollama arac cagirmayi nasil konusuyor?

Sayfa olcumu degil; betigi yazmadan once alan adlarini sunucunun kendisinden
dogrulama adimi. Iki sey test edilir: (a) varsayilan (auto) arac seciminde 3B
model araci cagiyor mu, (b) tool_choice="required" fark ediyor mu.
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
                "properties": {
                    "sehir": {"type": "string", "description": "Sehir adi"},
                },
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


def özet(başlık, yanıt):
    mesaj = yanıt.get("message", {})
    print("=" * 70)
    print(başlık)
    print("-" * 70)
    print("anahtarlar      :", sorted(yanıt.keys()))
    print("mesaj anahtarları:", sorted(mesaj.keys()))
    print("content          :", repr((mesaj.get("content") or "")[:220]))
    print("tool_calls       :", json.dumps(mesaj.get("tool_calls"), ensure_ascii=False)[:400])
    print("done_reason      :", yanıt.get("done_reason"))
    print("tokenlar         : girdi", yanıt.get("prompt_eval_count"),
          "çıktı", yanıt.get("eval_count"),
          "önbellek", yanıt.get("prompt_eval_cached_count"))
    print("süre (sn)        : toplam %.2f | yük %.2f | ön-yük %.2f | çözme %.2f" % (
        yanıt.get("total_duration", 0) / 1e9, yanıt.get("load_duration", 0) / 1e9,
        yanıt.get("prompt_eval_duration", 0) / 1e9, yanıt.get("eval_duration", 0) / 1e9))


soru = [{"role": "user", "content": "Izmir'in nufusu kac? Bu soru icin sehir_nufusu aracini kullan."}]

özet("1) tools + varsayilan secim (tool_choice yok)", gonder(soru, {"tools": ARAÇLAR}))
özet("2) tools + tool_choice='required'",
     gonder(soru, {"tools": ARAÇLAR, "tool_choice": "required"}))
özet("3) tools + tool_choice isimli fonksiyon",
     gonder(soru, {"tools": ARAÇLAR,
                   "tool_choice": {"type": "function", "function": {"name": "sehir_nufusu"}}}))
print("=" * 70)
print("kesif bitti.")
