"""PR-001 template structure tests only; cannot prove independent PR scope."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


class TestPR001Template(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE.read_text(encoding="utf-8")

    def test_atomic_objective_and_scope_fields(self):
        for phrase in (
            "PR-001", "One purpose", "Work item / milestone ID",
            "One-sentence objective", "Explicitly out of scope",
            "Dependencies on other PRs",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)

    def test_ci_qa_and_handoff_traceability(self):
        for phrase in (
            "Acceptance criteria", "Test evidence", "Python 3.11 / 3.12",
            "GitHub Actions", "Master Handoff", "Main SHA before and after",
            "Owner and scoped writer lease",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)

    def test_squash_independent_rollback_and_data_restore(self):
        for phrase in (
            "Squash only", "Exact revert steps", "independent recovery",
            "How rollback and restore will be validated",
            "Git revert cannot undo external data migration",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)

    def test_exception_requires_owner_receipt(self):
        for phrase in (
            "Owner-approved exception receipt", "explicit project-owner approval",
            "Why it cannot be split",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.template)


if __name__ == "__main__":
    unittest.main()
