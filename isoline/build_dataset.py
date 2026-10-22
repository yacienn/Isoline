"""Phase 1: build dataset.csv from labeled folders.

    data/benign/*.apk   -> label 0
    data/malware/*.apk  -> label 1

Usage: python -m isoline.build_dataset [--data-dir data] [--out dataset.csv]
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from .features import InvalidAPKError, extract_permissions, permissions_to_vector
from .schema import FEATURE_PERMISSIONS


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="dataset.csv")
    args = ap.parse_args()

    rows, seen, skipped = [], {}, 0
    for label, folder in ((0, "benign"), (1, "malware")):
        for apk in sorted((Path(args.data_dir) / folder).glob("*.apk")):
            digest = sha256(apk)
            if digest in seen:  # exact duplicate files
                if seen[digest] != label:
                    print(f"CONFLICT: {apk.name} appears with both labels; dropped")
                skipped += 1
                continue
            try:
                vec = permissions_to_vector(extract_permissions(apk))
            except InvalidAPKError as e:
                print(f"SKIP {apk.name}: {e}")
                skipped += 1
                continue
            seen[digest] = label
            rows.append([digest, *vec, label])

    df = pd.DataFrame(rows, columns=["sha256", *FEATURE_PERMISSIONS, "label"])
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} samples to {args.out} "
          f"({int((df.label == 0).sum())} benign, {int((df.label == 1).sum())} malware); "
          f"skipped {skipped}")


if __name__ == "__main__":
    main()
