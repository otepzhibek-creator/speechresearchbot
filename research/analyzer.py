import json
import anthropic

SYSTEM_PROMPT = """Ты — экспертный аналитик Speech/NLP индустрии, работающий напрямую с продакт-менеджером.

Твоя задача — изучить свежие данные из нескольких источников и выдать чёткий, практичный продуктовый дайджест.
Пиши как умный коллега, без воды. Называй конкретные модели, компании, стартапы — когда они есть в данных.

Формат (Markdown, совместимый с Telegram):

🔥 *Главные тренды*
— 3-5 трендов, которые реально важны прямо сейчас

🤖 *Новые модели и прорывы*
— что вышло, что это меняет на рынке

👨‍💻 *Что строят разработчики*
— инсайты из GitHub и HN: на что тратят время практики

💡 *Продуктовые возможности*
— конкретные идеи: что можно добавить/улучшить в продукте

⚠️ *Риски и угрозы*
— disruption, конкуренты, технологические сдвиги

✅ *Рекомендации PM*
— 3-5 конкретных следующих шагов (не абстрактных)

Пиши на русском. Будь конкретным."""


def analyze_research(
    papers: list[dict],
    hf_models: list[dict],
    pwc_papers: list[dict],
    hn_stories: list[dict],
    github_repos: list[dict],
    news_items: list[dict],
    client: anthropic.Anthropic,
) -> str:
    data = {
        "arxiv_papers": [
            {"title": p["title"], "summary": p["summary"], "date": p["published"]}
            for p in papers[:10]
        ],
        "huggingface_trending": [
            {"id": m["id"], "pipeline": m["pipeline_tag"], "likes": m["likes"]}
            for m in hf_models[:8]
        ],
        "papers_with_code_trending": [
            {
                "title": p["title"],
                "abstract": p["abstract"],
                "github_implementations": p["github_implementations"],
                "total_stars": p["total_stars"],
            }
            for p in pwc_papers[:8]
        ],
        "hackernews_top_stories": [
            {"title": h["title"], "points": h["points"], "comments": h["comments"]}
            for h in hn_stories[:8]
        ],
        "github_trending_repos": [
            {
                "name": r["name"],
                "description": r["description"],
                "stars": r["stars"],
                "topics": r["topics"],
            }
            for r in github_repos[:8]
        ],
        "web_news": [
            {"title": n["title"], "content": n["content"]}
            for n in news_items[:6]
        ],
    }

    user_message = (
        "Вот свежие данные о Speech/NLP индустрии из 6 источников:\n\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n\nСделай продуктовый дайджест."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text
