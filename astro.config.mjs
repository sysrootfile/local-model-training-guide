// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'Model Eğitimi Rehberi',
      description:
        'Türkçe, sıfırdan ileri seviyeye model eğitimi rehberi: veri bulma, veri hazırlama, fine-tuning, LoRA/QLoRA, değerlendirme ve yayınlama.',
      favicon: '/favicon.svg',
      defaultLocale: 'root',
      locales: {
        root: { label: 'Türkçe', lang: 'tr' },
      },
      credits: false,
      customCss: ['./src/styles/custom.css'],
      // Sayfanın `dogrulama` damgası bayatlayınca üstte banner basılır: src/starlightRouteData.ts
      routeMiddleware: './src/starlightRouteData.ts',
      sidebar: [
        {
          label: 'Başlangıç',
          items: [
            { slug: 'baslangic/giris' },
            { slug: 'baslangic/kavramlar' },
            { slug: 'baslangic/yol-haritasi' },
          ],
        },
        {
          label: 'Temeller',
          items: [
            { slug: 'temeller/transformer' },
            { slug: 'temeller/tokenizasyon' },
            { slug: 'temeller/egitim-nasil-calisir' },
          ],
        },
        {
          label: 'RAG',
          items: [
            { slug: 'rag/rag-mi-ince-ayar-mi' },
            { slug: 'rag/rag-degerlendirme' },
            { slug: 'rag/parcalama-ve-hibrit-arama' },
            { slug: 'rag/gomme-egitimi' },
          ],
        },
        {
          label: 'Ajanlar ve Araç Çağırma',
          items: [
            { slug: 'ajan/ajan-mi-sabit-hat-mi' },
            { slug: 'ajan/arac-cagirma-ve-mcp' },
            { slug: 'ajan/ajan-olcumu' },
            { slug: 'ajan/prompt-enjeksiyonu' },
            { slug: 'ajan/enjeksiyon-olcumu' },
          ],
        },
        {
          label: 'Donanım ve Ortam',
          items: [
            { slug: 'donanim/vram-hesabi' },
            { slug: 'donanim/yerel-kurulum' },
            { slug: 'donanim/bulut-secenekleri' },
          ],
        },
        {
          label: 'Veri',
          items: [
            { slug: 'veri/veri-turleri' },
            { slug: 'veri/veri-nereden-bulunur' },
            { slug: 'veri/veri-formatlari' },
            { slug: 'veri/veri-temizleme' },
            { slug: 'veri/kendi-verini-olustur' },
          ],
        },
        {
          label: 'LLM Eğitimi',
          items: [
            { slug: 'llm/pretraining' },
            { slug: 'llm/sft' },
            { slug: 'llm/lora-qlora' },
            { slug: 'llm/dpo-rlhf' },
            { slug: 'llm/araclar' },
            { slug: 'llm/adim-adim-egitim' },
            { slug: 'llm/hiperparametreler' },
            { slug: 'llm/sorun-giderme' },
          ],
        },
        {
          label: 'Görsel Model Eğitimi',
          items: [
            { slug: 'gorsel/diffusion-temelleri' },
            { slug: 'gorsel/lora-egitimi' },
          ],
        },
        {
          label: 'Klasik Makine Öğrenmesi',
          items: [
            { slug: 'klasik-ml/temeller' },
            { slug: 'klasik-ml/ilk-model' },
          ],
        },
        {
          label: 'Değerlendirme',
          items: [
            { slug: 'degerlendirme/loss-ve-metrikler' },
            { slug: 'degerlendirme/benchmarklar' },
          ],
        },
        {
          label: 'Kullanım ve Yayınlama',
          items: [
            { slug: 'kullanim/lora-birlestirme' },
            { slug: 'kullanim/quantization' },
            { slug: 'kullanim/ollama' },
            { slug: 'kullanim/cikarim-parametreleri' },
            { slug: 'kullanim/tekrarlanabilirlik' },
            { slug: 'kullanim/eminlik-ve-kalibrasyon' },
            { slug: 'kullanim/hiz-ve-maliyet' },
            { slug: 'kullanim/eszamanlilik' },
            { slug: 'kullanim/sunma-api' },
            { slug: 'kullanim/huggingface-paylasim' },
            { slug: 'kullanim/lisans-ve-model-karti' },
          ],
        },
        {
          label: 'Örnek Projeler',
          items: [
            { slug: 'ornekler/genel-bakis' },
            { slug: 'ornekler/klasik-ml' },
            { slug: 'ornekler/veri-temizleme' },
            { slug: 'ornekler/turkce-asistan' },
            { slug: 'ornekler/gorsel-lora' },
            { slug: 'ornekler/yerel-rag' },
            { slug: 'ornekler/viki-rag' },
            { slug: 'ornekler/ajan-dongusu' },
            { slug: 'ornekler/enjeksiyon-deni' },
            { slug: 'ornekler/ucdan-uca' },
          ],
        },
        {
          label: 'Kaynaklar',
          items: [
            { slug: 'kaynaklar/sss' },
            { slug: 'kaynaklar/sozluk' },
            { slug: 'kaynaklar/faydali-linkler' },
            { slug: 'kaynaklar/dogrulama-mekanizmasi' },
            { slug: 'kaynaklar/agent-ve-cok-makine' },
            { slug: 'kaynaklar/kapsam-haritasi' },
          ],
        },
      ],
    }),
  ],
});
