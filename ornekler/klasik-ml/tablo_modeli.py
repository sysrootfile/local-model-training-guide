# ---------------------------------------------------------------------------
# Örnek Proje 1: Tablo verisiyle uçtan uca makine öğrenmesi
# Veri: veri/breast_cancer.csv — göğüs kanseri teşhis veri seti
#       (569 hasta, 30 sayısal özellik, hedef: 0 = kötü huylu / 1 = iyi huylu)
#       Kaynak: scikit-learn deposundaki herkese açık veri dosyası.
#
# Kurulum:  pip install pandas scikit-learn joblib
# Çalıştır: python tablo_modeli.py  (bu klasörden)
#
# Akış: keşif (EDA) -> ayırma -> ön işleme + model (Pipeline) -> baseline ->
#       çapraz doğrulama -> test değerlendirmesi -> model kaydı -> tahmin
# ---------------------------------------------------------------------------

from pathlib import Path
import sys

# Windows konsolları varsayılan olarak UTF-8 dışı bir kodlama (ör. cp1252)
# kullanır; Türkçe karakterler yazdırılırken hata vermesin diye çıktıyı
# UTF-8'e sabitliyoruz. (reconfigure her ortamda bulunmaz, korumalı çağırıyoruz.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42  # sonuçların her çalıştırmada aynı çıkması için sabit tohum
VERI_YOLU = Path(__file__).parent / "veri" / "breast_cancer.csv"
CIKTI_KLASORU = Path(__file__).parent / "cikti"

# Veri setinin 30 özelliğinin standart adları (CSV'de yalnızca sayılar var).
OZELLIK_ADLARI = [
    "mean radius", "mean texture", "mean perimeter", "mean area", "mean smoothness",
    "mean compactness", "mean concavity", "mean concave points", "mean symmetry",
    "mean fractal dimension", "radius error", "texture error", "perimeter error",
    "area error", "smoothness error", "compactness error", "concavity error",
    "concave points error", "symmetry error", "fractal dimension error",
    "worst radius", "worst texture", "worst perimeter", "worst area",
    "worst smoothness", "worst compactness", "worst concavity",
    "worst concave points", "worst symmetry", "worst fractal dimension",
]


def baslik(metin: str) -> None:
    """Çıktıyı bölümlere ayırmak için basit bir başlık yazdırır."""
    print("\n" + "=" * 60)
    print(metin)
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1) Veriyi yükle
#    CSV'nin ilk satırı metadata (örnek/sütun sayısı ve sınıf adları);
#    skiprows=1 ile atlıyoruz. Başlık satırı olmadığı için header=None
#    verip sütun adlarını kendimiz koyuyoruz.
# ---------------------------------------------------------------------------
baslik("1) Veri yükleme")

ilk_satir = VERI_YOLU.read_text(encoding="utf-8").splitlines()[0]
n_ornek, n_ozellik, sinif_adi_0, sinif_adi_1 = ilk_satir.split(",")

df = pd.read_csv(VERI_YOLU, skiprows=1, header=None)
df.columns = OZELLIK_ADLARI + ["hedef"]
df["hedef"] = df["hedef"].astype(int)

print(f"Kaynak dosya : {VERI_YOLU.name}")
print(f"Satır sayısı : {df.shape[0]} (metadata: {n_ornek} hasta, {n_ozellik} özellik)")
print(f"Sınıflar     : 0 = {sinif_adi_0}, 1 = {sinif_adi_1}")
print(f"\nİlk 3 satır (ilk 5 sütun):")
print(df.iloc[:3, :5].to_string())

# ---------------------------------------------------------------------------
# 2) Keşifsel veri analizi (EDA): sınıf dengesi ve eksik değer kontrolü
# ---------------------------------------------------------------------------
baslik("2) Keşif: sınıf dengesi ve eksik değerler")

sinif_sayilari = df["hedef"].value_counts().sort_index()
print("Sınıf dağılımı:")
print(f"  0 ({sinif_adi_0:9s}): {sinif_sayilari[0]} hasta")
print(f"  1 ({sinif_adi_1:9s}): {sinif_sayilari[1]} hasta")
print(f"  Dengesizlik oranı: {sinif_sayilari.min() / sinif_sayilari.max():.2f}")

eksik = df.isnull().sum().sum()
print(f"\nToplam eksik değer: {eksik}")
if eksik > 0:
    print("Eksik değer olan sütunlar:")
    print(df.isnull().sum()[df.isnull().sum() > 0])

# ---------------------------------------------------------------------------
# 3) Eğitim / test ayırımı
#    - stratify=y: sınıf oranları hem eğitimde hem testte korunur
#    - test_size=0.2: verinin %20'si hiç görülmemiş "sınav" verisi olur
# ---------------------------------------------------------------------------
baslik("3) Eğitim ve test kümelerine ayırma")

X = df.drop(columns="hedef")
y = df["hedef"]
X_egitim, X_test, y_egitim, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
print(f"Eğitim kümesi: {X_egitim.shape[0]} hasta")
print(f"Test kümesi  : {X_test.shape[0]} hasta")

# ---------------------------------------------------------------------------
# 4) Ön işleme + model: Pipeline
#    Ölçekleme (StandardScaler) SADECE eğitim verisiyle öğrenilir; Pipeline
#    bunu otomatik halleder ve sızıntıyı (leakage) önler.
# ---------------------------------------------------------------------------
baslik("4) Modelleri pipeline olarak tanımlama")

