"""Use case tested with fakes: no subprocess, no temp files, no model."""
import io
import unittest
from contextlib import contextmanager
from pathlib import Path

from isoline.webapp.application.errors import InvalidApk, UploadRejected
from isoline.webapp.application.ports import RawScan
from isoline.webapp.application.scan_apk import ScanApk
from isoline.webapp.domain.verdict import Verdict
from isoline.webapp.infrastructure.temp_upload_storage import TempUploadStorage
from isoline.webapp.application.errors import UploadIncomplete


class FakeStorage:
    def __init__(self):
        self.entered = self.exited = 0

    @contextmanager
    def store(self, stream, length):
        self.entered += 1
        try:
            yield Path("/fake/app.apk")
        finally:
            self.exited += 1


class FakeScanner:
    def __init__(self, raw=None, error=None):
        self.raw, self.error, self.seen = raw, error, None

    def scan(self, apk_path):
        self.seen = apk_path
        if self.error:
            raise self.error
        return self.raw


RAW = RawScan("f" * 64, 0.8, ("android.permission.SEND_SMS", "android.permission.INTERNET"))


class ScanApkTests(unittest.TestCase):
    def test_returns_assessed_report_and_cleans_up(self):
        storage, scanner = FakeStorage(), FakeScanner(RAW)
        report = ScanApk(storage, scanner, 1000).execute(io.BytesIO(b"x" * 10), 10)
        self.assertIs(report.verdict, Verdict.MALICIOUS)
        self.assertEqual(scanner.seen, Path("/fake/app.apk"))
        self.assertEqual((storage.entered, storage.exited), (1, 1))

    def test_rejects_empty_and_oversized_before_touching_storage(self):
        storage = FakeStorage()
        uc = ScanApk(storage, FakeScanner(RAW), 5 * 1024 * 1024)
        for length in (0, -1, 5 * 1024 * 1024 + 1):
            with self.assertRaises(UploadRejected):
                uc.execute(io.BytesIO(b""), length)
        self.assertEqual(storage.entered, 0)

    def test_scanner_errors_propagate_and_storage_is_still_cleaned(self):
        storage = FakeStorage()
        uc = ScanApk(storage, FakeScanner(error=InvalidApk("nope")), 1000)
        with self.assertRaises(InvalidApk):
            uc.execute(io.BytesIO(b"x"), 1)
        self.assertEqual(storage.exited, 1)


class TempUploadStorageTests(unittest.TestCase):
    def test_streams_to_file_and_deletes_it(self):
        with TempUploadStorage().store(io.BytesIO(b"hello world"), 5) as path:
            self.assertEqual(path.read_bytes(), b"hello")
        self.assertFalse(path.exists())

    def test_truncated_upload_raises_and_leaves_nothing(self):
        seen = []
        with self.assertRaises(UploadIncomplete):
            with TempUploadStorage().store(io.BytesIO(b"abc"), 10) as path:
                seen.append(path)
        self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
