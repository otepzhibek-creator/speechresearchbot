import time
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta


def fetch_arxiv_papers(max_results: int = 15) -> list[dict]:
    """Latest papers from arxiv: cs.CL, cs.SD, eess.AS."""
    query = "cat:cs.CL+OR+cat:cs.SD+OR+cat:eess.AS"
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query={query}"
        "&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip()[:400]
            authors = [
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
            ][:3]
            link = entry.find("atom:id", ns).text
            published = entry.find("atom:published", ns).text[:10]
            papers.append({
                "title": title,
                "summary": summary,
                "authors": authors,
                "link": link,
                "published": published,
            })
        return papers
    except Exception as e:
        print(f"[fetcher] arxiv error: {e}")
        return []


def fetch_huggingface_trending(limit: int = 12) -> list[dict]:
    """Trending speech/NLP models from HuggingFace Hub."""
    results = []
    for tag in ("speech", "text-generation", "automatic-speech-recognition"):
        try:
            response = requests.get(
                "https://huggingface.co/api/models",
                params={"sort": "trending", "limit": limit // 2, "filter": tag},
                timeout=10,
            )
            for m in response.json():
                results.append({
                    "id": m.get("id"),
                    "likes": m.get("likes", 0),
                    "downloads": m.get("downloads", 0),
                    "tags": m.get("tags", [])[:5],
                    "pipeline_tag": m.get("pipeline_tag"),
                })
        except Exception as e:
            print(f"[fetcher] HuggingFace ({tag}) error: {e}")
    seen, unique = set(), []
    for m in results:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)
    return unique[:limit]


def fetch_papers_with_code(limit: int = 10) -> list[dict]:
    """Trending NLP/Speech papers from Papers With Code (sorted by GitHub implementations)."""
    try:
        response = requests.get(
            "https://paperswithcode.com/api/v1/papers/",
            params={
                "q": "speech language model NLP ASR TTS",
                "ordering": "-github_link_count",
                "page_size": limit,
            },
            timeout=12,
        )
        response.raise_for_status()
        data = response.json()
        results = []
        for p in data.get("results", []):
            results.append({
                "title": p.get("title", ""),
                "abstract": (p.get("abstract") or "")[:350],
                "github_implementations": p.get("github_link_count", 0),
                "total_stars": p.get("total_stars", 0),
                "published": (p.get("published") or "")[:10],
                "url": p.get("url_abs", ""),
            })
        return results
    except Exception as e:
        print(f"[fetcher] Papers With Code error: {e}")
        return []


def fetch_hackernews(limit: int = 10) -> list[dict]:
    """Recent HN stories about Speech/NLP/AI from the last 7 days, sorted by points."""
    week_ago = int(time.time()) - 7 * 24 * 3600
    try:
        response = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": "speech recognition NLP voice AI language model",
                "tags": "story",
                "hitsPerPage": limit,
                "numericFilters": f"created_at_i>{week_ago}",
            },
            timeout=10,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
        results = [
            {
                "title": h.get("title"),
                "url": h.get("url"),
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "author": h.get("author"),
            }
            for h in hits
        ]
        return sorted(results, key=lambda x: x["points"], reverse=True)
    except Exception as e:
        print(f"[fetcher] HackerNews error: {e}")
        return []


def fetch_github_trending(limit: int = 10) -> list[dict]:
    """Trending GitHub repos in NLP/Speech created in the last 14 days."""
    since = (date.today() - timedelta(days=14)).isoformat()
    queries = [
        f"topic:speech-recognition created:>{since}",
        f"topic:text-to-speech created:>{since}",
        f"topic:nlp created:>{since} language:python",
        f"topic:asr created:>{since}",
    ]
    seen, results = set(), []
    for q in queries:
        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": q, "sort": "stars", "order": "desc", "per_page": limit // 2},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            for repo in response.json().get("items", []):
                name = repo.get("full_name")
                if name not in seen:
                    seen.add(name)
                    results.append({
                        "name": name,
                        "description": (repo.get("description") or "")[:200],
                        "stars": repo.get("stargazers_count", 0),
                        "topics": repo.get("topics", [])[:6],
                        "url": repo.get("html_url"),
                        "language": repo.get("language"),
                    })
        except Exception as e:
            print(f"[fetcher] GitHub trending error ({q[:30]}): {e}")
    return sorted(results, key=lambda x: x["stars"], reverse=True)[:limit]


def fetch_web_news(api_key: str, limit: int = 10) -> list[dict]:
    """Recent Speech/NLP/AI product news via Tavily."""
    if not api_key:
        return []
    try:
        from tavily import TavilyClient  # type: ignore
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query="speech recognition NLP voice AI product launch 2025 2026",
            max_results=limit,
            search_depth="advanced",
        )
        return [
            {
                "title": r.get("title"),
                "content": r.get("content", "")[:400],
                "url": r.get("url"),
                "published_date": r.get("published_date"),
            }
            for r in response.get("results", [])
        ]
    except Exception as e:
        print(f"[fetcher] Tavily error: {e}")
        return []
