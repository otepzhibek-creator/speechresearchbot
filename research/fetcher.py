import requests
import xml.etree.ElementTree as ET


def fetch_arxiv_papers(max_results: int = 15) -> list[dict]:
    """Fetch latest papers from arxiv in NLP/Speech categories."""
    query = "cat:cs.CL+OR+cat:cs.SD+OR+cat:eess.AS"
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending"
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
    """Fetch trending speech/NLP models from HuggingFace Hub."""
    results = []
    for filter_tag in ("speech", "text-generation", "automatic-speech-recognition"):
        try:
            response = requests.get(
                "https://huggingface.co/api/models",
                params={"sort": "trending", "limit": limit // 2, "filter": filter_tag},
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
            print(f"[fetcher] HuggingFace ({filter_tag}) error: {e}")
    # deduplicate by id
    seen = set()
    unique = []
    for m in results:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)
    return unique[:limit]


def fetch_web_news(api_key: str, limit: int = 10) -> list[dict]:
    """Fetch recent Speech/NLP/AI product news via Tavily."""
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
