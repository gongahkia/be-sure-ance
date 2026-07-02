import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from src.scrapers import run_all


class RunAllTests(unittest.TestCase):
    def test_only_runs_selected_scraper(self):
        completed = type("CompletedProcess", (), {"returncode": 0})()
        scripts = [Path("aia.py"), Path("uoi.py")]

        with (
            patch.object(sys, "argv", ["run_all.py", "--only", "aia", "--dry-run"]),
            patch("src.scrapers.run_all.list_scraper_scripts", return_value=scripts),
            patch("src.scrapers.run_all.subprocess.run", return_value=completed) as run,
        ):
            run_all.main()

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:3], [sys.executable, "-m", "src.scrapers.aia"])
        self.assertIn("--dry-run", command)


if __name__ == "__main__":
    unittest.main()
