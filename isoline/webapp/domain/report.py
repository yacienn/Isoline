from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .indicators import Indicator, build_indicators
from .permissions import Permission
from .verdict import Verdict


@dataclass(frozen=True)
class ScanReport:
    """The outcome of analysing one APK."""
    sha256: str
    malicious_score: float          # 0-1, share of trees voting malicious; NOT a calibrated probability
    verdict: Verdict
    permissions: tuple[Permission, ...]
    indicators: tuple[Indicator, ...]

    @property
    def score_percent(self) -> int:
        return round(self.malicious_score * 100)

    @property
    def permission_count(self) -> int:
        return len(self.permissions)


def assess(sha256: str, malicious_score: float, permission_names: Iterable[str]) -> ScanReport:
    """Turn the raw model output into a verdict with findings (the core business rule)."""
    names = tuple(permission_names)
    verdict = Verdict.from_score(malicious_score)
    return ScanReport(
        sha256=sha256,
        malicious_score=malicious_score,
        verdict=verdict,
        permissions=tuple(Permission.declared(n) for n in names),
        indicators=build_indicators(names, verdict),
    )
