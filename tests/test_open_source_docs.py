import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


class OpenSourceDocsTests(unittest.TestCase):
    def test_license_is_explicit_mit(self):
        license_text = read("LICENSE")

        self.assertIn("MIT License", license_text)
        self.assertIn("Be-sure-ance contributors", license_text)

    def test_contributing_documents_setup_tests_workflow_and_data_quality(self):
        contributing = read("CONTRIBUTING.md")

        for required in (
            "pip install -r requirements.txt",
            "npm --prefix src/be-sure-ance-app ci",
            "python -m unittest discover -s tests",
            "Use GitHub issues for scoped work.",
            "source_url",
            "source_type",
            "last_verified_at",
            "Do not infer premiums",
            "docs/COMPLIANCE.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, contributing)

    def test_code_of_conduct_exists_with_reporting_path(self):
        conduct = read("CODE_OF_CONDUCT.md")

        for required in (
            "Expected behavior",
            "Unacceptable behavior",
            "Enforcement",
            "gabrielzmong@gmail.com",
        ):
            with self.subTest(required=required):
                self.assertIn(required, conduct)

    def test_readme_links_open_source_docs(self):
        readme = read("README.md")

        for required in (
            "[CONTRIBUTING.md](./CONTRIBUTING.md)",
            "[CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)",
            "MIT licensed",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)


if __name__ == "__main__":
    unittest.main()
