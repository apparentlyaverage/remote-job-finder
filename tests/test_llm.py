import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from llm import _parse_response


class TestParseResponse(unittest.TestCase):
    def test_well_formed_response(self):
        text = (
            "FIT: 4\n"
            "RESUME_ANGLE: Lead with the ReLivR backend work.\n"
            "BLURB: I built and shipped ReLivR end to end. This role's Node.js "
            "focus lines up directly with that experience. I'd bring the same "
            "ownership here."
        )
        result = _parse_response(text)
        self.assertEqual(result["fit"], 4)
        self.assertIn("ReLivR backend", result["resume_angle"])
        self.assertIn("shipped ReLivR", result["blurb"])

    def test_multiline_blurb(self):
        text = "FIT: 3\nRESUME_ANGLE: data projects\nBLURB: First line.\nSecond line."
        result = _parse_response(text)
        self.assertEqual(result["blurb"], "First line. Second line.")

    def test_malformed_falls_back_to_raw_text(self):
        text = "Sure, here's a paragraph about the job with no labels at all."
        result = _parse_response(text)
        self.assertIsNone(result["fit"])
        self.assertEqual(result["resume_angle"], "")
        self.assertEqual(result["blurb"], text)

    def test_fit_extracts_leading_digit_from_noisy_value(self):
        text = "FIT: 5/5 strong match\nRESUME_ANGLE: x\nBLURB: y"
        result = _parse_response(text)
        self.assertEqual(result["fit"], 5)


if __name__ == "__main__":
    unittest.main()
