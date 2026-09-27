import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from settings import DEFAULTS, load_settings, save_settings


class TestSettings(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            settings = load_settings(Path(d) / "nope.json")
            self.assertEqual(settings, DEFAULTS)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.json"
            custom = dict(DEFAULTS)
            custom["ollama_model"] = "gemma3:1b"
            custom["resume_path"] = "/tmp/resume.md"
            save_settings(path, custom)
            loaded = load_settings(path)
            self.assertEqual(loaded["ollama_model"], "gemma3:1b")
            self.assertEqual(loaded["resume_path"], "/tmp/resume.md")

    def test_partial_file_gets_defaults_merged_in(self):
        # A settings.json written by an older version of setup.py, or hand-
        # edited, might be missing keys a newer version expects. Loading
        # should fill those in from DEFAULTS rather than crash on lookup.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.json"
            path.write_text(json.dumps({"ollama_model": "gemma2:9b"}), encoding="utf-8")
            loaded = load_settings(path)
            self.assertEqual(loaded["ollama_model"], "gemma2:9b")
            self.assertIn("include_keywords", loaded)
            self.assertIn("greenhouse_companies", loaded)

    def test_corrupt_file_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.json"
            path.write_text("{not valid json", encoding="utf-8")
            loaded = load_settings(path)
            self.assertEqual(loaded, DEFAULTS)


if __name__ == "__main__":
    unittest.main()
