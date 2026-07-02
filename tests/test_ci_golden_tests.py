import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = (ROOT / ".github/workflows/ci.yml").read_text()


class CiGoldenTests(unittest.TestCase):
    def test_ci_runs_offline_golden_tests_through_unittest_discovery(self):
        self.assertIn("Run unit and offline golden tests", CI)
        self.assertIn('python3 -m unittest discover -s tests -p "test_*.py"', CI)


if __name__ == "__main__":
    unittest.main()
