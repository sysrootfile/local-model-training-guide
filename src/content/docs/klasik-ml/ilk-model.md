---
title: "İlk Modelin: Uçtan Uca scikit-learn Örneği"
description: Iris çiçek veri setiyle veri yüklemeden yeni örnek tahminine kadar eksiksiz bir scikit-learn iş akışını satır satır açıklıyoruz.
dogrulama: 2026-10-17
---

Teoriyi bir kenara bırakıp ilk modelinizi eğitme zamanı. Senaryomuz: 4 ölçümden (çanak ve taç yaprakların uzunluk-genişliği) bir çiçeğin türünü tahmin etmek. Kullanacağımız **Iris veri seti**, scikit-learn'ün içinde paketli gelir — indirme, dosya arama, ayıklama yok. 150 örnek, 3 sınıf, 4 özellik: hem gerçek hem de öğrenmek için ideal boyutta.

:::note[Ön koşul]
Bilgisayarınızda Python ve şu iki paket kurulu olmalı: `pip install scikit-learn pandas`. Kurulumla uğraşmak istemiyorsanız [Yerel Kurulum](/donanim/yerel-kurulum/) sayfasındaki adımlar Windows'a göre anlatıyor.
:::

## Tek dosyalık, uçtan uca betik

Aşağıdaki betiği `ilk_model.py` olarak kaydedin ve `python ilk_model.py` ile çalıştırın. Yorumlar, her adımın **neden** yapıldığını anlatıyor:

```python title="ilk_model.py"
# ---------------------------------------------------------------------------
# Uçtan uca ilk model: Iris çiçek türü sınıflandırma (rastgele orman)
# Çalıştırmadan önce: pip install scikit-learn pandas
# ---------------------------------------------------------------------------

# 1) Gerekli kütüphaneleri içe aktar
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 2) Veriyi yükle -------------------------------------------------------------
#    Iris veri seti scikit-learn ile birlikte gelir; internetten indirmek gerekmez.
iris = load_iris()

#    X = özellikler (4 ölçüm), y = hedef (0, 1, 2 → üç çiçek türü)
X, y = iris.data, iris.target

#    Önce gözle bakalım: tabloya çevirip ilk satırları yazdıralım.
df = pd.DataFrame(X, columns=iris.feature_names)
df["tur"] = y
print("İlk 5 satır:")
print(df.head())

# 3) Küçük bir keşif: özet istatistikler ve sınıf dağılımı --------------------
#    Ortalama, standart sapma, min/maks değerleri görürüz.
print("\nÖzet istatistikler:")
print(df.describe().round(2))

#    Üç türden de kaçar örnek var? (Dengeli bir veri seti bekleriz)
print("\nSınıf dağılımı:")
print(df["tur"].value_counts().sort_index())

# 4) Eğitim / test ayrımı ------------------------------------------------------
#    Verinin %80'i eğitim, %20'si test için ayrılır.
#    stratify=y    -> sınıf oranları her iki kümede de korunur
#    random_state  -> bölünme her çalıştırmada aynı olsun (tekrarlanabilirlik)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 5) Modeli seç: rastgele orman -------------------------------------------------
#    100 karar ağacı eğitilir; tahmin, ağaçların çoğunluk oyuyla verilir.
#    Neden bu model? Ayarları affeden, tablo verisinde az emekle iyi sonuç
#    veren bir başlangıçtır. Tek ağacın ezberleme eğilimini, çok sayıda
#    ağacın ortalamasını alarak dengeler.
model = RandomForestClassifier(n_estimators=100, random_state=42)

# 6) Eğitim: model örneklerden örüntüleri öğrenir ------------------------------
model.fit(X_train, y_train)

# 7) Değerlendirme: hiç görülmemiş test verisi üzerinde ------------------------
y_pred = model.predict(X_test)

print("\nDoğruluk (accuracy):", round(accuracy_score(y_test, y_pred), 2))
print("\nSınıf bazında rapor:")
print(classification_report(y_test, y_pred, target_names=iris.target_names))

# 8) Karışıklık matrisi: hangi tür, hangi türle karıştırıldı? ------------------
print("Karışıklık matrisi (satır = gerçek, sütun = tahmin):")
print(confusion_matrix(y_test, y_pred))

# 9) Hangi ölçüm daha belirleyici? ---------------------------------------------
#    feature_importances_, her özelliğin karara katkısını 0-1 arasında verir.
print("\nÖzellik önemleri:")
for isim, onem in zip(iris.feature_names, model.feature_importances_):
    print(f"  {isim:>25}: {onem:.3f}")

# 10) Yeni bir örnekle tahmin ---------------------------------------------------
#     Ölçüleri elle girdiğimiz hayali bir çiçek (4 değer, eğitimdeki sırayla):
yeni_ornek = [[5.1, 3.5, 1.4, 0.2]]

tahmin = model.predict(yeni_ornek)[0]           # hangi tür? (0, 1 veya 2)
olasiliklar = model.predict_proba(yeni_ornek)[0] # her tür için olasılık

print("\nYeni örnek için tahmin:", iris.target_names[tahmin])
print("Sınıf olasılıkları:")
for tur_adi, p in zip(iris.target_names, olasiliklar):
    print(f"  {tur_adi}: {p:.2f}")
```

