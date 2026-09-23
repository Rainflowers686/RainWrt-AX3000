#!/usr/bin/env python3
import hashlib
import pathlib
import tempfile
import unittest
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scripts import local_bdf


class LocalBdfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.source = self.root / "local"
        self.dest = self.root / "staging"
        self.source.mkdir()
        self.dest.mkdir()
        self.files = {"radio-a.bin": b"fixture-radio-a", "radio-b.bin": b"fixture-radio-b"}
        self.expected = {name: hashlib.sha256(data).hexdigest() for name, data in self.files.items()}
        for name, data in self.files.items():
            (self.source / name).write_bytes(data)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_files_validate_and_stage(self):
        local_bdf.validate(self.source, self.expected)
        local_bdf.stage(self.source, self.dest, self.expected)
        for name, data in self.files.items():
            self.assertEqual((self.dest / name).read_bytes(), data)

    def test_missing_input_fails(self):
        (self.source / "radio-b.bin").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            local_bdf.validate(self.source, self.expected)

    def test_mismatched_hash_fails_before_staging(self):
        (self.source / "radio-a.bin").write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            local_bdf.stage(self.source, self.dest, self.expected)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_unexpected_entry_fails(self):
        (self.source / "extra.bin").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "unexpected entries"):
            local_bdf.validate(self.source, self.expected)

    def test_conflicting_destination_fails_before_any_copy(self):
        (self.dest / "radio-b.bin").write_bytes(b"conflict")
        with self.assertRaisesRegex(ValueError, "conflicting"):
            local_bdf.stage(self.source, self.dest, self.expected)
        self.assertFalse((self.dest / "radio-a.bin").exists())


if __name__ == "__main__":
    unittest.main()
