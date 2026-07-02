import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (ROOT / "requirements.txt").read_text()
README = (ROOT / "README.md").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()
BOT_DOC = (ROOT / "docs/TELEGRAM_BOT.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
BOT_RUNNER = (ROOT / "src/bot/telegram_bot.py").read_text()


class TelegramBotDocsTests(unittest.TestCase):
    def test_python_telegram_bot_dependency_is_pinned(self):
        self.assertIn("python-telegram-bot==22.8", REQUIREMENTS)

    def test_bot_token_and_deploy_path_are_documented(self):
        for required in (
            "TELEGRAM_BOT_TOKEN=",
            "python -m src.bot.telegram_bot",
            "/panel <hospital name>",
            "/fact <plan name or slug>",
            "Do not expose `TELEGRAM_BOT_TOKEN`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ENV_EXAMPLE + README + BOT_DOC)

    def test_compliance_documents_no_persistence_boundary(self):
        for required in (
            "Telegram bot beta responses are read-only plan lookups",
            "does not persist Telegram chat IDs",
            "in-memory rate limiting",
            "Telegram platform metadata handling",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPLIANCE)

    def test_runner_lazy_imports_telegram_library(self):
        self.assertIn("from telegram.ext import Application, CommandHandler", BOT_RUNNER)
        self.assertIn("def build_application", BOT_RUNNER)
        self.assertIn("TELEGRAM_BOT_TOKEN", BOT_RUNNER)


if __name__ == "__main__":
    unittest.main()
