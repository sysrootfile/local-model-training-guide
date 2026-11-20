---
title: "Classic Machine Learning: Fundamentals"
description: "A classic machine learning introduction gathering supervised and unsupervised learning, the train-test split, basic metrics and model families on one page."
dogrulama: 2026-11-20
---

Most of this guide is about LLMs and image models; but machine learning isn't only those. If you have tabular data (row-column data resembling Excel) and a prediction target — will the customer leave, what's the price, is this product faulty — **classic machine learning** often trains faster, asks for less hardware, is easier to explain, and frequently gives more accurate results.

There's also a pedagogical reason: training, testing, overfitting, metrics… All these concepts are learned most clearly here. On a small dataset like Iris the model trains in seconds; i.e. there's no need to "wait days on a GPU to learn the concept". Everything you learn here will meet you verbatim in LLM training.

## The types of learning

| Type | What does it do? | An everyday example | Typical algorithms |
|---|---|---|---|
| **Supervised — classification** | Learns to predict a category from labeled data | Whether an email is spam | Logistic regression, Random Forest, XGBoost |
| **Supervised — regression** | Learns to predict a number from labeled data | House price, temperature, sales count | Linear regression, gradient boosting |
| **Unsupervised** | Finds hidden structure/clusters in unlabeled data | Separating customers into similar behavior groups | K-means, hierarchical clustering |
| **Reinforcement** | Learns a strategy by trial and error with a reward signal | A game-playing bot, robot walking | Q-learning, policy gradients |

On this page we'll mostly deal with **supervised learning**; because most of the business world's tabular data problems fall there. LLM fine-tuning is also actually supervised learning: the input text is the feature, the expected answer the label.

## The basic workflow

Every classic ML project — some skip certain steps — follows this line:

```text
data collection → cleaning → feature engineering → the train/test split
       → model choice → training → evaluation → prediction on new data
```

Accept two points up front:

1. **Most of the job passes in the data.** In real projects 70-80% of the time goes to data collection, cleaning and feature preparation. The model line is relatively short. That's why this guide's [Data Types](/en/veri/veri-turleri/) and [Data Cleaning](/en/veri/veri-temizleme/) pages should be read independently of the model pages.
2. **Evaluation is planned before training.** The question "by what will I measure success?" should be clarified at the very start. Otherwise, when the result lands in your hands, you'll start arguing over the metrics.

:::tip[While looking for data]
In classic ML the data is often already in your hands: in-house tables, Excel files, open data portals. To see what's possible, [Where to Find Data?](/en/veri/veri-nereden-bulunur/); for the format to store your prepared table in, the [Data Formats](/en/veri/veri-formatlari/) pages.
:::

### Feature engineering: producing information from data

The model learns not the raw columns but the representations you present. Feature engineering is producing new columns useful to the model from the raw data:

- From a date column, extracting "day of week", "month", "is holiday?" columns.
- From a free-text address column, separating "city" and "postal code".
- Computing derived values like unit price from total price, debt/income ratio from income.
- Introducing categorical columns (color: red/blue/green) to the model as numbers; the most common being "one-hot encoding", which produces a 0/1 column per category.

A different engineering applied to the same column can get you very different results from the same model. In classic ML, "improve the features before changing the model" almost always pays. Its counterpart on the LLM side is data quality and labeling: the same logic, different materials.

### Cross-validation and the baseline model

A single train/test split is open to chance: when the split changes, the score can jump. **Cross-validation** splits the data into k pieces and uses each piece in turn as validation, reporting the mean of the k scores (k=5 is typical). Both the measurement becomes more reliable and every example is seen in an "exam" more than once. One line in scikit-learn: `cross_val_score(model, X, y, cv=5)`.

Also, in every project set up a simple **baseline**: even a dummy model saying "tell everyone the most common class" provides a comparison floor. For example, if 60% of customers leave, the "everyone leaves" model's accuracy is 60%; if your real model can't meaningfully beat that, you need to return to the data and features before growing the architecture.

## Why is the train/test split sacred?

The model being good on the data it was trained on proves nothing: like a student who saw the exam questions beforehand scoring high on those questions. The real exam is **data never seen**. That's why the data is split into two (even three) before training even starts:

| Set | What's it for? | Typical ratio |
|---|---|---|
| Training (train) | The model learns from here | 70-80% |
| Validation | Setting trials, model choice | 10-15% |
| Test | Untouchable; the final report card is measured here | 10-20% |

**Overfitting** is the model "memorizing" the data instead of "generalizing" it: flawless on the training data, bad on new data. The symptoms: the training score near perfect while the test score is clearly lower; fitting even the noise in the training data. The ways out: more data, a simpler model, regularization and early stopping (cutting training when the validation score stops improving).

On the LLM side you'll see the same of these concepts with loss curves: if the validation loss starts rising while the training loss drops, overfit has begun. Details: [How Does Training Work?](/en/temeller/egitim-nasil-calisir/) and [Loss and Metrics](/en/degerlendirme/loss-ve-metrikler/).

## The basic metrics (and their traps)

| Metric | What does it measure? | Where is it critical? | Its trap |
|---|---|---|---|
| **Accuracy** | The rate of correct predictions | If the classes are balanced | **Misleads on imbalanced data:** if 95% of the data is "negative", a model always saying "negative" gets 95% accuracy — but is of no use at all. |
| **Precision** | How many of those we called "positive" really are? | Where false alarms are expensive (a spam filter: counting a legitimate email as spam is a heavy price) | A timid model inflates precision but misses most of the positives; don't read it alone. |
| **Recall** | How many of the real positives were caught? | Where missing is expensive (disease screening: telling a sick person "healthy" is unacceptable) | A model saying "positive" to everything makes recall 100%; evaluate it together with precision. |
| **F1** | The harmonic mean of precision and recall | Cases where both errors matter | It doesn't show which component dragged it down; watch the two metrics separately too. |
| **MSE / MAE** | The magnitude of the prediction error in regression | Number predictions like price, duration, temperature | MSE is overly sensitive to outliers; MAE is more robust but non-differentiable, so it isn't preferred in optimization. |

