"""Build a permission-only, binary-labeled CSV from the CICMalDroid 2020 CSV bundle.

    python -m tools.prepare_cicmaldroid CSV.zip --out cicmaldroid_permissions.csv

- Features: the clean `android.permission.*` columns of feature_vectors_static.csv
  (the file has ~50k messy columns; everything else is ignored).
- Labels: the static file has NO label column. They come from the 'Class' column of
  feature_vectors_syscallsbinders_frequency_5_Cat.csv (1 Adware, 2 Banking, 3 SMS,
  4 Riskware, 5 Benign), matched BY ROW ORDER (both files have 11,598 rows).
  Class 5 -> label 0 (benign); classes 1-4 -> label 1 (malware).
"""
import argparse, csv, io, re, sys, zipfile
import numpy as np, pandas as pd

csv.field_size_limit(sys.maxsize)
PAT = re.compile(r"^android\.permission\.[A-Z0-9_]+$")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path")
    ap.add_argument("--out", default="cicmaldroid_permissions.csv")
    a = ap.parse_args()

    with zipfile.ZipFile(a.zip_path) as z:
        with z.open("feature_vectors_syscallsbinders_frequency_5_Cat.csv") as f:
            cls = pd.read_csv(f, usecols=["Class"])["Class"].to_numpy()
        rows = []
        with z.open("feature_vectors_static.csv") as f:  # streamed: never fully in RAM
            r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline=""))
            header = next(r)
            idx = [i for i, h in enumerate(header) if PAT.match(h)]
            names = [header[i] for i in idx]
            for row in r:
                rows.append([0 if row[i] in ("", "0", "0.0") else 1 for i in idx])

    if len(rows) != len(cls):
        raise SystemExit(f"Row mismatch: static={len(rows)} labels={len(cls)}; cannot align safely.")
    df = pd.DataFrame(rows, columns=names, dtype=np.int8)
    df["label"] = (cls != 5).astype(np.int8)
    df.to_csv(a.out, index=False)
    print(f"Wrote {a.out}: {len(df)} rows, {len(names)} permission columns, "
          f"{int((df.label == 0).sum())} benign / {int((df.label == 1).sum())} malware")


if __name__ == "__main__":
    main()
