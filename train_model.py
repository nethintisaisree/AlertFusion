# train_model.py

"""
MODEL TRAINING SCRIPT
Intelligent Emergency Alert System
------------------------------------

Trains a TF-IDF + Logistic Regression classifier
on the emergency dataset.

Improvements:
  - Uses both 'message' AND 'emergency_type' as features
  - Train/test split for honest accuracy evaluation
  - Class weight balancing for imbalanced dataset
  - Full classification report printed after training
  - Absolute paths — works from any directory
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline, FeatureUnion
import joblib

# ======================================================
# PATHS — resolved from project root
# ======================================================

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH    = os.path.join(BASE_DIR, "dataset", "emergency_dataset.csv")
MODEL_PATH      = os.path.join(BASE_DIR, "model", "emergency_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "model", "vectorizer.pkl")

# ======================================================
# LOAD DATASET
# ======================================================

print("Loading dataset...")
data = pd.read_csv(DATASET_PATH)

print(f"Total samples: {len(data)}")
print(f"\nClass distribution:\n{data['decision'].value_counts()}\n")

# ======================================================
# FEATURE ENGINEERING
# Combine message + emergency_type into single text input
# e.g. "house is on fire [fire]" — type adds context
# ======================================================

data["combined"] = (
    data["message"].str.lower().str.strip() +
    " [" +
    data["emergency_type"].str.lower().str.strip() +
    "]"
)

X = data["combined"]
y = data["decision"]

# ======================================================
# TRAIN / TEST SPLIT
# 80% train, 20% test — stratified to preserve class ratios
# ======================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Training samples : {len(X_train)}")
print(f"Testing samples  : {len(X_test)}\n")

# ======================================================
# VECTORIZER
# TF-IDF with unigrams and bigrams
# ======================================================

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    max_features=5000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)

# ======================================================
# MODEL TRAINING
# class_weight='balanced' compensates for imbalanced classes
# e.g. LOG_AND_MONITOR (11 samples) vs IMMEDIATE (50 samples)
# ======================================================

print("Training model...")

model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    random_state=42,
    solver="lbfgs"
)

model.fit(X_train_vec, y_train)

# ======================================================
# EVALUATION
# ======================================================

y_pred = model.predict(X_test_vec)

accuracy = accuracy_score(y_test, y_pred)

print(f"\n{'='*50}")
print(f"MODEL ACCURACY: {accuracy:.2%}")
print(f"{'='*50}\n")

print("CLASSIFICATION REPORT:")
print(classification_report(y_test, y_pred, zero_division=0))

# ======================================================
# SAVE MODEL + VECTORIZER
# ======================================================

os.makedirs(os.path.join(BASE_DIR, "model"), exist_ok=True)

joblib.dump(model,      MODEL_PATH)
joblib.dump(vectorizer, VECTORIZER_PATH)

print(f"\nModel saved     : {MODEL_PATH}")
print(f"Vectorizer saved: {VECTORIZER_PATH}")
print("\nTraining complete. Run your Flask app now.")