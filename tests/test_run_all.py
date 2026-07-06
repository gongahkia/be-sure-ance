import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from src.scrapers import run_all
from src.scrapers.registry import EXPERIMENTAL_SCRAPERS, SUPPORTED_SCRAPERS


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

    def test_default_scraper_set_excludes_experimental_modules(self):
        default_stems = [path.stem for path in run_all.list_scraper_scripts()]

        self.assertEqual(default_stems, list(SUPPORTED_SCRAPERS))
        for scraper in EXPERIMENTAL_SCRAPERS:
            self.assertNotIn(scraper, default_stems)

    def test_experimental_scrapers_require_explicit_opt_in(self):
        with (
            patch.object(sys, "argv", ["run_all.py", "--only", "china_taiping"]),
            self.assertRaises(SystemExit) as context,
        ):
            run_all.main()

        self.assertIn("--include-experimental", str(context.exception))

    def test_include_experimental_allows_selected_experimental_scraper(self):
        completed = type("CompletedProcess", (), {"returncode": 0})()

        with (
            patch.object(
                sys,
                "argv",
                ["run_all.py", "--only", "china_taiping", "--include-experimental", "--dry-run"],
            ),
            patch("src.scrapers.run_all.subprocess.run", return_value=completed) as run,
        ):
            run_all.main()

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:3], [sys.executable, "-m", "src.scrapers.china_taiping"])
        self.assertIn("--dry-run", command)


if __name__ == "__main__":
    unittest.main()
