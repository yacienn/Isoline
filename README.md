# Isoline

**Static Android malware detection from declared permissions.**
Upload an APK, and Isoline reads its `AndroidManifest.xml` permissions, turns them into a binary
feature vector, and asks a trained machine-learning model whether the app looks benign, malicious,
or uncertain. The APK is never executed.

> Isoline is a learning/research project. It is **not** a replacement for an antivirus.
> Permission-only detection has real limits (see [Limitations](#limitations)).

---

## Contents
1. [How it works](#how-it-works)
2. [Project structure](#project-structure)
3. [Quick start](#quick-start)
4. [Datasets](#datasets)
5. [Training options](#training-options)
6. [Command-line scanner](#command-line-scanner)
7. [Web interface](#web-interface)
8. [Web architecture](#web-architecture)
9. [Understanding the results](#understanding-the-results)
10. [Security notes](#security-notes)
11. [Limitations](#limitations)
12. [Roadmap](#roadmap)
13. [Testing](#testing)
14. [Troubleshooting](#troubleshooting)
15. [Credits and citations](#credits-and-citations)

---

## How it works

```
 APK file ──► validate ──► extract permissions ──► binary vector ──► model ──► score ──► verdict
 (untrusted)  (ZIP, size,  (Androguard,            (same column     (Random   0–1       benign /
               manifest)    no execution)           order as          Forest or          uncertain /
                                                    training)         Decision Tree)     malicious
```

1. **Validate** – the file must be a ZIP under 150 MB containing `AndroidManifest.xml`.
2. **Extract** – Androguard reads the permissions the app declares.
3. **Vectorize** – each permission becomes a 0/1 feature. The column order is stored *inside* the
   saved model, so training and scanning can never disagree.
4. **Predict** – the model returns a score: the share of trees that vote "malicious".
5. **Decide** – score `< 0.35` → benign, `> 0.65` → malicious, otherwise **uncertain**.

## Project structure

```
Isoline/
├── isoline/
│   ├── schema.py          # built-in permission list + rule-of-thumb risk labels (for the UI)
│   ├── features.py        # APK validation, permission extraction, vectorization
│   ├── build_dataset.py   # build dataset.csv from folders of labeled APKs
│   ├── train.py           # load/clean CSV, split, baseline, train, evaluate, save model
│   ├── scan.py            # scan one APK from the command line (JSON output)
│   ├── policy.py          # benign/uncertain/malicious thresholds (shared by CLI and web)
│   ├── server.py          # `python -m isoline.server` entry point (delegates to webapp/)
│   └── webapp/            # the website back end, in clean-architecture layers (see below)
│       ├── domain/        #   verdicts, permission risk, findings, ScanReport (pure rules)
│       ├── application/   #   ScanApk use case, ports (interfaces), errors
│       ├── infrastructure/#   subprocess scanner, temp-file upload storage
│       ├── interface/     #   HTTP controller, presenters, static files, http.server adapter
│       ├── config.py      #   Settings (host, port, limits, paths)
│       └── container.py   #   composition root: wires the layers together
├── web/                   # the website front end, also layered (see below)
│   ├── index.html         #   markup only
│   ├── css/styles.css
│   └── js/                #   domain/, application/, infrastructure/, ui/, main.js
├── tools/
│   ├── prepare_cicmaldroid.py     # CICMalDroid CSV bundle -> clean permission CSV
│   └── make_synthetic_dataset.py  # FAKE data, only to smoke-test the pipeline
├── tests/                 # unit tests (Python + front end); test_architecture.py guards the layers
├── data/benign/, data/malware/    # put labeled APKs here (git-ignored)
├── models/                # trained model + metrics.json (git-ignored)
├── feature_extractor.py   # early exploration: permissions + DEX method counts for one APK
├── main.py                # runs feature_extractor.py on crackMe.apk -> features.json
└── requirements.txt
```

## Quick start

Requires **Python 3.10+** (tested on 3.12).

```powershell
# 1. install libraries (once)
pip install -r requirements.txt

# 2. get a dataset CSV into this folder (see "Datasets"), then train (once)
python -m isoline.train --csv cicmaldroid_permissions.csv --label-col label --model forest

# 3. start the website
python -m isoline.server
```

Open **http://127.0.0.1:8000** and drop in an `.apk`. Stop the server with `Ctrl+C`.
After the first training you only need step 3 next time.

On macOS/Linux use `python3` and activate a virtual environment first
(`python3 -m venv .venv && source .venv/bin/activate`).

## Datasets

Isoline can learn from either ready-made permission CSVs or from APKs you collect.

| Source | What you get | Access |
|---|---|---|
| **CICMalDroid 2020** (UNB/CIC) | ~17k APKs + CSVs, 5 classes (adware, banking, SMS, riskware, benign) | Public download; cite the paper |
| **NATICUSdroid** (UCI repository, id 722) | One 4.9 MB CSV, 86 permission columns, ~29k apps, benign/malware | Free download |
| **AndroZoo** | ~27M APKs with antivirus detection counts | Free, but request access from an institutional email |
| **MalwareBazaar** | Recent malware samples | Free account and API key |
| **F-Droid** | Benign open-source APKs | Free, no sign-up |

### A. CICMalDroid 2020 CSV bundle (`CSV.zip`)
```powershell
python -m tools.prepare_cicmaldroid CSV.zip --out cicmaldroid_permissions.csv
```
- Features: the 266 clean `android.permission.*` columns from `feature_vectors_static.csv`
  (the raw file has ~50k messy columns).
- Labels: the static file has **no label column**. Labels come from the `Class` column of
  `feature_vectors_syscallsbinders_frequency_5_Cat.csv`, matched **by row order** (both files have
  11,598 rows). Class 5 (Benign) → `0`; classes 1–4 → `1`.
- The row-order match is an assumption, but it checks out: ~99.5% of SMS-malware rows declare
  `SEND_SMS` versus ~7% of benign rows. Verify this yourself if you change the data.

### B. NATICUSdroid (or any permission CSV)
```powershell
python -m isoline.train --csv data.csv --label-col Result --model forest
```
Any CSV works if it has one 0/1 column per permission plus a 0/1 label column. All other columns are
used as features automatically.

### C. Your own APKs
Put APKs in `data/benign/` and `data/malware/`, then:
```powershell
python -m isoline.build_dataset      # writes dataset.csv, removes duplicate files by SHA-256
python -m isoline.train              # trains on dataset.csv
```

**Handle malware only inside an isolated virtual machine, and never install samples on a real phone.**

## Training options

```powershell
python -m isoline.train --csv FILE --label-col NAME [options]
```

| Option | Default | Meaning |
|---|---|---|
| `--csv` | `dataset.csv` | Input CSV |
| `--label-col` | `label` | Name of the 0/1 label column |
| `--id-cols` | `sha256` | Columns to ignore (not features) |
| `--model` | `tree` | `tree` (Decision Tree) or `forest` (Random Forest, 200 trees) |
| `--max-depth` | `8` | Tree depth limit (tree only); lower = less overfitting |
| `--min-samples-leaf` | `5` | Minimum samples per leaf |
| `--out-dir` | `models` | Where to save the model |

What training does:
1. **Cleans** the data: drops exact duplicate rows and contradictory rows (same permissions, different
   label). Duplicates matter a lot — in CICMalDroid about 8,850 of 11,598 rows are repeats, and leaving them in
   would put the same pattern in both the training and test sets and inflate scores.
2. **Splits** 80/20, stratified, `random_state=42`.
3. **Baseline** – a "always guess the majority class" model, so you can see if the real model is worth anything.
4. **Trains** with `class_weight="balanced"`.
5. **Reports** accuracy, precision, recall, F1, confusion matrix, top features, and warns if train/test F1 differ by more than 0.1.
6. **Saves** `models/isoline_model.joblib` (model + exact feature names) and `models/metrics.json`.

### Reference results (CICMalDroid 2020, duplicates removed, 538 test apps)

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Decision Tree | ~87% | ~87% | ~88% | ~88% |
| Random Forest | ~88% | ~88% | ~89–90% | ~89% |

Your numbers will differ by a point or so between runs and machines. These are lower than many published
figures (~97%) because adware/riskware look like normal apps and because duplicates are removed.

## Command-line scanner

```powershell
python -m isoline.scan some_app.apk
```
Example output:
```json
{
  "file": "some_app.apk",
  "status": "ok",
  "sha256": "…",
  "prediction": "uncertain",
  "malicious_score": 0.576,
  "permission_count": 17,
  "permissions": ["android.permission.INTERNET", "…"],
  "unrecognized_permissions": ["com.android.launcher.permission.READ_SETTINGS"]
}
```
`unrecognized_permissions` are permissions the app declares that the model has no column for; they are
ignored by the model.

## Web interface

```powershell
python -m isoline.server [--host 127.0.0.1] [--port 8000]
```

- `GET /` – the upload page; `/css/*` and `/js/*` – its static files (known file types only).
- `POST /api/scan` – body is the raw APK bytes (`Content-Type: application/octet-stream`).
  Returns JSON: `score` (0–100), `verdict` (`benign` / `uncertain` / `malicious`), `sha256`,
  `permission_count`, `permissions[]` (each with a `high`/`medium`/`low` label), and `indicators[]`
  (plain-language findings). The browser displays the server's `verdict`; it never recomputes it.

Error responses: `403` cross-origin request, `411` missing length, `413` empty or over 150 MB,
`400` upload cut short, `422` not a valid APK or timed out, `500` scanner crashed, `503` no trained model yet.

## Web architecture

The website follows a clean architecture: **business rules know nothing about HTTP, files or
processes; those details plug in from the outside.** Dependencies only point inwards.

```
 browser ──► interface (HTTP) ──► application (use case) ──► domain (rules)
                 │                        │
                 └──── infrastructure ────┘   implements the application's ports
                       (subprocess scanner, temp files)
                 container.py wires everything (the only file that sees all layers)
```

| Layer | Folder | Contains | May import |
|---|---|---|---|
| Domain | `isoline/webapp/domain/` | `Verdict`, `RiskLevel`, `Permission`, indicator rules, `ScanReport`, `assess()` | nothing outside the standard library, `isoline.policy`, `isoline.schema` |
| Application | `isoline/webapp/application/` | `ScanApk` use case, ports `ApkScanner` / `UploadStorage`, `ScanError` family | domain |
| Infrastructure | `isoline/webapp/infrastructure/` | `SubprocessApkScanner` (isolated process, 90 s timeout, 2 at a time), `TempUploadStorage` | application, domain |
| Interface | `isoline/webapp/interface/` | `ScanController`, presenters (JSON + error → status), `StaticFiles`, `WebApp` router, `http.server` adapter | application, domain |

Front end (`web/js/`), same idea:

| Layer | Folder | Role |
|---|---|---|
| Domain | `domain/` | APK file rule (extension, 150 MB), how each verdict is explained, permission risk order/filter |
| Application | `application/` | `analyzeApk` use case; talks to a `scanner` port |
| Infrastructure | `infrastructure/` | `scanApiGateway`: the only code that calls `fetch('/api/scan')` |
| UI | `ui/` | drop zone, progress panel, result view, background animation |
| Entry | `main.js` | wires the above together |

**Why it pays off**
- Swap the scanner (e.g. a container, a remote API, a different model) by writing one new adapter; the
  use case, rules and UI do not change.
- Every rule is testable without a server, a model, or Androguard (see `tests/test_webapp_*.py`).
- `tests/test_architecture.py` fails if a layer imports something it should not.

**Adding a feature** – e.g. a scan history: add a `ScanHistory` port in `application/`, a SQLite adapter in
`infrastructure/`, call it from `ScanApk`, expose it with a new controller, and wire it in `container.py`.

## Understanding the results

| Verdict | Score | Meaning |
|---|---|---|
| Benign | < 35 | The permission pattern resembles normal apps in the training data. Not a guarantee. |
| Uncertain | 35–65 | The model cannot decide. **This is not a "safe" result.** |
| Malicious | > 65 | The pattern matches malware in the training data. |

- The score is the **fraction of trees voting "malicious"**. It is *not* a calibrated probability.
- The **findings** list is built only from declared permissions (e.g. "Declares SEND_SMS"). It does not claim to
  have seen behaviour such as dynamic code loading, because Isoline does not analyze code yet.
- The **high / medium / low** permission labels are rules of thumb defined in `isoline/schema.py`, not model output.

## Security notes

APK files are untrusted input.
- The APK is **never executed** — static analysis only.
- Parsing runs in a **separate process** with a 90-second timeout; at most 2 scans run at once.
- Uploads are streamed to a temporary file (limit 150 MB) and deleted afterwards.
- The server listens on **localhost only** by default and rejects cross-origin POSTs. If you bind it to another
  interface, put it behind authentication and stronger isolation (container/VM, memory limits).
- `models/*.joblib` files are Python pickles: **only load models you trained yourself.**
- Every response carries `Content-Security-Policy`, `X-Frame-Options: DENY`, `nosniff` and `no-referrer`
  headers; static files are served only from `web/`, only for known file types, never dotfiles.
- Never commit APKs, malware samples, or generated models (`.gitignore` already excludes them).

## Limitations

- **Permissions are a weak signal.** Many malware families request few or ordinary permissions, and many
  legitimate apps request many. Expect false positives and false negatives.
- **Old data.** CICMalDroid and NATICUSdroid cover roughly 2010–2019. Modern Android apps use different permissions,
  so benign modern apps may score as uncertain. The most important features in a trained model (such as
  `USE_CREDENTIALS`, `MANAGE_ACCOUNTS`) are era-specific.
- **Label quality.** Adware and riskware are gray areas; here they are all counted as malware.
- **Static only.** Obfuscation, packed code, and runtime-loaded payloads are invisible to this approach.
- **Dataset assumption.** The CICMalDroid labels are aligned by row order (see above).
- Scores are for the data and thresholds used here; they will not transfer to every app store.

## Roadmap

Done: dataset preparation, permission vectorization, train/test split, baseline, Decision Tree and Random Forest,
evaluation, model saving, CLI scanner, web interface with uncertain verdict.

Next ideas:
- Add more benign, modern apps (e.g. F-Droid, own phone) and NATICUSdroid to reduce era bias.
- Tune thresholds and tree depth; evaluate on a separate, previously unseen dataset; group related app versions
  so they never straddle the train/test split.
- Add richer static features from DEX (suspicious API calls, intents, services) — `feature_extractor.py` already
  extracts method identifiers.
- Stronger isolation for the scanner (container, resource limits) and a scan history database.
- Optional client/back-end split (Flutter app + Node API calling the Python scanner).
- Dynamic analysis in a controlled sandbox.

## Testing

```powershell
pip install pytest
python -m pytest -q                       # all Python tests (the web tests are plain unittest, so they also run without pytest)
node --test "tests/js/*.test.mjs"         # front-end unit tests (Node 20+, no packages needed)
```
`tools/make_synthetic_dataset.py` creates a **fake** dataset to check that the training pipeline runs.
Results on it mean nothing about real malware.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not recognized | Try `py` (Windows) or `python3` |
| `FileNotFoundError: cicmaldroid_permissions.csv` | The CSV must be in the folder you run the command from |
| `No trained model found` on the web page | Run the training command first |
| `androguard` fails to install | Use Python 3.12 or 3.13 instead of a pre-release Python |
| "Not a valid APK" | The file is not a real APK (must be a ZIP containing `AndroidManifest.xml`) |
| Scanner is slow on a big APK | Parsing is capped at 90 seconds; very large or malformed files may time out |
| OneDrive shows the file but Python can't read it | Right-click it → "Always keep on this device" |

## Credits and citations

- **Androguard** for APK parsing.
- **scikit-learn**, **pandas**, **joblib** for the machine-learning pipeline.
- **CICMalDroid 2020** — if you use it, cite: S. Mahdavifar, A. F. A. Kadir, R. Fatemi, D. Alhadidi, A. A. Ghorbani,
  *Dynamic Android Malware Category Classification using Semi-Supervised Deep Learning*, IEEE DASC 2020; and
  S. Mahdavifar, D. Alhadidi, A. A. Ghorbani, *Effective and Efficient Hybrid Android Malware Classification Using
  Pseudo-Label Stacked Auto-Encoder*, Journal of Network and Systems Management 30(1), 2022.
- **NATICUSdroid** — A. Mathur, UCI Machine Learning Repository, https://doi.org/10.24432/C5FS64.
- **AndroZoo** — K. Allix, T. F. Bissyandé, J. Klein, Y. Le Traon, *AndroZoo: Collecting Millions of Android Apps
  for the Research Community*, MSR 2016.
