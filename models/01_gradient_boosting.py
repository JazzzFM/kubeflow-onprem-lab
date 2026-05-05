"""
Demo 1: Gradient Boosting Classifier (sklearn) — ML clasico
Dataset: Wine quality (3 clases, 178 samples, 13 features).
Mide accuracy + tiempo de training, guarda resultados.
"""
import json, time
from pathlib import Path
from sklearn.datasets import load_wine
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np

print("=" * 60)
print("DEMO 1: GRADIENT BOOSTING CLASSIFIER (CPU)")
print("=" * 60)

data = load_wine()
X, y = data.data, data.target
print(f"Dataset: Wine — {X.shape[0]} samples, {X.shape[1]} features, {len(set(y))} clases")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
print(f"Train: {len(X_train)} / Test: {len(X_test)}")

print("\nEntrenando Gradient Boosting (n_estimators=200, max_depth=3)...")
clf = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42)
t0 = time.time()
clf.fit(X_train, y_train)
train_time = time.time() - t0
print(f"  [ok] training: {train_time:.2f}s")

y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {acc:.4f}")
print("\nClassification report:")
print(classification_report(y_test, y_pred, target_names=data.target_names))
print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))

# Top features
features = sorted(zip(clf.feature_importances_, data.feature_names), reverse=True)
print("\nTop 5 features importance:")
for imp, name in features[:5]:
    print(f"  {name:30s} {imp:.4f}")

results = {
    "model": "GradientBoostingClassifier",
    "framework": "scikit-learn",
    "device": "cpu",
    "dataset": "wine",
    "n_samples": int(X.shape[0]),
    "n_features": int(X.shape[1]),
    "n_classes": int(len(set(y))),
    "n_estimators": 200,
    "max_depth": 3,
    "training_time_sec": round(train_time, 3),
    "accuracy": round(acc, 4),
    "top_features": [{"feature": name, "importance": float(imp)} for imp, name in features[:5]],
}
out = Path("/mnt/c/temp/lab-models/outputs/gbc_results.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(results, indent=2))
print(f"\nResultado guardado en: {out}")
print("\n[OK] Demo 1 completado")
