---
title: "Faydalı Linkler ve Kaynaklar"
description: "Öğrenme kaynakları, temel makaleler, eğitim araçları, veri setleri ve topluluklar: 2026 itibarıyla doğrulanmış küratörlü link listesi."
dogrulama: 2026-10-17
---

Bu sayfa, rehber boyunca önerdiğimiz kaynakların kategorilere ayrılmış tek listesidir. Her bağlantının yanındaki cümle neden faydalı olduğunu anlatır. Liste canlı tutulmalıdır; **2026 itibarıyla bağlantılar doğrulanmıştır.**

## Öğrenme ve kurslar

- [Hugging Face LLM Course](https://huggingface.co/learn) — Transformer'dan ince ayara uzanan, ücretsiz ve uygulamalı resmi kurs; bu rehberin en doğal İngilizce tamamlayıcısı.
- [Hugging Face Blog](https://huggingface.co/blog) — Yeni modeller, teknikler ve kütüphane duyuruları üzerine düzenli ve güvenilir yazılar.
- [DeepLearning.AI](https://www.deeplearning.ai) — Andrew Ng'nin kısa ve uygulamalı kursları; temel ML ve LLM konularına hızlı giriş.
- [3Blue1Brown — Sinir Ağları Serisi](https://www.3blue1brown.com/topics/neural-networks) — Animasyonlarla sinir ağları ve geri yayılım sezgisi; matematikten korkanların ilk durağı olmalı.
- [Andrej Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html) — Videolarla sıfırdan dil modeli inşa etme; "içeride ne oluyor?" sorusunun en iyi cevabı.
- [MIT 6.S191 — Introduction to Deep Learning](https://introtodeeplearning.com) — MIT'nin ünlü yoğun dersi; slayt ve laboratuvarlarla derin öğrenmeye akademik ama erişilebilir bir giriş.

## Temel makaleler

- [Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762) — Transformer mimarisini tanıtan, bugünkü tüm LLM'lerin atası olan makale.
- [LoRA (2021)](https://arxiv.org/abs/2106.09685) — Düşük rütbeli adaptörlerle verimli ince ayarın orijinal çalışması.
- [QLoRA (2023)](https://arxiv.org/abs/2305.14314) — 4-bit nicemlenmiş taban modeller üzerinde LoRA eğitimi; tek GPU'da büyük modelleri mümkün kılan yöntem.
- [Chinchilla (2022)](https://arxiv.org/abs/2203.15556) — "Ne kadar veri, ne kadar parametre?" sorusunu ölçek yasalarıyla yanıtlayan çalışma.
- [InstructGPT / RLHF (2022)](https://arxiv.org/abs/2203.02155) — GPT modellerinin insan geri bildirimiyle nasıl hizalandığını anlatan temel makale.
- [DPO (2023)](https://arxiv.org/abs/2305.18290) — RLHF'ye göre çok daha basit ve pratik bir hizalama alternatifi.
- [LIMA (2023)](https://arxiv.org/abs/2305.11206) — 1.000 özenle seçilmiş örnekle şaşırtıcı derecede iyi hizalamanın mümkün olduğunu gösteren çalışma.

## Eğitim ve ince ayar araçları

- [unslothai/unsloth](https://github.com/unslothai/unsloth) — Daha hızlı ve daha az VRAM'le ince ayar; Windows dahil en kolay başlangıç araçlarından biri.
- [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) — Yüzlerce modeli tek arayüz veya CLI üzerinden eğitme imkânı.
- [axolotl-ai-cloud/axolotl](https://github.com/axolotl-ai-cloud/axolotl) — YAML yapılandırmalarıyla üretim kalitesinde eğitim akışları.
- [huggingface/trl](https://github.com/huggingface/trl) — Hugging Face'in resmi SFT, DPO ve GRPO eğitim kütüphanesi.
- [huggingface/peft](https://github.com/huggingface/peft) — LoRA ve benzeri verimli ince ayar yöntemlerinin referans uygulaması.
- [huggingface/transformers](https://github.com/huggingface/transformers) — Tüm ekosistemin temel taşı; model yükleme, eğitim ve çıkarımın standart kütüphanesi.
- [UKPLab/sentence-transformers](https://github.com/UKPLab/sentence-transformers) — Gömme modeli eğitiminin referans kütüphanesi; kayıplar, `mine_hard_negatives` ve [eğitim genel bakışı belgesi](https://sbert.net/docs/sentence_transformer/training_overview.html) burada. [Gömme Modeli Eğitmek](/rag/gomme-egitimi/) sayfasındaki kafes bu kütüphaneyle kuruldu.

## Çalıştırma ve sunum araçları

- [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — GGUF ekosisteminin kalbi; nicemleme araçları ve CPU/GPU çıkarımının kaynağı.
- [ollama/ollama](https://github.com/ollama/ollama) — Windows'ta tek kurulumla yerel modeller; başlangıç için en kolay yol.
- [vllm-project/vllm](https://github.com/vllm-project/vllm) — Yüksek eşzamanlılık için GPU sunum motoru; üretim ortamlarının standardı.
- [huggingface/text-generation-inference (TGI)](https://github.com/huggingface/text-generation-inference) — Hugging Face'in Docker tabanlı üretim sunum motoru.
- [open-webui/open-webui](https://github.com/open-webui/open-webui) — Ollama için sohbet arayüzü; dosya yükleme ve RAG desteğiyle yerel AI platformu hissi.
- [LM Studio](https://lmstudio.ai) — GGUF modelleri grafik arayüzle indirip sohbet etme; kod yazmadan denemek isteyenler için.

## Görsel model araçları

- [kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts) — Görsel modellerde LoRA eğitiminin endüstri standardı araç seti.
- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) — En yaygın Stable Diffusion arayüzü; eğitim eklentileriyle birlikte.
- [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) — Düğüm tabanlı görsel üretim akışları; karmaşık işlem hatlarını görselleştirir.
- [huggingface/diffusers](https://github.com/huggingface/diffusers) — Diffusion modellerini Python'dan çalıştırma ve eğitme kütüphanesi.

## Veri kaynakları

- [Hugging Face Datasets](https://huggingface.co/datasets) — On binlerce hazır veri seti; filtreleyip doğrudan `datasets` kütüphanesiyle yükleyebilirsiniz.
- [FineWeb-2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) — Türkçe dahil çok dilli, web ölçeğinde temizlenmiş ön eğitim veri seti.
- [atasoglu — Turkish Instruction Datasets](https://huggingface.co/collections/atasoglu/turkish-instruction-datasets) — Türkçe talimat veri setlerinin derli toplu koleksiyonu; ince ayar için ilk bakılacak yer.
- [ogulcanaydogan/Turkish-LLM](https://github.com/ogulcanaydogan/Turkish-LLM) — Türkçe LLM çalışmaları: veri, model ve deneylerin toplandığı açık depo (Hugging Face profili: [ogulcanaydogan](https://huggingface.co/ogulcanaydogan)).
- [kesimeg/awesome-turkish-language-models](https://github.com/kesimeg/awesome-turkish-language-models) — Türkçe dil modelleri ve kaynaklarının küratörlü listesi.
- [Holmeister Türkçe Değerlendirme Koleksiyonu](https://huggingface.co/collections/Holmeister/turkish-llm-multi-prompt-evaluation-datasets) — 17 Türkçe veri seti ve çoklu istem düzeniyle model değerlendirme paketi.
- [Kaggle Datasets](https://www.kaggle.com/datasets) — Yarışma ve topluluk veri setleri; klasik ML projeleri için zengin kaynak.
- [Common Crawl](https://commoncrawl.org) — Web ölçeğinde açık tarama verisi; ön eğitim verisinin ham maddesi.

## Topluluk ve takip

- [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA) — Yerel model çalıştırma ve eğitme topluluğu; donanım, nicemleme ve araç tartışmalarının merkezi.
- [Hugging Face Discord](https://huggingface.co/join/discord) — Hugging Face topluluğunun canlı sohbet ortamı; hızlı soru-cevap için birebir.
- [Hugging Face Forum](https://discuss.huggingface.co) — Kütüphaneler, modeller ve veri setleri hakkında arama yapılabilir soru-cevap arşivi.
- [r/MachineLearning](https://www.reddit.com/r/MachineLearning) — Akademik ve genel makine öğrenmesi tartışmaları; yeni makalelerin özetleri.
- Türkçe topluluklar: Üniversite yapay zeka kulüplerinin Discord/Telegram grupları ve Türkçe ML forumları hızla değiştiği için buraya sabit bir bağlantı koymuyoruz; güncel toplulukları arama motorundan "yapay zeka topluluğu Discord" gibi terimlerle bulabilirsiniz.

---

:::tip
Bu listede önerdiğimiz akış: önce [Yol Haritası](/baslangic/yol-haritasi/) ile sıranızı belirleyin, öğrenirken [Sözlük](/kaynaklar/sozluk/) ve [SSS](/kaynaklar/sss/) sayfalarını yanınızda tutun, derinleşmek istediğiniz konuda buradaki kaynaklara geçin.
:::