modeller = {
    "Lojistik Regresyon": Pipeline(
        [
            ("olcekle", StandardScaler()),
            ("model", LogisticRegression(max_iter=5000, random_state=RANDOM_STATE)),
        ]
    ),
    "Rastgele Orman": Pipeline(
        [
            ("model", RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE)),
        ]
    ),
}
for isim in modeller:
    print(f"  - {isim} hazır")

# ---------------------------------------------------------------------------
# 5) Baseline: "her zaman en sık sınıfı tahmin et" modeli
#    Bir modelin gerçekten işe yarayıp yaramadığını ancak bir taban çizgisiyle
#    karşılaştırarak anlarız.
# ---------------------------------------------------------------------------
baslik("5) Baseline (taban çizgisi) model")

baseline = DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE)
baseline.fit(X_egitim, y_egitim)
baseline_dogruluk = accuracy_score(y_test, baseline.predict(X_test))
print(f"Baseline test doğruluğu: {baseline_dogruluk:.4f}")
print("(Bu, verideki en sık sınıfın oranıdır; bunun üzeri katkı demektir.)")

# ---------------------------------------------------------------------------
# 6) Çapraz doğrulama ile model karşılaştırma
#    5 parçalı (5-fold) çapraz doğrulama: veri 5 parçaya bölünür, her parça
#    sırayla doğrulama olarak kullanılır. Test kümesine HENÜZ dokunmadık.
# ---------------------------------------------------------------------------
baslik("6) 5-fold çapraz doğrulama (eğitim kümesi üzerinde)")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
for isim, model in modeller.items():
    skorlar = cross_validate(model, X_egitim, y_egitim, cv=cv, scoring="roc_auc")
    ortalama = skorlar["test_score"].mean()
    std = skorlar["test_score"].std()
    print(f"{isim:22s} ROC-AUC: {ortalama:.4f} (+/- {std:.4f})")

# ---------------------------------------------------------------------------
# 7) Seçilen modeli TÜM eğitim verisiyle eğit ve test kümesinde değerlendir
#    Metrik seçimi: tıbbi taramada "kötü huyluyu kaçırmak" (yanlış negatif)
#    en pahalı hata olduğundan recall (duyarlılık) özellikle önemlidir.
# ---------------------------------------------------------------------------
baslik("7) Test değerlendirmesi (hiç görülmemiş veri)")

secilen = modeller["Lojistik Regresyon"]
secilen.fit(X_egitim, y_egitim)
tahmin = secilen.predict(X_test)
olasilik = secilen.predict_proba(X_test)[:, 1]

print(f"Doğruluk (accuracy) : {accuracy_score(y_test, tahmin):.4f}")
print(f"Kesinlik (precision): {precision_score(y_test, tahmin):.4f}")
print(f"Duyarlılık (recall): {recall_score(y_test, tahmin):.4f}")
print(f"F1 skoru            : {f1_score(y_test, tahmin):.4f}")
print(f"ROC-AUC             : {roc_auc_score(y_test, olasilik):.4f}")

print("\nKarışıklık matrisi (satır: gerçek, sütun: tahmin):")
print(confusion_matrix(y_test, tahmin))

print("\nSınıf bazlı rapor:")
print(classification_report(y_test, tahmin, target_names=[sinif_adi_0, sinif_adi_1]))

# ---------------------------------------------------------------------------
# 8) Modeli diske kaydet
#    joblib ile kaydedilen pipeline; ölçekleme + modeli birlikte taşır.
# ---------------------------------------------------------------------------
baslik("8) Modeli kaydetme")

CIKTI_KLASORU.mkdir(exist_ok=True)
model_yolu = CIKTI_KLASORU / "model.joblib"
joblib.dump(secilen, model_yolu)
print(f"Model kaydedildi: {model_yolu}")

rapor_yolu = CIKTI_KLASORU / "rapor.txt"
rapor_yolu.write_text(
    f"Veri: breast_cancer | Eğitim: {X_egitim.shape[0]} | Test: {X_test.shape[0]}\n"
    f"Model: Lojistik Regresyon (StandardScaler pipeline)\n"
    f"ROC-AUC: {roc_auc_score(y_test, olasilik):.4f} | "
    f"Doğruluk: {accuracy_score(y_test, tahmin):.4f} | "
    f"Duyarlılık: {recall_score(y_test, tahmin):.4f}\n",
    encoding="utf-8",
)
print(f"Özet rapor kaydedildi: {rapor_yolu}")

# ---------------------------------------------------------------------------
# 9) Kaydedilen modelle yeni bir hastayı puanla ("üretimde kullanım" taklidi)
# ---------------------------------------------------------------------------
baslik("9) Yeni örnek tahmini (kaydedilen modelle)")

kayitli_model = joblib.load(model_yolu)
yeni_hasta = X_test.iloc[[0]]  # test kümesinden bir örnek alalım
tahmin_sinif = kayitli_model.predict(yeni_hasta)[0]
tahmin_olasilik = kayitli_model.predict_proba(yeni_hasta)[0]

etiket = sinif_adi_1 if tahmin_sinif == 1 else sinif_adi_0
gercek = sinif_adi_1 if y_test.iloc[0] == 1 else sinif_adi_0
print(f"Gerçek etiket      : {gercek}")
print(f"Modelin tahmini    : {etiket}")
print(f"Olasılıklar        : {sinif_adi_0} {tahmin_olasilik[0]:.3f} | {sinif_adi_1} {tahmin_olasilik[1]:.3f}")

print("\nBitti. cikti/ klasöründeki model.joblib dosyasını yeni verilerle kullanabilirsiniz.")
