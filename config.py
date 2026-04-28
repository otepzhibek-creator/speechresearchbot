import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

RESEARCH_SCHEDULE_HOUR = int(os.getenv("RESEARCH_SCHEDULE_HOUR", "9"))
RESEARCH_SCHEDULE_MINUTE = int(os.getenv("RESEARCH_SCHEDULE_MINUTE", "0"))
