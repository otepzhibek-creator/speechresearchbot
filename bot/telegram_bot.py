import asyncio
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

from research.fetcher import fetch_arxiv_papers, fetch_huggingface_trending, fetch_web_news
from research.analyzer import analyze_research
import anthropic

logger = logging.getLogger(__name__)


class ResearchBot:
    def __init__(
        self,
        token: str,
        chat_id: str,
        anthropic_key: str,
        tavily_key: str | None = None,
    ):
        self.token = token
        self.chat_id = chat_id
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        self.tavily_key = tavily_key
        self.app = Application.builder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("research", self.cmd_research))
        self.app.add_handler(CommandHandler("help", self.cmd_help))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 *Speech/NLP Research Bot* запущен!\n\n"
            "Каждый день в заданное время я буду присылать дайджест "
            "о новинках Speech и NLP индустрии — с продуктовым взглядом.\n\n"
            "Команды:\n"
            "/research — исследование прямо сейчас\n"
            "/help — справка",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "*Speech/NLP Research Bot*\n\n"
            "Источники данных:\n"
            "• arxiv (cs.CL, cs.SD, eess.AS) — новые статьи\n"
            "• HuggingFace Trending — трендовые модели\n"
            "• Tavily Web Search — новости (если настроен)\n\n"
            "Анализ делает Claude, дайджест на русском.\n\n"
            "/research — запустить вручную",
            parse_mode=ParseMode.MARKDOWN,
        )

    async def cmd_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("🔄 Собираю данные и анализирую, подождите ~30 сек...")
        try:
            digest = await self._run_research()
            await self._send_digest(digest, update.effective_chat.id)
            await msg.delete()
        except Exception as e:
            logger.error(f"Research failed: {e}")
            await msg.edit_text(f"❌ Ошибка: {e}")

    async def _run_research(self) -> str:
        loop = asyncio.get_event_loop()
        papers, hf_models = await asyncio.gather(
            loop.run_in_executor(None, fetch_arxiv_papers, 15),
            loop.run_in_executor(None, fetch_huggingface_trending, 12),
        )
        if self.tavily_key:
            news = await loop.run_in_executor(None, fetch_web_news, self.tavily_key, 10)
        else:
            news = []

        digest = await loop.run_in_executor(
            None, analyze_research, papers, hf_models, news, self.anthropic_client
        )
        return digest

    async def send_scheduled_digest(self):
        """Called by the scheduler for the daily digest."""
        try:
            digest = await self._run_research()
            await self._send_digest(digest, self.chat_id)
        except Exception as e:
            logger.error(f"Scheduled research failed: {e}")

    async def _send_digest(self, text: str, chat_id: str | int):
        bot = Bot(token=self.token)
        # Telegram message limit is 4096 chars
        chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN,
            )

    def run(self):
        self.app.run_polling()
