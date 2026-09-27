import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest

from filters import dedupe_against_seen, filter_jobs, load_seen, matches, save_seen
from sources import Job


def make_job(title="Junior Python Developer", description="Remote role, Python, Django."):
    return Job(id="x:1", source="test", title=title, company="Acme", url="https://x", description=description)


class TestMatches(unittest.TestCase):
    def test_include_keyword_hits(self):
        job = make_job()
        self.assertTrue(matches(job, ["python developer"], []))

    def test_no_keyword_hit_excludes(self):
        job = make_job(title="Sales Rep", description="Sell things.")
        self.assertFalse(matches(job, ["python developer"], []))

    def test_exclude_title_keyword_wins(self):
        job = make_job(title="Senior Python Developer")
        self.assertFalse(matches(job, ["python developer"], ["senior"]))

    def test_case_insensitive(self):
        job = make_job(title="JUNIOR PYTHON DEVELOPER")
        self.assertTrue(matches(job, ["python developer"], ["senior"]))

    def test_description_only_boilerplate_does_not_match(self):
        # Regression: the first version of this filter matched keywords
        # against title+description, so an unrelated posting whose
        # description happened to say "entry-level friendly, no experience
        # needed" got pulled in even though the title was irrelevant.
        job = make_job(
            title="Hotline Paralegal",
            description="Entry level, internship-friendly. Junior staff welcome, no experience needed.",
        )
        self.assertFalse(
            matches(job, ["software engineer", "junior developer", "developer intern"], [])
        )

    def test_real_tech_title_still_matches_regardless_of_description(self):
        job = make_job(
            title="Junior Software Engineer",
            description="We sell insurance. Nothing technical in here at all.",
        )
        self.assertTrue(matches(job, ["junior software engineer"], []))


class TestFilterJobs(unittest.TestCase):
    def test_filters_list(self):
        jobs = [make_job(), make_job(title="Senior Engineer")]
        result = filter_jobs(jobs, ["python developer", "engineer"], ["senior"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Junior Python Developer")


class TestSeenPersistence(unittest.TestCase):
    def test_roundtrip(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            seen_path = Path(d) / "seen.json"
            self.assertEqual(load_seen(seen_path), set())
            save_seen(seen_path, {"a", "b"})
            self.assertEqual(load_seen(seen_path), {"a", "b"})

    def test_dedupe(self):
        jobs = [make_job(), make_job(title="Other")]
        jobs[1].id = "x:2"
        result = dedupe_against_seen(jobs, {"x:1"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "x:2")


if __name__ == "__main__":
    unittest.main()
