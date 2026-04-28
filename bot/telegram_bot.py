import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

from research.fetcher import (
    fetch_arxiv_papers,
    fetch_huggingface_trending,
    fetch_papers_with_code,
    fetch_hackernews,
    fetch_github_trending,
    fetch_web_news,
)
from research.analyzer import analyze_research
import anthropic
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

SOURCES_INFO = (
    "📡 *Источники данных:*\n"
    "• arxiv (cs.CL, cs.SD, eess.AS)\n"
    "• HuggingFace Trending\n"
    "• Papers With Code\n"
    "• Hacker News (топ за 7 дней)\n"
    "• GitHub Trending (новые репо за 14 дней)\n"
    "• Tavily Web Search (если настроен)\n"
)

ASK_SYSTEM_PROMPT = """Ты — эксперт по Speech/NLP индустрии, советник продакт-менеджера.
Отвечай конкретно и практично, без воды. Упоминай названия моделей/компаний когда уместно.
Формат ответа: короткий Markdown, совместимый с Telegram. Отвечай на языке пользователя."""


class ResearchBot:
    def __init__(
        self,
        token: str,
        chat_id: str,
        anthropic_key: str,
        schedule_hour: int = 9,
        schedule_minute: int = 0,
        tavily_key: str | None = None,
    ):
        self.token = token
        self.chat_id = chat_id
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        self.tavily_key = tavily_key
        self.schedule_hour = schedule_hour
        self.schedule_minute = schedule_minute
        self.scheduler = AsyncIOScheduler()
        self.app = (
            Application.builder()
            .token(token)
            .post_init(self._post_init)
            .build()
        )
        self._setup_handlers()

    async def _post_init(self, application: Application):
        self.scheduler.add_job(
            self.send_scheduled_digest,
            "cron",
            hour=self.schedule_hour,
            minute=self.schedule_minute,
            id="daily_digest",
        )
        self.scheduler.start()
        logger.info(
            f"Scheduler started. Daily digest at "
            f"{self.schedule_hour:02d}:{self.schedule_minute:02d} UTC"
        )

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("research", self.cmd_research))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.cmd_ask)
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 *Speech/NLP Research Bot* запущен!\n\n"
            "Просто напиши любой вопрос о Speech/NLP индустрии — отвечу.\n\n"
            "Команды:\n"
            "/research — полный дайджест из 6 источников\n"
            "/help — справка",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "*Speech/NLP Research Bot*\n\n"
            + SOURCES_INFO
            + "\nАнализ делает Claude.\n\n"
            "Можно просто написать вопрос текстом — отвечу.\n"
            "/research — полный дайджест",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        question = update.message.text
        msg = await update.message.reply_text("🤔 Думаю...")
        try:
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None, self._ask_claude, question
            )
            await msg.edit_text(answer, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Ask failed: {e}")
            await msg.edit_text(f"❌ Ошибка: {e}")

    def _ask_claude(self, question: str) -> str:
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=ASK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text

    async def cmd_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text(
            "🔄 Собиႈаю данные из 6 источников, анализиႈую чеႈез Claude...\n"
            "Обычно занимает 30–60 секунд."
        )
        try:
            digest = await self._run_research()
            await self._send_digest(digest, update.effective_chat.id)
            await msg.delete()
        except Exception as e:
            logger.error(f"Research failed: {e}")
            await msg.edit_text(f"❌ Ошибка: {e}")

    async def _run_research(self) -> str:
        loop = asyncio.get_event_loop()
        (
            papers,
            hf_models,
            pwc_papers,
            hn_stories,
            github_repos,
        ) = await asyncio.gather(
            loop.run_in_executor(None, fetch_arxiv_papers, 15),
            loop.run_in_executor(None, fetch_huggingface_trending, 12),
            loop.run_in_executor(None, fetch_papers_with_code, 10),
            loop.run_in_executor(None, fetch_hackernews, 10),
            loop.run_in_executor(None, fetch_github_trending, 10),
        )
        news = (
            await loop.run_in_executor(None, fetch_web_news, self.tavily_key, 10)
            if self.tavily_key
            else []
        )
        return await loop.run_in_executor(
            None,
            analyze_research,
            papers, hf_models, pwc_papers, hn_stories, github_repos, news,
            self.anthropic_client,
        )

    async def send_scheduled_digest(self):
        try:
            digest = await self._run_research()
            await self._send_digest(digest, self.chat_id)
        except Exception as e:
            logger.error(f"Scheduled research failed: {e}")

    async def _send_digest(self, text: str, chat_id: str | int):
        bot = Bot(token=self.token)
        chunks = [text[i: i + 4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN,
            )

    def run(self):
        print(
            f"Bot started. Daily digest at "
            f"{self.schedule_hour:02d}:{self.schedule_minute:02d} UTC"
        )
        self.app.run_polling()
