---
title: "Yerel Kurulum (Windows): Sıfırdan Hazır Ortam"
description: Windows'ta Python, sanal ortam, NVIDIA sürücüsü ve PyTorch'u adım adım kurun; CUDA doğrulaması, WSL2 ne zaman gerekir ve sık kurulum hatalarının çözümü.
dogrulama: 2026-10-15
---

Bu sayfa, hiçbir şeyin kurulu olmadığı bir Windows bilgisayardan "model eğitebilirim" noktasına gelmenin en kısa yoludur. Her adımda önce **ne** ve **neden** yaptığımızı, sonra kopyala-yapıştır komutları vereceğiz.

:::tip
Tüm komutlar PowerShell (veya Windows Terminal) içindir ve yönetici yetkisi gerektirmez.
:::

## Genel Resim: Python, PyTorch, CUDA, Sürücü

Bu dört ismin ilişkisini bir kez oturtmak, sonraki hataları kendi başınıza teşhis etmenizi sağlar:

```text title="Katmanlı yapı"
  ┌────────────────────────────────────────────────────┐
  │  Sizin kodunuz ve kütüphaneler                     │
  │  (transformers, datasets, peft, trl, ...)          │
  ├────────────────────────────────────────────────────┤
  │  PyTorch   →  tensör matematiği ve otomatik türev  │
  ├────────────────────────────────────────────────────┤
  │  CUDA      →  matematiği GPU'da paralel koşturma   │
  ├────────────────────────────────────────────────────┤
  │  NVIDIA sürücüsü  →  Windows'un kartla konuşması   │
  ├────────────────────────────────────────────────────┤
  │  GPU donanımı                                      │
  └────────────────────────────────────────────────────┘
```

- **Python:** kodu yazdığınız dil; kütüphaneler burada yaşar.
- **PyTorch:** ağırlık, gradyan ve matris işlemlerini yapan çerçeve.
- **CUDA:** PyTorch'un GPU ile konuştuğu arayüz ("kartın hesap makinesi dili").
- **Sürücü:** donanım ile işletim sistemi arasındaki çevirmen; `nvidia-smi` bu katmanın canlı raporudur.

:::note
**GPU'nuz yoksa ne olur?** Her şey yine kurulur; PyTorch CPU modunda çalışır. Küçük modellerle (0.5-1B) kısa deneyler yapabilirsiniz ama gerçek bir ince ayar CPU'da katlanılamayacak kadar yavaştır. Bu durumda yolculuk [Bulut Seçenekleri](/donanim/bulut-secenekleri/) sayfasından devam eder; kurulum adımları bulutta neredeyse aynıdır.
:::

## Adım 1: Python Kurulumu

