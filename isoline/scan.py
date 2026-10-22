"""Phase 8: scan a new APK.

Usage: python -m isoline.scan path/to/app.apk
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib

from .features import InvalidAPKError, extract_permissions, permissions_to_vector
from .policy import verdict_for

MODEL_PATH = Path("models/isoline_model.joblib")


def scan(apk_path: str, model_path: Path = MODEL_PATH) -> dict:
    bundle = joblib.load(model_path)  # only load models you trained yourself
    feature_names = bundle["feature_names"]  # the exact columns the model was trained on
    name = Path(apk_path).name
    try:
        perms = extract_permissions(apk_path)
    except InvalidAPKError as e:
        return {"file": name, "status": "error", "error": str(e)}

    vec = permissions_to_vector(perms, feature_names)
    model = bundle["model"]
    score = float(model.predict_proba([vec])[0][list(model.classes_).index(1)])
    return {
        "file": name,
        "status": "ok",
        "sha256": hashlib.sha256(Path(apk_path).read_bytes()).hexdigest(),
        "prediction": verdict_for(score),
        "malicious_score": round(score, 3),  # share of trees voting malicious; NOT a calibrated probability
        "permission_count": len(perms),
        "permissions": perms,
        "unrecognized_permissions": sorted(set(perms) - set(feature_names)),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("--model", default=str(MODEL_PATH))
    a = ap.parse_args()
    print(json.dumps(scan(a.apk, Path(a.model)), indent=2))
