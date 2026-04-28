import json
import anthropic

SYSTEM_PROMPT = """Ты — экспертный аналитик Speech/NLP индустрии, работающий напрямую с продакт-менеджером.

Твоя задача — изучить свежие данные (arxiv-статьи, трендовые модели HuggingFace, новости) и выдать
чёткий, практичный продуктовый дайджест. Пиши как умный коллега, без воды.

Формат (Markdown, совместимый с Telegram):

🔥 *Главные тренды*
— 3-5 трендов, которые реально важны прямо сейчас

🤖 *Новые модели и прорывы*
— что вышло, что это меняет на рынке

💡 *Продуктовые возможности*
— конкретные идеи: что можно добавить/улучшить в продукте, используя новые технологии

⚠️ *Риски и угрозы*
— что может быть disruption для вашего продукта, за чем следить

✅ *Рекомендации PM*
— 3-5 конкретных следующих шагов (не абстрактных, а действенных)

Пиши на русском. Будь конкретным. Указывай названия моделей/компаний/стартапов когда они есть."""


def analyze_research(
    papers: list[dict],
    hf_models: list[dict],
    news_items: list[dict],
    client: anthropic.Anthropic,
) -> str:
    data = {
        "arxiv_papers": [
            {"title": p["title"], "summary": p["summary"], "date": p["published"]}
            for p in papers[:12]
        ],
        "trending_hf_models": [
            {"id": m["id"], "pipeline": m["pipeline_tag"], "likes": m["likes"]}
            for m in hf_models[:10]
        ],
        "web_news": [
            {"title": n["title"], "content": n["content"]}
            for n in news_items[:8]
        ],
    }

    user_message = (
        "Вот свежие данные о Speech/NLP индустрии:\n\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n\nСделай продуктовый дайджест."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text
