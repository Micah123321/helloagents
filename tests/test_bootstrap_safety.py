"""Static safety checks for bootstrap installers."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BootstrapSafetyTests(unittest.TestCase):
    def test_powershell_pins_commit_and_has_no_global_remnant_delete(self):
        content = (ROOT / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("git ls-remote", content)
        self.assertIn("@$Commit", content)
        self.assertNotIn('-Filter "~*"', content)
        self.assertNotIn("Remove-Item", content)
        self.assertNotIn(" -c ", content)
        self.assertNotIn("| iex", content)

    def test_shell_pins_commit_and_has_no_global_remnant_delete(self):
        content = (ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("git ls-remote", content)
        self.assertIn("@${COMMIT}", content)
        self.assertNotIn('"$sp_dir"/~*', content)
        self.assertNotIn("rm -rf", content)
        self.assertNotIn(' -c "import site', content)
        self.assertNotIn("| bash", content)


if __name__ == "__main__":
    unittest.main()
