import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.demo_supabase_api import app

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


class LocalDockerStackTests(unittest.TestCase):
    def test_demo_supabase_api_select_insert_and_update(self):
        client = TestClient(app)
        share_id = "22222222-3333-4444-8555-666666666666"

        plans = client.get("/rest/v1/plans", params={"select": "*"})
        self.assertEqual(plans.status_code, 200)
        self.assertGreaterEqual(len(plans.json()), 2)

        insert_response = client.post(
            "/rest/v1/comparison_shares",
            json=[
                {
                    "id": share_id,
                    "selected_plans": [
                        {"insurer": "aia", "plan_slug": "healthshield-gold-max-demo"}
                    ],
                    "view_count": 0,
                    "created_at": "2026-07-02T00:00:00+00:00",
                }
            ],
        )
        self.assertEqual(insert_response.status_code, 200)

        patch_response = client.patch(
            "/rest/v1/comparison_shares",
            params={"id": f"eq.{share_id}"},
            json={"view_count": 1, "last_viewed_at": "2026-07-02T00:01:00+00:00"},
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()[0]["view_count"], 1)

        select_response = client.get(
            "/rest/v1/comparison_shares",
            params={"select": "*", "id": f"eq.{share_id}", "limit": "1"},
        )
        self.assertEqual(select_response.status_code, 200)
        self.assertEqual(select_response.json()[0]["last_viewed_at"], "2026-07-02T00:01:00+00:00")

    def test_compose_defines_default_demo_stack_and_profiles(self):
        compose = read("docker-compose.yml")

        for required in (
            "supabase-local:",
            "backend:",
            "frontend:",
            "scraper:",
            "bot:",
            "profiles:",
            "tools",
            "http://localhost:54321",
            "http://localhost:8000/briefs/client.pdf",
            "http://localhost:8000/shares",
        ):
            with self.subTest(required=required):
                self.assertIn(required, compose)

    def test_compose_uses_fake_local_values_without_real_secret_placeholders(self):
        compose = read("docker-compose.yml")

        self.assertIn("sb_secret_local_demo_not_real", compose)
        for forbidden in (
            "your-sb-secret-key",
            "your-service-role-jwt",
            "your-telegram-bot-token",
            "https://your-project-ref.supabase.co",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, compose)

    def test_demo_supabase_api_exposes_seed_tables_and_postgrest_routes(self):
        demo_api = read("src/backend/demo_supabase_api.py")
        demo_data = read("src/backend/demo_data.py")

        for required in (
            '@app.get("/rest/v1/{table_name}")',
            '@app.post("/rest/v1/{table_name}")',
            '@app.patch("/rest/v1/{table_name}")',
            "plans",
            "plan_facts",
            "comparison_shares",
            "HealthShield Gold Max Demo",
            "Mount Elizabeth Novena Hospital",
        ):
            with self.subTest(required=required):
                self.assertIn(required, demo_api + demo_data)

    def test_readme_documents_one_command_demo_without_prod_supabase(self):
        readme = read("README.md")

        for required in (
            "docker compose up --build",
            "http://localhost:5173",
            "in-memory Supabase-compatible demo API",
            "does not require production Supabase credentials",
            "docker compose run --rm scraper",
            "docker compose --profile bot up bot",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)

    def test_env_example_warns_not_to_put_prod_secrets_in_compose(self):
        env_example = read(".env.example")

        self.assertIn("docker compose up --build injects fake local values", env_example)
        self.assertIn("Do not replace those compose values with production secrets.", env_example)


if __name__ == "__main__":
    unittest.main()
