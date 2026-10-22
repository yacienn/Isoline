"""Decision thresholds shared by the CLI scanner and the web app (single source of truth)."""
from __future__ import annotations

BENIGN_BELOW = 0.35     # score under this  -> benign
MALICIOUS_ABOVE = 0.65  # score over this   -> malicious; in between -> uncertain


def verdict_for(score: float) -> str:
    if score < BENIGN_BELOW:
        return "benign"
    if score > MALICIOUS_ABOVE:
        return "malicious"
    return "uncertain"
