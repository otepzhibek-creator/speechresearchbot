# Speech/NLP Research Bot

Telegram-бот для продакт-менеджеров, который ежедневно мониторит Speech/NLP индустрию и присылает умный продуктовый дайджест.

## Что делает

- Собирает свежие статьи с **arxiv** (cs.CL, cs.SD, eess.AS)
- Смотрит **HuggingFace Trending** модели в сфере Speech и NLP
- Ищет **веб-новости** через Tavily (опционально)
- Анализирует всё через **Claude** и выдаёт дайджест на русском:
  - Главные тренды
  - Новые модели и прорывы
  - Продуктовые возможности
  - Риски и угрозы
  - Конкретные рекомендации PM

## Быстрый старт

### 1. Установка

```bash
pip install -r requirements.txt
```

### 2. Настройка

```bash
cp .env.example .env
```

Заполни `.env`:

| Переменная | Описание | Обязательна |
|---|---|---|
| `ANTHROPIC_API_KEY` | Ключ от [Anthropic Console](https://console.anthropic.com/) | Да |
| `TELEGRAM_BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) | Да |
| `TELEGRAM_CHAT_ID` | Твой chat ID (узнай через [@userinfobot](https://t.me/userinfobot)) | Да |
| `TAVILY_API_KEY` | Ключ от [Tavily](https://tavily.com/) для веб-поиска | Нет |
| `RESEARCH_SCHEDULE_HOUR` | Час отправки дайджеста (UTC, default: 9) | Нет |
| `RESEARCH_SCHEDULE_MINUTE` | Минута отправки (default: 0) | Нет |

### 3. Запуск

```bash
python main.py
```

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Запустить бота |
| `/research` | Запустить исследование прямо сейчас |
| `/help` | Справка |

## Структура

```
speechresearchbot/
├── main.py              # точка входа, планировщик
├── config.py            # загрузка env-переменных
├── bot/
│   └── telegram_bot.py  # Telegram-хендлеры
└── research/
    ├── fetcher.py       # данные из arxiv, HuggingFace, Tavily
    └── analyzer.py      # анализ через Claude
```
