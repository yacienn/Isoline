"""Domain rules: pure Python, no files, no server, no model."""
import unittest

from isoline.webapp.domain.indicators import Severity
from isoline.webapp.domain.permissions import RiskLevel
from isoline.webapp.domain.report import assess
from isoline.webapp.domain.verdict import Verdict

P = "android.permission."


class VerdictTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertIs(Verdict.from_score(0.0), Verdict.BENIGN)
        self.assertIs(Verdict.from_score(0.349), Verdict.BENIGN)
        self.assertIs(Verdict.from_score(0.35), Verdict.UNCERTAIN)
        self.assertIs(Verdict.from_score(0.65), Verdict.UNCERTAIN)
        self.assertIs(Verdict.from_score(0.651), Verdict.MALICIOUS)


class AssessTests(unittest.TestCase):
    def test_sms_trojan_pattern(self):
        r = assess("ab" * 32, 0.9, [P + "INTERNET", P + "SEND_SMS", P + "READ_SMS", P + "VIBRATE"])
        self.assertIs(r.verdict, Verdict.MALICIOUS)
        self.assertEqual(r.score_percent, 90)
        self.assertEqual(r.permission_count, 4)
        titles = {i.title for i in r.indicators}
        self.assertIn("Can send SMS messages", titles)
        self.assertIn("Can read incoming SMS", titles)
        self.assertTrue(all(i.severity is Severity.HIGH for i in r.indicators))

    def test_risk_labels(self):
        r = assess("x", 0.1, [P + "SEND_SMS", P + "CAMERA", P + "INTERNET"])
        self.assertEqual([p.risk for p in r.permissions], [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW])

    def test_uncertain_and_few_permissions_warnings(self):
        r = assess("x", 0.5, [P + "INTERNET"])
        titles = [i.title for i in r.indicators]
        self.assertEqual(titles, ["Very few permissions declared", "The model is unsure"])

    def test_benign_with_many_ordinary_permissions_has_no_findings(self):
        names = [P + n for n in ("INTERNET", "VIBRATE", "WAKE_LOCK", "ACCESS_NETWORK_STATE")]
        self.assertEqual(assess("x", 0.05, names).indicators, ())


if __name__ == "__main__":
    unittest.main()
