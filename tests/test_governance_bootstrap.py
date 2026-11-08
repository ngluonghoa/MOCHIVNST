"""Read-only bootstrap smoke tests; not full security enforcement tests.

These only verify the initial repository policy markers and safe workflow
defaults. GOV-01..GOV-10 require separate, real remote denial evidence.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
WORKFLOW = ROOT / ".github" / "workflows" / "governance-ci.yml"


class TestGovernanceBootstrap(unittest.TestCase):
    def test_readme_has_canonical_governance_reference(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("MOCHIVNST", text)
        self.assertIn("Canonical gate: https://docs.google.com/document/d/", text)
        self.assertIn("P0 not yet enforced", text)

    def test_workflow_uses_read_only_token(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("persist-credentials: false", text)

    def test_workflow_avoids_privileged_pr_triggers(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("workflow_run:", text)

    def test_workflow_pins_actions_and_test_versions(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", text)
        self.assertIn("actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1", text)
        self.assertIn('python-version: ["3.11", "3.12"]', text)


if __name__ == "__main__":
    unittest.main()
