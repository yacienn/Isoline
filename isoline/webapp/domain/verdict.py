from __future__ import annotations

from enum import Enum

from isoline import policy  # shared kernel: thresholds also used by the CLI scanner


class Verdict(str, Enum):
    BENIGN = "benign"
    UNCERTAIN = "uncertain"
    MALICIOUS = "malicious"

    @classmethod
    def from_score(cls, score: float) -> "Verdict":
        """score is the model's 0-1 malicious score (share of trees voting malicious)."""
        return cls(policy.verdict_for(score))
