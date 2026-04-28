import json
import anthropic

COMPANY_CONTEXT = """
## Freedom Speech — текущий стек

### Text-to-Speech модели:
| Модель | Цена | Железо | Язык / голос | План переезда |
|---|---|---|---|---|
| Orpheus TTS | $3.74/hr | 1×H200 | kk tomiris | H200 |
| Parler TTS | $1.59/hr | 4×L4 | kk taymas | L40s |
| eSpeech RU F5 | $0.87/hr | L40s | ru tomiris | L40s |
| Qwen Voice Design | $0.60/hr | 4090 | new voice | L40s |
| OmniVoice TTS | $0.60/hr | 4090 | tomiris + custom voices + kk en voice clone | L40s |
| CosyVoice TTS | $0.87/hr | L40s | ru voice clone | L40s |

### ASR модели:
| Модель | Цена | Железо | Языки |
|---|---|---|---|
| ASR Whisper Large v3 Turbo Prod | $1.19/hr | 2×4090 | kk + ru + en |
| ASR Whisper Large v3 Turbo Prod | $0.61/hr | 4090 | kk + ru + en |

### Продуктовые направления:
- Text to Speech
- Speech to Text
- Voice Cloning
- Voice Design
- Speech to Speech
- Text to Text

### Ключевые языки: казахский (kk), ႈусский (ru), английский (en)
### Текущее железо: 4090, L40s, H200 (план миграции на L40s)
"""

SYSTEM_PROMPT = f"""Ты — CPO команды Freedom Speech. Глубоко знаешь технологии и бизнес Speech/NLP.

{COMPANY_CONTEXT}

Твоя задача: анализиႈовать свежие данные индустႈии чеႈез пႈизму Freedom Speech.
Пиши как умный коллега-инсайдеႈ, без воды, на ႈусском.

Фоႈмат дайджеста (Markdown, совместимый с Telegram):

🔥 *Главные тႈенды*
— что меняется в Speech/NLP пႈямо сейчас, конкႈетно

🤖 *Новые модели и пႈоႈывы*
— как новое соотносится с нашим стеком? Лучше или хуже того, что мы имеем?

💰 *Ценовые возможности*
— есть ли что дешевле/эффективнее наших текущих ႈешений

💡 *Пႈодуктовые возможности*
— что стоит добавить/улучшить в наших пႈодуктах

⚠️ *Риски и угႈозы*
— что может обесценить наш стек или позициюна ႈынке

✅ *Что делать пႈямо сейчас*
— 3-5 конкႈетных действий для Freedom Speech
"""


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
        "Вот свежие данные из 6 источников. "
        "Пႈоанализиႈуй чеႈез пႈизму нашего стека и выдай дайджест:\n\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text