Precision and recall's formulas come from the confusion matrix's definition — the 2x2 table showing what the model confuses with what:

| | Prediction: positive | Prediction: negative |
|---|---|---|
| **Actually: positive** | True positive (TP) | False negative (FN) |
| **Actually: negative** | False positive (FP) | True negative (TN) |

From here: `precision = TP / (TP + FP)`, `recall = TP / (TP + FN)`. So precision is the question "how solid are those I called positive", recall "how many of the positives did I find". Never read either alone; which is critical depends on the **application**: in a spam filter precision, in disease screening recall comes to the fore.

## The model families: a quick tour

- **Linear models** (linear/logistic regression): they predict with a weighted sum of the input features. Fast, work with little data and, thanks to their coefficients, are interpretable; the clearest answer to "which feature affects how much?" is here. If the relation is close to linear, a surprisingly good first model.
- **Decision trees and random forest:** a decision tree is an if-else chain like "if age > 30 and income < X then…"; alone it's prone to memorization (overfit). A random forest trains hundreds of different trees and decides by majority vote — this "wisdom of the crowd" seriously balances memorization. With its low tuning need, it's tabular data's reliable workhorse.
- **Gradient boosting (XGBoost / LightGBM):** it trains trees in sequence; each new tree focuses on correcting the previous ones' errors. It's been the most frequent winning family in tabular data competitions for years; it needs tuning but its ceiling accuracy is high. If you have numeric tabular data, definitely try it.
- **KNN (k-nearest neighbors):** for prediction it looks at the k most similar examples and follows the majority. Conceptually the most intuitive method; scaling is mandatory and prediction slows on big data. A good reference on small datasets.
- **SVM (support vector machines):** it finds the widest "margin" separating the classes; a classic tool on medium-sized, high-dimensional data. Kernel tricks are powerful but training gets heavy on big data.
- **K-means:** it splits unlabeled data into k clusters. It's the standard tool of "discovery" problems like customer segmentation; you say how many clusters there are (k), which is both power and toil.

To decide quickly:

| Situation | The first to try | The next step |
|---|---|---|
| Small data, quick results wanted | Logistic regression | Random forest |
| Tabular data, a best-score goal | Random forest | XGBoost / LightGBM |
| Explainability required ("why this decision?") | Logistic regression, a decision tree | Coefficient and branch analysis |
| Unlabeled data, discovering groups | K-means | Hierarchical clustering |

## Two classic traps: scaling and leakage

- **Scaling:** if age (0-100) and income (0-1,000,000) are in the same table, distance and dot-product-based models (KNN, SVM, linear models) give the second column more weight than it deserves. The fix is transforming every column with tools like `StandardScaler` so the mean is 0 and the standard deviation 1. A fine detail: the scaler should be `fit` only on the **training data**, with `transform` alone applied to the test data; tree-based models are generally unaffected by scaling.
- **Data leakage:** if the test set's information mixes into training, the scores look higher than they are. The most common example is scaling leakage; another is using columns formed when the target formed as features (e.g. trying to predict the "did they leave?" target with a "departure date" column). The rule is clear: no information you **won't have** at prediction time can be a feature.

## scikit-learn: the standard toolbox

When classic ML is said in Python, the framework that comes to mind is [scikit-learn](https://scikit-learn.org). Why the standard?

- The same API in every model: fit, predict, score.
- Data preprocessing, splitting, scaling, metrics, cross-validation — all in the same package.
- Over a hundred algorithms; to switch, changing the model's name suffices.

The whole library's essence is these three lines:

```python title="the scikit-learn API pattern"
model.fit(X_train, y_train)        # learn
prediction = model.predict(X_test)     # predict
score = model.score(X_test, y_test) # evaluate
```

Every classification/regression model fits this pattern; their differences are only the constructor parameters (`RandomForestClassifier(n_estimators=100)` etc.). This pattern is the same philosophy as the `trainer.train()` / `model.generate()` flow on the Hugging Face side: the library hides the detail, you focus on the flow.

:::tip
If you'll apply this pattern for the first time, move to an end-to-end example with ready data: [Your First Model: An End-to-End scikit-learn Example](/en/klasik-ml/ilk-model/) — you'll run the whole workflow in a 40-line script.
:::

## The decision: when classic ML, when LLM/deep learning?

| Situation | The right tool |
|---|---|
| Prediction on tabular/numeric data (price, class, score) | **Classic ML** — especially XGBoost/random forest |
| Little data + tabular (hundreds of rows) | **Classic ML** — deep learning memorizes at this scale |
| Text, image, audio, chat generation | **Deep learning / LLM** ([Step-by-Step Training](/en/llm/adim-adim-egitim/)) |
| The "why this decision?" explanation is a must | **Classic ML** (linear models, trees) |
| Extracting features from text and combining with a table | **Hybrid:** the LLM extracts, classic ML decides |

The practical rule: if you have columns and rows in hand, try classic ML first. If text/image is in the job or you want generation, move to the deep learning side. Most real systems mix the two.

## What's next?

Your concept map is now ready: the learning types, the workflow, the train/test split, the metrics and the model families. Next is running all of these with real code.

Continue: [Your First Model: An End-to-End scikit-learn Example](/en/klasik-ml/ilk-model/)
