"""Phases 3-7: load, clean, split, baseline, train, evaluate, save.

Two data sources:
  python -m isoline.train                       # dataset.csv built from your APKs
  python -m isoline.train --csv data.csv --label-col Result   # ready-made CSV (e.g. NATICUSdroid)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

SCHEMA_VERSION = 2


def metrics(y_true, y_pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def load_dataset(path: str, label_col: str, id_cols: list[str]):
    df = pd.read_csv(path)
    if label_col not in df.columns:
        raise SystemExit(f"Label column '{label_col}' not found. Columns end with: {list(df.columns[-5:])}")
    feature_names = [c for c in df.columns if c != label_col and c not in id_cols]
    df[feature_names] = df[feature_names].apply(pd.to_numeric, errors="coerce")
    before = len(df)
    df = df.dropna(subset=feature_names + [label_col])
    df[feature_names] = (df[feature_names] > 0).astype(int)  # force 0/1
    df[label_col] = df[label_col].astype(int)

    # Cleaning: identical permission vectors inflate test scores (same app pattern in train AND test).
    n_dup = int(df.duplicated(subset=feature_names + [label_col]).sum())
    df = df.drop_duplicates(subset=feature_names + [label_col])
    conflict = df.duplicated(subset=feature_names, keep=False)  # same vector, different label
    n_conf = int(conflict.sum())
    df = df[~conflict]
    print(f"Loaded {before} rows -> removed {n_dup} exact duplicates and {n_conf} contradictory rows "
          f"-> {len(df)} usable rows, {len(feature_names)} features")
    return df, feature_names


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="dataset.csv")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--id-cols", nargs="*", default=["sha256"])
    ap.add_argument("--model", choices=["tree", "forest"], default="tree")
    ap.add_argument("--max-depth", type=int, default=8)
    ap.add_argument("--min-samples-leaf", type=int, default=5)
    ap.add_argument("--out-dir", default="models")
    args = ap.parse_args()

    df, feature_names = load_dataset(args.csv, args.label_col, args.id_cols)
    X = df[feature_names].to_numpy()
    y = df[args.label_col].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    base = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    base_m = metrics(y_test, base.predict(X_test))

    if args.model == "tree":
        model = DecisionTreeClassifier(max_depth=args.max_depth,
                                       min_samples_leaf=args.min_samples_leaf,
                                       class_weight="balanced", random_state=42)
    else:
        model = RandomForestClassifier(n_estimators=200, min_samples_leaf=args.min_samples_leaf,
                                       class_weight="balanced", n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    train_m = metrics(y_train, model.predict(X_train))
    test_m = metrics(y_test, model.predict(X_test))

    print(f"Samples: {len(df)}  train={len(y_train)}  test={len(y_test)}  model={args.model}")
    for name, m in (("Baseline (test)", base_m), ("Model train", train_m), ("Model test", test_m)):
        print(f"{name:16s} acc={m['accuracy']:.3f} prec={m['precision']:.3f} "
              f"rec={m['recall']:.3f} f1={m['f1']:.3f}  {m['confusion']}")
    gap = train_m["f1"] - test_m["f1"]
    if gap > 0.1:
        print(f"WARNING: train/test F1 gap {gap:.2f} suggests overfitting; lower --max-depth.")

    print("\nTop features:")
    imp = sorted(zip(feature_names, model.feature_importances_), key=lambda t: -t[1])[:10]
    for name, v in imp:
        print(f"  {name.split('.')[-1]:28s} {v:.3f}")

    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)
    joblib.dump({"model": model, "feature_names": feature_names,
                 "schema_version": SCHEMA_VERSION}, out / "isoline_model.joblib")
    (out / "metrics.json").write_text(json.dumps(
        {"baseline_test": base_m, "train": train_m, "test": test_m}, indent=2))
    print(f"\nSaved model + metrics to {out}/")


if __name__ == "__main__":
    main()
