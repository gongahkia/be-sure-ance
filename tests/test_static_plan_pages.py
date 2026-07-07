import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
PACKAGE_JSON = (ROOT / "src/be-sure-ance-app/package.json").read_text()
SSG_SCRIPT = (ROOT / "src/be-sure-ance-app/scripts/generate-static-pages.mjs").read_text()
README = (ROOT / "README.md").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()
CI_WORKFLOW = (ROOT / ".github/workflows/ci.yml").read_text()
NETLIFY_REDIRECTS = (ROOT / "src/be-sure-ance-app/public/_redirects").read_text()


class StaticPlanPagesTests(unittest.TestCase):
    def test_build_runs_static_plan_generator_after_vite(self):
        self.assertIn(
            '"build:app": "vite build && node scripts/generate-static-pages.mjs"', PACKAGE_JSON
        )
        self.assertIn("scripts/**/*.mjs", PACKAGE_JSON)

    def test_generator_builds_plan_pages_json_ld_and_sitemap(self):
        for required in (
            "planRoutePath(plan)",
            "FinancialProduct",
            "sitemap.xml",
            "robots.txt",
            "VITE_SITE_ORIGIN",
            "app-data.json",
            "plan_facts",
            "source_url",
            "last_verified_at",
            "subjectOf",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SSG_SCRIPT)

    def test_generator_avoids_quantitative_structured_data_fields(self):
        for forbidden in (
            "annualPercentageRate",
            "feesAndCommissionsSpecification",
            "interestRate",
            '"offers"',
            "premium",
            "deductible",
            "coinsurance",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, SSG_SCRIPT)

    def test_spa_handles_plan_routes_without_breaking_matrix_route(self):
        for required in (
            "const routePlanTarget = computed(() => parsePlanRoute(currentPath.value))",
            "function parsePlanRoute(path)",
            "providerKeyFromPath(window.location.pathname)",
            "plan.plan_slug === routeTarget.planSlug",
            "path === '/matrix/panel-hospitals'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_detail_plan_layout_does_not_stretch_sparse_cards(self):
        for required in (
            ".repo-layout {",
            "align-items: start",
            ".repo-main {",
            "align-content: start",
            "align-self: start",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_plan_cards_link_to_static_plan_pages(self):
        for required in (
            'v-if="planPagePath"',
            ':href="planPagePath"',
            "encodeURIComponent(props.plan.providerKey)",
            "encodeURIComponent(props.plan.plan_slug)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_sitemap_origin_is_documented_for_ci_and_phase_5(self):
        for required in (
            "VITE_SITE_ORIGIN=",
            "VITE_SITE_ORIGIN",
            "Submit `<origin>/sitemap.xml`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ENV_EXAMPLE + README + CI_WORKFLOW)

    def test_static_host_rewrites_share_routes_to_spa(self):
        self.assertIn("/share/* /index.html 200", NETLIFY_REDIRECTS)


if __name__ == "__main__":
    unittest.main()
