from __future__ import annotations

import os

import src.backend.helper as helper
from src.bot.lookup import PlanFactIndex, RateLimiter, help_text, safe_answer


class LocalDataLookupProvider:
    def load_index(self) -> PlanFactIndex:
        if helper.data_store is None:
            helper.initialize_data_store()
        client = helper.require_client()
        plans = client.table("plans").select("insurer,plan_slug,plan_name").execute().data or []
        facts = (
            client.table("plan_facts")
            .select("insurer,plan_slug,field_name,field_value,source_url,last_verified_at")
            .execute()
            .data
            or []
        )
        return PlanFactIndex(plans=plans, facts=facts)


def bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")
    return token


def build_application(
    provider: LocalDataLookupProvider | None = None, limiter: RateLimiter | None = None
):
    from telegram.ext import Application, CommandHandler

    provider = provider or LocalDataLookupProvider()
    limiter = limiter or RateLimiter()

    async def start(update, context):
        await update.message.reply_text(help_text(), disable_web_page_preview=True)

    async def panel(update, context):
        await update.message.reply_text(
            safe_answer(
                command="panel",
                query=" ".join(context.args),
                index=provider.load_index(),
                chat_key=chat_key(update),
                limiter=limiter,
            ),
            disable_web_page_preview=True,
        )

    async def fact(update, context):
        await update.message.reply_text(
            safe_answer(
                command="fact",
                query=" ".join(context.args),
                index=provider.load_index(),
                chat_key=chat_key(update),
                limiter=limiter,
            ),
            disable_web_page_preview=True,
        )

    application = Application.builder().token(bot_token()).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("panel", panel))
    application.add_handler(CommandHandler("fact", fact))
    return application


def chat_key(update) -> str:
    chat = getattr(update, "effective_chat", None)
    return str(getattr(chat, "id", "unknown"))


def main() -> None:
    build_application().run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