1. [python.org/downloads](https://www.python.org/downloads/) adresinden **Python 3.11 veya 3.12** sürümünü indirin.
2. Kurulum ekranında **"Add python.exe to PATH"** kutusunu mutlaka işaretleyin. (Sonradan düzeltmek zahmetlidir.)
3. Kurulumu bitirin, terminali **kapatıp yeniden açın**.

:::caution
2026 itibarıyla PyTorch, Windows'ta Python 3.10-3.14 bantını resmen destekliyor; 3.15'in Windows paketi ise henüz yok. 3.13 de genelde sorunsuzdur, ancak 3.14/3.15 gibi en uç bantta üçüncü taraf paketlerle "paket derlenemedi" tipi hatalar alırsanız ilk şüpheli Python sürümüdür; 3.12'ye dönmek en pratik çözümdür.
:::

Doğrulama:

```bash title="PowerShell"
python --version
# Örnek çıktı: Python 3.12.8
```

`python` bulunamadıysa Windows'un `py` başlatıcısını deneyin: `py --version`.

:::tip
Makinede birden çok Python sürümü olabilir. Hangisinin aktif olduğunu `where python` gösterir; kalıcı çözüm sanal ortamdır (Adım 2).
:::

## Adım 2: Sanal Ortam (venv veya uv)

Sanal ortam (venv), proje bazlı izole bir Python kurulumudur: A projesinin paketleri B projesini etkilemez.

- **venv:** Python ile birlikte gelir, ek kurulum istemez.
- **uv:** Rust ile yazılmış modern paket yöneticisi; kurulum ve paket çözümlemesi çok hızlıdır, Python sürümlerini de yönetebilir. 2026 itibarıyla olgun ve yaygındır.

:::caution
**Neden sanal ortam şart?** Sistem geneline kurulan paketler zamanla birbirini bozar ("A paketi X'in yeni sürümünü ister, B paketi X'in eskisini"). Sanal ortam her projeye kendi kutulu dünyasını verir; silmek istediğinizde klasörü silmeniz yeterlidir.
:::

### uv kurulumu (önerilen)

```powershell title="PowerShell — uv kurulumu"
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Terminali yeniden açın ve doğrulayın:

```powershell title="PowerShell"
uv --version
```

:::note
Yukarıdaki komut uv'nin resmi kurulum betiğidir (`irm` = Invoke-RestMethod). Güncel komut her zaman [uv dokümanında](https://docs.astral.sh/uv/) bulunur; tek satırlık betikleri kopyalarken kaynağı doğrulamak iyi alışkanlıktır.
:::

### Proje ve ortam oluşturma

```powershell title="PowerShell"
mkdir C:\ml\projelerim
cd C:\ml\projelerim
uv venv --python 3.12
```

Kısa yol (`C:\ml\...`) bilinçli bir tercih: Windows'un uzun yol (260 karakter) sınırı, derin klasörlerde beklenmedik hatalara yol açar.

`uv` kullanırken ortamı etkinleştirmeden doğrudan `uv pip install ...` çalıştırabilirsiniz. Klasik `venv` tercih ederseniz:

```powershell title="PowerShell — klasik venv"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

:::tip
PowerShell "bu sistemde betik çalıştırma devre dışı" hatası verirse bir kez şunu çalıştırın: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
:::

## Adım 3: NVIDIA Sürücüsü Kontrolü

```bash title="PowerShell / CMD"
nvidia-smi
```

Çıktıda üç satır önemlidir:

```text
+-------------------------------------------------------------+
| NVIDIA-SMI 5xx.xx    Driver Version: 5xx.xx                 |
| CUDA Version: 12.x                                          |
+-------------------------------------------------------------+
|   0  NVIDIA GeForce RTX 4070        Mem: 1234MiB / 12282MiB |
+-------------------------------------------------------------+
```

- **Driver Version:** yüklü sürücünün sürümü.
- **CUDA Version:** sürücünün *desteklediği en yüksek* CUDA sürümü — kurulu sürüm değil, üst sınırdır. PyTorch'un getirdiği CUDA çalışma zamanı bu değerin altında olmalıdır.
- **Memory-Usage (Mem):** kartta kullanılan / toplam VRAM.

Komut bulunamıyorsa NVIDIA sürücüsü kurulu değildir (ya da kart NVIDIA değildir). Güncel sürücü: [NVIDIA resmi sürücü indirme sayfası](https://www.nvidia.com/Download/index.aspx).

Sürücü bantları hakkında fikir vermesi için: 2026 itibarıyla CUDA 13 çalışma zamanı **r580 sürücü ailesinden** bir sürücü ister; CUDA 12 ailesi için Linux'ta 525.60.13, Windows'ta 527.41 ve üzeri yeterlidir (NVIDIA CUDA Toolkit sürüm notları). Kuracağınız PyTorch derlemesinin CUDA sürümü, çıktıdaki "CUDA Version" üst sınırını aşıyorsa (örn. cu130 kurarken 12.x görüyorsanız) sürücüyü güncelleyin; sürücü güncellemesi kurulu PyTorch kurulumunu bozmaz.

:::note
"CUDA Version 12.x yazıyor, ayrıca CUDA'yı elle mi kurmam lazım?" — Hayır. PyTorch, CUDA çalışma zamanını paketiyle birlikte getirir. Sizden istenen tek şey yeterince yeni bir **sürücüdür**.
:::

## Adım 4: PyTorch Kurulumu

CPU (GPU'suz) kurulum — yalnızca küçük denemeler için:

```bash title="PowerShell — CPU"
pip install torch
```

GPU (CUDA) kurulumu — 2026 itibarıyla tipik biçim (güncel stabil sürüm: PyTorch 2.13):

```bash title="PowerShell — şablon; güncel etiketi siteden kopyalayın"
pip install torch --index-url https://download.pytorch.org/whl/cuXXX
```

:::caution
Yukarıdaki `cuXXX` bir **yer tutucudur**. 2026 itibarıyla güncel örnek etiketler `cu126` ve `cu130`'dur; CUDA 13.0 varsayılan derlemedir ve eski etiketler dönem dönem emekliye ayrılır (PyTorch 2.13 ile birlikte `cu128`/`cu129` tekerlekleri kaldırıldı — eski rehberlerdeki komutlar bu yüzden artık çalışmayabilir). Tam komutu her zaman [PyTorch: Get Started](https://pytorch.org/get-started/locally/) sayfasındaki seçiciden üretin: Platform **Windows**, Package **pip**, Compute Platform **CUDA XX**.
:::

:::danger
Windows'ta düz `pip install torch` genellikle **CPU sürümünü** kurar. "Kurdum ama GPU kullanılmıyor" sorununun bir numaralı nedeni budur. Şüphedeyseniz Adım 5'teki doğrulamayı çalıştırın.
:::

## Adım 5: Doğrulama

```python title="dogrula.py"
import torch

print("PyTorch sürümü      :", torch.__version__)
print("CUDA var mı?        :", torch.cuda.is_available())
print("CUDA çalışma zamanı :", torch.version.cuda)

if torch.cuda.is_available():
    print("Cihaz               :", torch.cuda.get_device_name(0))
    toplam_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print("Toplam VRAM         :", round(toplam_gb, 1), "GB")
    print("BF16 desteği        :", torch.cuda.is_bf16_supported())
```

Çalıştırın: `python dogrula.py`. Beklenen: `CUDA var mı? True`, kart adınız ve `CUDA çalışma zamanı` satırında `13.0` gibi bir değer. Çıktıyı şöyle okuyun:

- `CUDA çalışma zamanı` **None** görünüyorsa CPU tekerleği kuruludur — Adım 4'teki CUDA komutuyla yeniden kurun.
- `CUDA var mı?` **False** ise GPU sürücü düzeyinde bile görünmüyordur: önce sürücüyü kontrol edin (Adım 3), sonra Adım 4'e dönün.
- `CUDA çalışma zamanı` değeri, `nvidia-smi`'deki "CUDA Version" üst sınırından yüksekse sürücü eskidir; önce sürücüyü güncelleyin.
- `BF16 desteği` **False** ise kartınız bf16'yı donatı düzeyinde bilmez; reçetelerde `bf16=True` yerine fp16 kullanmanız gerekir.
- Kurulum tamam ama sürüm kaynaklı bir hatayla karşılaşırsanız aynı üç çıktıyı [Sorun Giderme](/llm/sorun-giderme/) sayfasındaki "Sürüm Uyuşmazlıkları" (11. başlık) bölümündeki tanı adımlarıyla karşılaştırın; oradaki akış bu betikle aynı bilgiyi kullanır.

## Adım 6: İlk Kütüphaneler

Tek satırda temel kütüphane yığını:

```bash title="PowerShell"
pip install -U pip
pip install transformers datasets peft trl accelerate bitsandbytes
```

(uv ile çalışıyorsanız `pip` yerine `uv pip` yazın.)

- **transformers:** model ve tokenizer yükleme.
- **datasets:** veri yükleme, dönüştürme, bölme.
- **peft:** LoRA gibi adaptör yöntemleri.
- **trl:** SFT / DPO / GRPO eğitim döngüleri.
- **accelerate:** cihaz, karışık hassasiyet ve dağıtım yönetimi.
- **bitsandbytes:** 4-bit / 8-bit nicemleme (QLoRA'nın motoru).

:::note
bitsandbytes 2026 itibarıyla Windows'u resmî olarak destekliyor: kurulum dokümanı Windows x86-64 için derlenmiş tekerlekleri tablolar halinde listeler ve düz `pip install bitsandbytes` önerir (sistem gereksinimleri: Python 3.10+, PyTorch 2.4+). Yine de bu yığındaki en nazlı pakettir: `ImportError` ya da DLL hatası alırsanız önce güncel sürüme geçin, sorun sürerse [Sorun Giderme](/llm/sorun-giderme/) sayfasındaki sürüm başlıklarına ve aşağıdaki WSL2 bölümüne bakın.
:::

## HF Önbelleği: Nerede Birikir, Nasıl Taşınır?

Adım 6'daki kütüphaneler, indirdiğiniz her model ve veri setini varsayılan olarak kullanıcı klasörünüzde biriktirir: `C:\Users\<kullanıcı>\.cache\huggingface` (modeller `hub` alt klasöründe, model başına ayrı klasörde durur). Modeller GB'lar mertebesinde olduğundan bu klasör sessizce büyür; disk dolduğunda ilk bakılacak yer burasıdır.

İki pratik alışkanlık:

- **Yer açma:** Kullanmadığınız modellerin klasörlerini silebilirsiniz; bir sonraki kullanımda yeniden indirilir. Checkpoint'lerle birleşen genel disk stratejisi için [Sorun Giderme](/llm/sorun-giderme/) sayfasındaki "Disk Doldu" (8. başlık) bölümüne bakın.
- **Başka diske taşıma:** `HF_HOME` ortam değişkeni önbellek kökünü belirler. Windows'ta kalıcı atamak için:

```powershell title="PowerShell — HF_HOME'u kalıcı ayarla"
[Environment]::SetEnvironmentVariable("HF_HOME", "D:\hf-onbellek", "User")
```

Terminali yeniden açın; transformers, datasets ve hub kütüphaneleri indirme ve okuma işlemlerini bu kökten yapar. Mevcut önbelleği yeni konuma taşıdıysanız eski klasörü silebilirsiniz.

## Sürüm Sabitleme: 3 Ay Sonra Aynı Ortam

Bugün kurduğunuz yığının sürümlerini kaydetmek, üç ay sonra (ya da başka bir makinede) birebir aynı ortamı kurmanın en ucuz yoludur; "bir deneyde çalışmıştı ama nasıl?" dönemini kapatır. Kurulum tamamlandıktan sonra:

```bash title="PowerShell — o anki sürümleri kaydet"
pip freeze > requirements.txt
```

uv kullanıyorsanız karşılığı `uv pip compile`'dır:

```bash title="PowerShell — uv ile kilitleme"
uv pip compile pyproject.toml -o requirements.txt
```

`requirements.txt` dosyasını projenizin yanında saklayın. Aynı ortamı geri kurmak:

```bash title="PowerShell — aynı ortamı geri kur"
pip install -r requirements.txt
```

:::caution
PyTorch satırı, CUDA derlemesini belirten bir sürüm etiketi taşır (+cu130 benzeri); bu etiket varsayılan PyPI'da bulunmayabilir. Yeniden kurarken torch'u Adım 4'teki komutla (aynı index-url ile) kurup kalanı `requirements.txt` üzerinden geçirmek en güvenli sıradır.
:::

## Kurulum Sonu Duman Testi (GPU'suz)

Doğrulama betiği "paketler yüklü" der; uçtan uca akışın çalıştığını göstermez. Bir dakikalık duman testi bu boşluğu kapatır: transformers ile gerçekten çok küçük bir modeli indirip CPU'da çalıştırın. HF'te uzun süredir yaygın kullanılan `sshleifer/tiny-gpt2` (test amaçlı, minyatür bir GPT-2) bu iş için uygundur:

```python title="duman_testi.py"
from transformers import pipeline

pipe = pipeline("text-generation", model="sshleifer/tiny-gpt2")
cikti = pipe("Merhaba", max_new_tokens=8)
print(cikti[0]["generated_text"])
```

İlk çalıştırmada model, bir önceki bölümdeki HF önbelleğine iner; ardından CPU'da saniyeler içinde yanıt verir. Çıktı temsilîdir: tiny-gpt2 test amaçlı bir modeldir, ürettiği metnin anlamlı olması beklenmez; amaç "indir → yükle → çıkarım" zincirinin hatasız dönmesidir. Betik hata vermeden bittiyse ortamınız uçtan uca çalışıyor demektir; GPU tarafı Adım 5'teki betikle ayrıca teyit edilir.

## WSL2: Ne Zaman Gerekir?

WSL2 (Windows Subsystem for Linux 2), Windows içinde gerçek bir Linux çekirdeği çalıştırır. Eğitimlerin çoğu Windows'ta sorunsuz çalışır; ancak `flash-attn` gibi Linux için derlenmiş hız paketleri, Unsloth gibi bazı araçların en sorunsuz kurulumları ve README'lerdeki `bash` betikleri Linux tarafında daha rahattır. Kurulum: **yönetici** PowerShell'de `wsl --install`, yeniden başlatma ve Ubuntu hesabı oluşturma. Güncel adımlar: [Microsoft WSL kurulum dokümanı (Türkçe)](https://learn.microsoft.com/tr-tr/windows/wsl/install). Kurulumdan sonra Ubuntu terminalinde Adım 2-6'yı tekrarlarsınız; fark yalnızca komut adlarındadır (`python3`, `source .venv/bin/activate`).

:::note
**WSL2'de iki pratik not.** (1) Sürücü Windows tarafında kalır: NVIDIA'nın CUDA-on-WSL kılavuzu, WSL içine Linux GPU sürücüsü kurulmamasını açıkça söyler; sürücüyü yalnızca Windows'ta güncel tutarsınız ve WSL içindeki `nvidia-smi` onu görür. WSL'e ayrı bir CUDA Toolkit kurmak da gerekmez — PyTorch'un pip tekerlekleri CUDA çalışma zamanını kendileri getirir; toolkit yalnızca kendi CUDA kodunuzu derleyecekseniz gerekir. (2) Proje dosyalarını WSL'in kendi dosya sisteminde (ör. `~/projelerim`) tutun: Microsoft'un WSL dokümanı, Linux araçlarıyla çalışırken en hızlı performansın bu biçimde alındığını belirtir; `/mnt/c` üzerinden çalışmak özellikle çok sayıda küçük dosyada (veri seti, checkpoint) belirgin yavaştır.
:::

:::note
**Git Bash yeterli mi?** Hayır. Git Bash yalnızca bir kabuk (shell) sağlar; Linux ortamı, Linux paketleri veya farklı CUDA davranışı getirmez. `bash` komutlarını rahatça çalıştırmak için güzeldir ama "Linux'a özgü araç" sorunlarını çözmez — bunun için WSL2 gerekir. Araçlarınız Linux'a özel değilse Windows'ta kalmanız da tamamen geçerlidir.
:::

## Sık Karşılaşılan Kurulum Hataları

| Hata mesajı | Anlamı | Çözüm |
| --- | --- | --- |
| `'pip' is not recognized...` | Python PATH'te değil ya da yanlış terminal | Terminali yeniden açın; `python -m pip --version` deneyin; Python'u "Add to PATH" ile yeniden kurun |
| `torch not compiled with CUDA enabled` | CPU sürümü kurulu | Adım 4'teki CUDA komutuyla (güncel index-url) yeniden kurun |
| `ImportError: DLL load failed while importing torch` | Eksik sistem bileşeni veya bozuk kurulum | [Microsoft Visual C++ Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe) kurun; `pip install --force-reinstall torch` |
| `UnicodeEncodeError` / bozuk Türkçe karakterler | Konsol kod sayfası veya dosya kodlaması | Terminalde `chcp 65001`; dosyaları UTF-8 (BOM'suz) kaydedin |
| "Uzun yol" / "path too long" uyarıları | 260 karakter sınırı | Projeyi kısa yola taşıyın (`C:\ml\...`); Uzun Yollar'ı etkinleştirin (gpedit → Bilgisayar Yapılandırması → Yönetim Şablonları → Sistem → Dosya Sistemi) |
| `No module named 'torch'` | Sanal ortam aktif değil | `.\.venv\Scripts\Activate.ps1`; `where python` ile kontrol edin |
| `CUDA out of memory` | Kurulum değil, VRAM sorunu | [VRAM Hesabı](/donanim/vram-hesabi/) |

## Kaynaklar ve İleri Okuma

- [Python İndirmeleri](https://www.python.org/downloads/) — Windows kurulumunun resmî kaynağı; güncel sürümler ve sürüm notları.
- [uv Dokümantasyonu](https://docs.astral.sh/uv/) — kurulum betiği, `uv venv` ve `uv pip` komutlarının resmî referansı.
- [PyTorch: Get Started Locally](https://pytorch.org/get-started/locally/) — güncel stabil sürüm; Windows + pip + CUDA kurulum komutunu üreten seçici.
- [NVIDIA Sürücü İndirme](https://www.nvidia.com/Download/index.aspx) — kart modelinize ve Windows sürümünüze uygun güncel sürücü.
- [Microsoft WSL Kurulumu](https://learn.microsoft.com/tr-tr/windows/wsl/install) — WSL2'nin resmî kurulum adımları; geliştirme ortamı önerileri için [ortam kurulum rehberine](https://learn.microsoft.com/en-us/windows/wsl/setup/environment) bakın.
- [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) — "DLL load failed" hatalarının ilk şüphelisi olan sistem bileşeninin resmî indirme sayfası.
- [bitsandbytes Kurulum Dokümanı](https://huggingface.co/docs/bitsandbytes/installation) — platform desteği, sistem gereksinimleri ve işletim sistemi başına tekerlek tabloları.

## Sırada Ne Var?

- GPU'nuz zayıfsa veya yoksa: [Bulut Seçenekleri](/donanim/bulut-secenekleri/)
- Araç seçimi ve eğitim akışı: [Adım Adım Eğitim](/llm/adim-adim-egitim/)
- Eğitim araçlarına genel bakış: [Araçlar](/llm/araclar/)
- İlk veri setiniz: [Veri Nereden Bulunur?](/veri/veri-nereden-bulunur/)
