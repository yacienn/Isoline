"""Plain-language findings.

Built ONLY from what is really known: the permissions an app declares. Isoline does not
analyze code, so nothing here claims to have observed behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Collection

from .verdict import Verdict

_P = "android.permission."
FEW_PERMISSIONS_MAX = 3


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"


@dataclass(frozen=True)
class Indicator:
    title: str
    detail: str
    severity: Severity


@dataclass(frozen=True)
class _PermissionRule:
    any_of: frozenset[str]
    severity: Severity
    title: str
    detail: str

    def matches(self, declared: Collection[str]) -> bool:
        return not self.any_of.isdisjoint(declared)

    def indicator(self) -> Indicator:
        return Indicator(self.title, self.detail, self.severity)


_RULES: tuple[_PermissionRule, ...] = (
    _PermissionRule(frozenset({_P + "SEND_SMS"}), Severity.HIGH,
                    "Can send SMS messages",
                    "Declares SEND_SMS, which SMS-fraud malware relies on. Legitimate messaging apps use it too."),
    _PermissionRule(frozenset({_P + "READ_SMS", _P + "RECEIVE_SMS"}), Severity.HIGH,
                    "Can read incoming SMS",
                    "Declares READ_SMS/RECEIVE_SMS, used by malware to intercept verification codes."),
    _PermissionRule(frozenset({_P + "SYSTEM_ALERT_WINDOW"}), Severity.HIGH,
                    "Can draw over other apps",
                    "Declares SYSTEM_ALERT_WINDOW, which overlay attacks use to cover login screens."),
    _PermissionRule(frozenset({_P + "BIND_ACCESSIBILITY_SERVICE"}), Severity.HIGH,
                    "Accessibility service",
                    "Can observe and control the screen. Powerful and often abused by banking trojans."),
    _PermissionRule(frozenset({_P + "REQUEST_INSTALL_PACKAGES", _P + "INSTALL_PACKAGES"}), Severity.HIGH,
                    "Can install other apps",
                    "Declares an install-packages permission, which droppers use to add more malware."),
    _PermissionRule(frozenset({_P + "BIND_DEVICE_ADMIN"}), Severity.HIGH,
                    "Device administrator",
                    "Device-admin rights make an app harder to uninstall."),
)


def build_indicators(declared: Collection[str], verdict: Verdict) -> tuple[Indicator, ...]:
    found = [rule.indicator() for rule in _RULES if rule.matches(declared)]
    if len(declared) <= FEW_PERMISSIONS_MAX:
        found.append(Indicator(
            "Very few permissions declared",
            "Permission-only analysis has little to work with here, so treat the score with caution.",
            Severity.MEDIUM))
    if verdict is Verdict.UNCERTAIN:
        found.append(Indicator(
            "The model is unsure",
            "The score is close to 50/50. Do not read it as either safe or malicious.",
            Severity.MEDIUM))
    return tuple(found)
