import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


class EnvironmentContractTests(unittest.TestCase):
    def test_env_example_separates_public_and_private_keys(self):
        env_example = read(".env.example")

        self.assertIn("VITE_STATIC_DATA_PATH=", env_example)
        self.assertIn("VITE_PDF_BRIEF_ENDPOINT=", env_example)
        self.assertIn("VITE_SITE_ORIGIN=", env_example)
        self.assertIn("NETLIFY_BUILD_HOOK_URL=", env_example)
        self.assertIn("TELEGRAM_BOT_TOKEN=", env_example)
        self.assertIn("Never expose", env_example)

    def test_frontend_uses_static_data_only(self):
        app_vue = read("src/be-sure-ance-app/src/App.vue")

        self.assertIn("loadAppData", app_vue)
        self.assertNotIn("VITE_SUPABASE", app_vue)
        self.assertNotIn("SUPABASE_", app_vue)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", app_vue)
        self.assertNotIn("VUE_APP_", app_vue)

    def test_refresh_workflow_uses_netlify_build_hook(self):
        workflow = read(".github/workflows/refresh-static-data.yml")

        self.assertIn("NETLIFY_BUILD_HOOK_URL", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("static_app_data --run-scrapers --output", workflow)
        self.assertIn("scripts/validate_static_app_data.py", workflow)
        self.assertIn('git commit -m "chore(data): refresh static app data [skip ci]"', workflow)
        self.assertIn("curl -fsS -X POST -d '{}'", workflow)
        self.assertNotIn("--fallback-demo", workflow)
        self.assertNotIn("SUPABASE", workflow)

    def test_readme_documents_local_and_actions_secrets(self):
        readme = read("README.md")

        for required in (
            "VITE_STATIC_DATA_PATH",
            "VITE_PDF_BRIEF_ENDPOINT",
            "VITE_SITE_ORIGIN",
            "NETLIFY_BUILD_HOOK_URL",
            "TELEGRAM_BOT_TOKEN",
            "Netlify only needs",
            "GitHub Actions uses",
            "Never expose",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)

    def test_gitignore_blocks_local_env_but_allows_template(self):
        gitignore = read(".gitignore")

        self.assertIn(".env", gitignore)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)
        self.assertIn("src/be-sure-ance-app/public/data/*", gitignore)
        self.assertIn("!src/be-sure-ance-app/public/data/app-data.json", gitignore)

    def test_netlify_uses_vite_dist_output(self):
        netlify = read("netlify.toml")

        self.assertIn('publish = "src/be-sure-ance-app/dist"', netlify)
        self.assertIn('functions = "netlify/functions"', netlify)
        self.assertIn("npm --prefix src/be-sure-ance-app run build:app", netlify)
        self.assertIn("scripts/netlify_ignore_data_refresh.sh", netlify)
        self.assertNotIn("static_app_data --run-scrapers", netlify)
        self.assertNotIn("playwright install", netlify)
        self.assertNotIn("pip install -r requirements.txt", netlify)

    def test_netlify_ignore_skips_scheduled_data_refresh_commits_only(self):
        ignore_script = read("scripts/netlify_ignore_data_refresh.sh")

        self.assertIn("src/be-sure-ance-app/public/data/app-data.json", ignore_script)
        self.assertIn("chore(data): refresh static app data", ignore_script)
        self.assertIn("exit 0", ignore_script)
        self.assertIn("exit 1", ignore_script)


if __name__ == "__main__":
    unittest.main()
