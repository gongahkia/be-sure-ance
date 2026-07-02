import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


class EnvironmentContractTests(unittest.TestCase):
    def test_env_example_separates_public_and_private_keys(self):
        env_example = read(".env.example")

        self.assertIn("VUE_APP_SUPABASE_ANON_KEY=", env_example)
        self.assertIn("SUPABASE_SECRET_KEY=", env_example)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY=", env_example)
        self.assertIn("Never expose", env_example)

    def test_frontend_uses_anon_key_only(self):
        app_vue = read("src/be-sure-ance-app/src/App.vue")

        self.assertIn("VUE_APP_SUPABASE_ANON_KEY", app_vue)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", app_vue)
        self.assertNotIn("SUPABASE_SECRET_KEY", app_vue)
        self.assertNotIn("VUE_APP_SUPABASE_KEY", app_vue)

    def test_scraper_workflow_uses_explicit_server_key_names(self):
        workflow = read(".github/workflows/scrape-to-supabase.yml")

        self.assertIn("SUPABASE_SECRET_KEY", workflow)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", workflow)
        self.assertNotIn("SUPABASE_KEY", workflow)

    def test_readme_documents_local_and_actions_secrets(self):
        readme = read("README.md")

        for required in (
            "VUE_APP_SUPABASE_ANON_KEY",
            "SUPABASE_SECRET_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "GitHub Actions requires",
            "Never expose",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)

    def test_gitignore_blocks_local_env_but_allows_template(self):
        gitignore = read(".gitignore")

        self.assertIn(".env", gitignore)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)


if __name__ == "__main__":
    unittest.main()