## Çıktıyı okuyalım

Aşağıdaki çıktı **örnektir** — sayılar sürüme ve ortama göre küçük farklar gösterebilir; önemli olan biçimi ve nasıl okunacağını öğrenmek:

```text title="örnek çıktı"
Doğruluk (accuracy): 0.93

Sınıf bazında rapor:
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       0.90      0.90      0.90        10
   virginica       0.90      0.90      0.90        10

    accuracy                           0.93        30
   macro avg       0.93      0.93      0.93        30
weighted avg       0.93      0.93      0.93        30

Karışıklık matrisi (satır = gerçek, sütun = tahmin):
[[10  0  0]
 [ 0  9  1]
 [ 0  1  9]]

Özellik önemleri:
         sepal length (cm): 0.10
          sepal width (cm): 0.02
        petal length (cm): 0.44
         petal width (cm): 0.44

Yeni örnek için tahmin: setosa
Sınıf olasılıkları:
  setosa: 1.00
  versicolor: 0.00
  virginica: 0.00
```

Her bölümün anlamı:

- **Doğruluk 0.93:** Test kümesindeki 30 örnekten 28'i doğru. Iris küçük ve "kolay" bir veri setidir; bu ayarlarla tipik olarak %90-97 bandında sonuç görürsünüz. Burada yüksek çıktı sizi yanıltmasın — gerçek dünya verisinde aynı ayarlar genelde %70-90 bandında dolaşır; bu yüzden metriği hep **veri setinizin bağlamında** yorumlayın.
- **precision / recall / f1-score:** Sınıf bazında üçlü skorlar ([metriklerin ne anlama geldiği](/klasik-ml/temeller/)). Örnekte versicolor ve virginica %90'da; ikisinin karıştırıldığı ve setosanın hiç karışmadığı görülüyor. Bir sınıf 1.00 alırken diğerleri 0.9'sa, iyileştirme çabasını düşük skorlu sınıfa yöneltirsiniz.
- **support:** Her sınıfın test setinde kaç örneği olduğu (10+10+10=30). Dengesiz veri setlerinde bu sayılar sınıflar arasında çok farklıysa, `macro avg` satırını okumaya özen gösterin.
- **Karışıklık matrisi:** 3x3 tablonun satırları gerçek tür, sütunları tahmin. Köşegen dışındaki hücreler hatalardır: bir versicolor bir kez virginica sanılmış, bir virginica da bir kez versicolor. Hangi türün hangisiyle karıştığı, modeli iyileştirmenin yol haritasıdır (ör. bu ikisi çok mu benzer?). Iris'te bu iki tür doğal olarak en çok karışan çifttir.
- **Özellik önemleri:** Modelin kararında en çok **taç yaprak (petal)** ölçümleri belirleyici olmuş (toplam ~0.88); çanak yaprak genişliği neredeyse hiç işe yaramamış. Bu tür içgörüler, hangi ölçümü toplamaya değer olduğunu söyler — veri toplama maliyetini düşürür.
- **Yeni örnek:** 5.1 / 3.5 / 1.4 / 0.2 ölçüleri tipik bir setosa profili; model "setosa" demiş ve olasılığı 1.00 vermiş. `predict` kararı verirken, `predict_proba` kararın **ne kadar kesin** olduğunu gösterir: 0.55-0.45 gibi bir dağılım görürseniz model o örnekte tereddüt ediyordur.

