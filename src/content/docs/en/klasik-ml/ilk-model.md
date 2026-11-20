---
title: "Your First Model: An End-to-End scikit-learn Example"
description: "With the Iris flower dataset, we explain a complete scikit-learn workflow line by line, from loading the data to predicting a new example."
dogrulama: 2026-11-20
---

Time to set theory aside and train your first model. Our scenario: predicting a flower's species from 4 measurements (the sepals' and petals' length-width). The **Iris dataset** we'll use comes packaged inside scikit-learn — no downloading, no file hunting, no extraction. 150 examples, 3 classes, 4 features: both real and ideal-sized for learning.

:::note[Prerequisite]
Python and these two packages must be installed on your computer: `pip install scikit-learn pandas`. If you don't want to wrestle with setup, the steps on the [Local Setup](/en/donanim/yerel-kurulum/) page are written for Windows.
:::

## The single-file, end-to-end script

Save the following script as `first_model.py` and run it with `python first_model.py`. The comments explain **why** each step is done:

```python title="first_model.py"
# ---------------------------------------------------------------------------
# An end-to-end first model: Iris flower species classification (random forest)
# Before running: pip install scikit-learn pandas
# ---------------------------------------------------------------------------

# 1) Import the required libraries
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 2) Load the data -------------------------------------------------------------
#    The Iris dataset comes with scikit-learn; no need to download from the internet.
iris = load_iris()

#    X = the features (4 measurements), y = the target (0, 1, 2 → three flower species)
X, y = iris.data, iris.target

#    Let's first look by eye: convert to a table and print the first rows.
df = pd.DataFrame(X, columns=iris.feature_names)
df["species"] = y
print("The first 5 rows:")
print(df.head())

# 3) A little exploration: summary statistics and the class distribution -------
#    We see the mean, standard deviation, min/max values.
print("\nSummary statistics:")
print(df.describe().round(2))

#    How many examples of each of the three species? (We expect a balanced dataset)
print("\nThe class distribution:")
print(df["species"].value_counts().sort_index())

# 4) The train/test split ------------------------------------------------------
#    80% of the data is reserved for training, 20% for testing.
#    stratify=y    -> the class ratios are preserved in both sets
#    random_state  -> let the split be the same on every run (reproducibility)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 5) Pick the model: a random forest -------------------------------------------
#    100 decision trees are trained; the prediction is given by the trees' majority vote.
#    Why this model? It's a start that forgives settings and gives good results on
#    tabular data with little effort. It balances a single tree's memorization
#    tendency by taking the average of many trees.
model = RandomForestClassifier(n_estimators=100, random_state=42)

# 6) Training: the model learns the patterns from the examples ------------------
model.fit(X_train, y_train)

# 7) Evaluation: on the never-seen test data ------------------------------------
y_pred = model.predict(X_test)

print("\nAccuracy:", round(accuracy_score(y_test, y_pred), 2))
print("\nThe per-class report:")
print(classification_report(y_test, y_pred, target_names=iris.target_names))

# 8) The confusion matrix: which species was confused with which? ---------------
print("The confusion matrix (row = actual, column = prediction):")
print(confusion_matrix(y_test, y_pred))

# 9) Which measurement is more decisive? ----------------------------------------
#    feature_importances_ gives each feature's contribution to the decision between 0-1.
print("\nThe feature importances:")
for name, importance in zip(iris.feature_names, model.feature_importances_):
    print(f"  {name:>25}: {importance:.3f}")

# 10) Predicting with a new example ---------------------------------------------
#     An imaginary flower whose measurements we entered by hand (4 values, in the training order):
new_example = [[5.1, 3.5, 1.4, 0.2]]

prediction = model.predict(new_example)[0]            # which species? (0, 1 or 2)
probabilities = model.predict_proba(new_example)[0]   # the probability for each species

print("\nThe prediction for the new example:", iris.target_names[prediction])
print("The class probabilities:")
for species_name, p in zip(iris.target_names, probabilities):
    print(f"  {species_name}: {p:.2f}")
```

## Let's read the output

The output below is an **example** — the numbers can show small differences by version and environment; what matters is learning the shape and how to read it:

```text title="example output"
Accuracy: 0.93

The per-class report:
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       0.90      0.90      0.90        10
   virginica       0.90      0.90      0.90        10

    accuracy                           0.93        30
   macro avg       0.93      0.93      0.93        30
weighted avg       0.93      0.93      0.93        30

The confusion matrix (row = actual, column = prediction):
[[10  0  0]
 [ 0  9  1]
 [ 0  1  9]]

The feature importances:
         sepal length (cm): 0.10
          sepal width (cm): 0.02
        petal length (cm): 0.44
         petal width (cm): 0.44

The prediction for the new example: setosa
The class probabilities:
  setosa: 1.00
  versicolor: 0.00
  virginica: 0.00
```

