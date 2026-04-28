import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.telegram_bot import ResearchBot
from config import (
    ANTHROPIC_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TAVILY_API_KEY,
    RESEARCH_SCHEDULE_HOUR,
    RESEARCH_SCHEDULE_MINUTE,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)


def main():
    missing = [
        k for k, v in {
            "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        }.items() if not v
    ]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    bot = ResearchBot(
        token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        anthropic_key=ANTHROPIC_API_KEY,
        tavily_key=TAVILY_API_KEY,
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        bot.send_scheduled_digest,
        "cron",
        hour=RESEARCH_SCHEDULE_HOUR,
        minute=RESEARCH_SCHEDULE_MINUTE,
        id="daily_digest",
    )
    scheduler.start()

    print(
        f"Bot started. Daily digest scheduled at "
        f"{RESEARCH_SCHEDULE_HOUR:02d}:{RESEARCH_SCHEDULE_MINUTE:02d} UTC"
    )
    bot.run()


if __name__ == "__main__":
    main()
