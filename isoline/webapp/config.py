from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from isoline.features import MAX_APK_BYTES

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"          # localhost only by default
    port: int = 8000
    model_path: Path = PROJECT_ROOT / "models" / "isoline_model.joblib"
    static_dir: Path = PROJECT_ROOT / "web"
    project_root: Path = PROJECT_ROOT
    max_upload_bytes: int = MAX_APK_BYTES
    scan_timeout_s: int = 90
    max_concurrent_scans: int = 2