Each section's meaning:

- **Accuracy 0.93:** 28 of the test set's 30 examples correct. Iris is a small and "easy" dataset; with these settings you'll typically see results in the 90-97% band. Don't let the high output mislead you — on real-world data the same settings usually circle the 70-90% band; that's why you should always interpret the metric **in your dataset's context**.
- **precision / recall / f1-score:** the triple scores per class ([what the metrics mean](/en/klasik-ml/temeller/)). In the example versicolor and virginica are at 90%; you can see the two being confused with each other and setosa never being confused. If one class scores 1.00 while the others are 0.9, you'd point the improvement effort at the low-scoring class.
- **support:** how many examples each class has in the test set (10+10+10=30). On imbalanced datasets, if these numbers differ a lot between classes, take care to read the `macro avg` row.
- **The confusion matrix:** the 3x3 table's rows are the real species, its columns the prediction. The cells outside the diagonal are the errors: a versicolor was once thought virginica, and a virginica once versicolor. Which species gets confused with which is the roadmap to improving the model (e.g. are these two very similar?). In Iris these two species are naturally the most confused pair.
- **The feature importances:** in the model's decision the **petal** measurements turned out most decisive (totaling ~0.88); the sepal width was of almost no use. Such insights say which measurement is worth collecting — they lower the data collection cost.
- **The new example:** the measurements 5.1 / 3.5 / 1.4 / 0.2 are a typical setosa profile; the model said "setosa" and gave it a probability of 1.00. While `predict` makes the decision, `predict_proba` shows **how certain** the decision is: if you see a 0.55-0.45 distribution, the model was hesitating on that example.

:::tip
To lower or raise the value, change the `random_state`, `test_size` and `n_estimators` values and run again. For loss and the other evaluation concepts: [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).
:::

## The alternative: the model doing the same job in 5 lines

Instead of the random forest, will you also try logistic regression? Thanks to scikit-learn's "same API" advantage, the only thing changing is the model line:

```python title="logistic_regression.py"
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)

model = LogisticRegression(max_iter=200)   # max_iter: to avoid the warning
model.fit(X_train, y_train)
print("Accuracy:", round(accuracy_score(y_test, model.predict(X_test)), 2))
```

On Iris both models give results in a similar band. In real jobs, the choice depends on these questions: are you after the best score (usually forest/gradient boosting), or 10x faster training and explainable coefficients (logistic regression)?

## Common mistakes

:::caution
- **`fit`ting on the test data:** all `fit` calls are made with the training data. Every line touching the test set inflates your report card and hides the real performance — this is called data leakage.
- **Forgetting scaling:** it wasn't needed in this example because all measurements are in centimeters; but when age (0-100) and income (0-1,000,000) sit side by side, KNN, SVM and linear models break. Use `StandardScaler` in such cases (tree-based models are generally unaffected by scale).
- **Ignoring the validation set and spending the test set:** if you keep looking at the test set while tuning, it too becomes learned data. Reserve a validation set for the trials, and save the test for last.
- **Speaking definitively with little data:** a single error on 30 test examples makes ~3% of wobble. Differences on small test sets may not be "improvement" but luck.
- **Not setting `random_state`:** if the same script gives a different result on every run, debugging becomes impossible. And distinguish what you pinned: judging by results measured on the same data, keeping the split fixed and changing only the model seed wobbles accuracy very little, while changing the split itself wobbles it markedly more — the details are on the [Reproducibility](/en/kullanim/tekrarlanabilirlik/) page.
:::

## The next steps

The next three directions:

1. **Gradient boosting:** in the same Iris script, try the XGBoost or LightGBM models (e.g. `LGBMClassifier`) instead of `RandomForestClassifier`; they usually score a notch better. The concept tour: [Classic ML Fundamentals](/en/klasik-ml/temeller/).
2. **Trying with your own table:** load an Excel/CSV file in your hands with `pd.read_csv` and apply the same flow. For jobs like converting text columns to numbers, see the [Data Cleaning](/en/veri/veri-temizleme/) page.
3. **Moving to deep learning:** when the data turns into text, the flow changes, the concepts don't. For the benchmark world: [Benchmarks](/en/degerlendirme/benchmarklar/).

You've now seen how a model is trained start to finish — the data was split, the model learned, it was evaluated on never-seen data, and a new prediction was produced. In LLMs too the flow is the same: **data → training → evaluation.** Only the scale, the data type and the tools grow.

Continue: [Step-by-Step Training in LLMs](/en/llm/adim-adim-egitim/)
