from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from isoline.schema import risk_of  # rule-of-thumb labels, NOT model output


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Permission:
    name: str
    risk: RiskLevel

    @classmethod
    def declared(cls, name: str) -> "Permission":
        return cls(name=name, risk=RiskLevel(risk_of(name)))
