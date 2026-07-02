# Telegram Bot Beta

## Library Choice

Use `python-telegram-bot==22.8`. It matches the Python scraper/backend stack and avoids adding a Node/Telegraf runtime.

## Environment

Required private variables:

```sh
TELEGRAM_BOT_TOKEN=
SUPABASE_URL=
SUPABASE_SECRET_KEY=
# or legacy fallback:
SUPABASE_SERVICE_ROLE_KEY=
```

Do not expose `TELEGRAM_BOT_TOKEN`, `SUPABASE_SECRET_KEY`, or `SUPABASE_SERVICE_ROLE_KEY` through `VITE_*` variables.

## Commands

- `/panel <hospital name>`: returns matching plan panel-hospital facts.
- `/fact <plan name or slug> [coverage|panel|waiting|claim|exclusions|brochure]`: returns source-traceable plan facts.

Responses include source URL, verified date, and no-advice wording. Missing data returns a safe failure or no-match message.

## Deployment

Run as a backend worker, not inside the Vue frontend:

```sh
python -m src.bot.telegram_bot
```

The beta uses long polling. Move to a webhook only after Phase 5 deployment decisions are complete.

## Privacy Boundary

The bot does not persist Telegram chat IDs, messages, usernames, or phone numbers. Rate limiting is in memory only. Telegram as a platform may process chat metadata outside this repository; document that before any public launch.