:::tip
Değeri düşürmek ya da yükseltmek için `random_state`, `test_size` ve `n_estimators` değerlerini değiştirip tekrar çalıştırın. Kayıp (loss) ve diğer değerlendirme kavramları için: [Loss ve Metrikler](/degerlendirme/loss-ve-metrikler/).
:::

## Alternatif: aynı işi 5 satırda yapan model

Rastgele orman yerine lojistik regresyon da dener misiniz? scikit-learn'ün "aynı API" avantajı sayesinde değişen tek şey model satırıdır:

```python title="lojistik_regresyon.py"
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)

model = LogisticRegression(max_iter=200)   # max_iter: uyarıyı önlemek için
model.fit(X_train, y_train)
print("Doğruluk:", round(accuracy_score(y_test, model.predict(X_test)), 2))
```

Iris'te iki model de benzer bandda sonuç verir. Gerçek işlerde seçim şu sorulara bağlıdır: en iyi skoru mu arıyorsunuz (genelde orman/gradyan artırma), yoksa 10 kat daha hızlı eğitim ve açıklanabilir katsayılar mı (lojistik regresyon)?

## Sık yapılan hatalar

:::caution
- **Test verisine `fit` etmek:** Tüm `fit` çağrıları eğitim verisiyle yapılır. Test setine dokunan her satır, karnenizi şişirir ve gerçek performansı gizler — buna veri sızıntısı (data leakage) denir.
- **Ölçekleme (scaling) unutmak:** Bu örnekte tüm ölçümler santimetre cinsinden olduğu için gerekmedi; ama yaş (0-100) ile gelir (0-1.000.000) yan yana geldiğinde KNN, SVM ve doğrusal modeller bozulur. Böyle durumlarda `StandardScaler` kullanın (ağaç tabanlı modeller genelde ölçekten etkilenmez).
- **Doğrulama setini yok sayıp testi harcamak:** Ayar yapa yapa test setine bakarsanız, o da öğrenilmiş veriye döner. Denemeler için doğrulama (validation) ayırın, testi en sona saklayın.
- **Az veriyle kesin konuşmak:** 30 test örneğinde tek hata ~%3'lük oynama yapar. Küçük test setlerindeki farklar "iyileşme" değil, şans olabilir.
- **`random_state` koymamak:** Aynı betik her çalıştırmada farklı sonuç verirse hata ayıklamak imkânsızlaşır. Bir de neyi sabitlediğinizi ayırt edin: aynı veri üzerinde ölçülen sonuçlara göre bölmeyi sabit tutup yalnız model tohumunu değiştirmek doğruluğu çok az oynatıyor, bölmenin kendisini değiştirmek ise belirgin biçimde daha fazla — ayrıntı [Tekrarlanabilirlik](/kullanim/tekrarlanabilirlik/) sayfasında.
:::

## Sonraki adımlar

Sıradaki üç yön:

1. **Gradyan artırma:** Aynı Iris betiğinde `RandomForestClassifier` yerine XGBoost veya LightGBM modellerini (ör. `LGBMClassifier`) deneyin; genelde bir tık daha iyi skor verir. Kavram turu: [Klasik ML Temelleri](/klasik-ml/temeller/).
2. **Kendi tablonuzla deneme:** Elinizdeki bir Excel/CSV dosyasını `pd.read_csv` ile yükleyip aynı akışı uygulayın. Metin sütunlarını sayıya çevirme gibi işler için [Veri Temizleme](/veri/veri-temizleme/) sayfasına bakın.
3. **Derin öğrenmeye geçiş:** Veri metne döndüğünde akış değişir, kavramlar değişmez. Benchmark dünyası için: [Benchmarklar](/degerlendirme/benchmarklar/).

Artık bir modelin baştan sona nasıl eğitildiğini gördünüz — veri bölündü, model öğrendi, hiç görülmemiş veriyle değerlendirildi, yeni bir tahmin üretildi. LLM'de de akış aynı: **veri → eğitim → değerlendirme.** Sadece ölçek, veri tipi ve araçlar büyüyor.

Devam: [LLM'lerde Adım Adım Eğitim](/llm/adim-adim-egitim/)
