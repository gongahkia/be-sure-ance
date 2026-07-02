import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR = (ROOT / "docs/adr/0001-defer-chrome-extension-sidebar.md").read_text()


class ChromeExtensionScopeTests(unittest.TestCase):
    def test_adr_records_defer_decision(self):
        for required in (
            "Accepted - defer implementation.",
            "Defer extension implementation until after Phase 3 exit verification.",
            "No extension work blocks Phase 3 exit.",
            "avoids adding `src/extension` source",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_adr_scopes_mv3_sidebar_and_content_script_behavior(self):
        for required in (
            "side_panel.default_path",
            "chrome.sidePanel.open()",
            "Content scripts can read and modify page DOM",
            "Content script that scans visible page text for known plan names",
            "Sidebar fact card showing plan name, carrier, source-traceable facts",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_adr_defines_blockers_and_restart_conditions(self):
        for required in (
            "Production/staging endpoint",
            "Extension privacy copy",
            "Supported carrier-domain permission list",
            "DOM-highlighting QA",
            "Chrome Web Store privacy/disclosure checklist",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_adr_lists_future_implementation_issue_scope(self):
        for required in (
            "Build MV3 manifest",
            "Implement plan-name content-script highlighter",
            "Implement sidebar fact card",
            "Add read-only data API/cache layer",
            "Add extension permission/privacy QA",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_no_extension_source_tree_created_while_deferred(self):
        self.assertFalse((ROOT / "src/extension").exists())


if __name__ == "__main__":
    unittest.main()
