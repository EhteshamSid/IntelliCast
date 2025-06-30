import re
from typing import List, Dict, Any
import os
import openai
from dotenv import load_dotenv
import requests
import time
import logging
import wikipedia
import concurrent.futures

load_dotenv()

# --- Error Handling Helper ---
class RateLimitException(Exception):
    pass

def try_api_call(api_func, query, max_retries=2, backoff_factor=2):
    """Attempts an API call with retries and exponential backoff on rate limit."""
    delay = 1
    for attempt in range(max_retries + 1):
        try:
            result = api_func(query)
            if result:
                return result
        except RateLimitException as e:
            logging.warning(f"{api_func.__name__} rate limited: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor
        except Exception as e:
            logging.error(f"{api_func.__name__} failed: {e}")
            break
    return None

# --- News APIs ---
def fetch_from_newsapi(query):
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        logging.error("NEWSAPI_KEY not set.")
        return None
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"NewsAPI request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return [
            {
                "title": a["title"],
                "url": a["url"],
                "source": a["source"]["name"],
                "publishedAt": a["publishedAt"],
                "content": a.get("content", "")
            }
            for a in data.get("articles", [])
        ]
    elif resp.status_code == 429:
        raise RateLimitException("NewsAPI rate limit hit.")
    else:
        logging.error(f"NewsAPI error: {resp.status_code} {resp.text}")
    return None

def fetch_from_guardian(query):
    api_key = os.getenv("GUARDIAN_API_KEY")
    if not api_key:
        logging.error("GUARDIAN_API_KEY not set.")
        return None
    url = f"https://content.guardianapis.com/search?q={query}&api-key={api_key}&show-fields=all&page-size=5"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"Guardian API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return [
            {
                "title": r['webTitle'],
                "url": r['webUrl'],
                "source": "The Guardian",
                "publishedAt": r['webPublicationDate'],
                "content": r['fields'].get('bodyText', '') if 'fields' in r else ''
            }
            for r in data.get('response', {}).get('results', [])
        ]
    elif resp.status_code == 429:
        raise RateLimitException("Guardian API rate limit hit.")
    else:
        logging.error(f"Guardian API error: {resp.status_code} {resp.text}")
    return None

def fetch_from_serper(query):
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        logging.error("SERPER_API_KEY not set.")
        return None
    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"q": query}, timeout=5)
    except Exception as e:
        logging.error(f"Serper API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return [
            {
                "title": n["title"],
                "url": n["link"],
                "source": n.get("source", ""),
                "publishedAt": n.get("date", ""),
                "content": n.get("snippet", "")
            }
            for n in data.get("news", [])
        ]
    elif resp.status_code == 429:
        raise RateLimitException("Serper API rate limit hit.")
    else:
        logging.error(f"Serper API error: {resp.status_code} {resp.text}")
    return None

def fetch_from_brave(query):
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        logging.error("BRAVE_API_KEY not set.")
        return None
    url = f"https://api.search.brave.com/res/v1/news/search?q={query}&count=5"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except Exception as e:
        logging.error(f"Brave API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return [
            {
                "title": n["title"],
                "url": n["url"],
                "source": n.get("publisher", {}).get("name", ""),
                "publishedAt": n.get("publishedAt", ""),
                "content": n.get("description", "")
            }
            for n in data.get("results", [])
        ]
    elif resp.status_code == 429:
        raise RateLimitException("Brave API rate limit hit.")
    else:
        logging.error(f"Brave API error: {resp.status_code} {resp.text}")
    return None

def fetch_from_wikipedia(query):
    try:
        results = wikipedia.search(query)
        if not results:
            # print("Wikipedia: No results found.")
            return None
        page = wikipedia.page(results[0])
        summary = wikipedia.summary(results[0], sentences=2)
        # print("Wikipedia page found:", page.title)
        # print("Wikipedia summary:", summary)
        return [{
            "title": page.title,
            "url": page.url,
            "source": "Wikipedia",
            "publishedAt": "",
            "content": summary
        }]
    except Exception as e:
        logging.error(f"Wikipedia API error: {e}")
        return None

def fetch_news_articles(query: str):
    articles = []
    api_funcs = [fetch_from_newsapi, fetch_from_guardian, fetch_from_serper, fetch_from_brave]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(try_api_call, api_func, query) for api_func in api_funcs]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                articles.extend(result)
    # Always try Wikipedia as a final fallback if no articles found
    if not articles:
        wiki_result = try_api_call(fetch_from_wikipedia, query)
        if wiki_result:
            articles.extend(wiki_result)
    if not articles:
        logging.error(f"All news APIs failed for query: {query}")
    return articles

# --- Government APIs ---
def fetch_from_congress_gov(query):
    api_key = os.getenv("CONGRESS_API_KEY")
    if not api_key:
        logging.error("CONGRESS_API_KEY not set.")
        return None
    url = f"https://api.congress.gov/v3/bill?query={query}&api_key={api_key}"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"Congress.gov API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return data.get("bills", [])
    elif resp.status_code == 429:
        raise RateLimitException("Congress.gov API rate limit hit.")
    else:
        logging.error(f"Congress.gov API error: {resp.status_code} {resp.text}")
    return None

def fetch_from_govinfo(query):
    api_key = os.getenv("GOVINFO_API_KEY")
    if not api_key:
        logging.error("GOVINFO_API_KEY not set.")
        return None
    url = f"https://api.govinfo.gov/collections/BILLS/{query}?api_key={api_key}"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"GovInfo API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return data.get("packages", [])
    elif resp.status_code == 429:
        raise RateLimitException("GovInfo API rate limit hit.")
    else:
        logging.error(f"GovInfo API error: {resp.status_code} {resp.text}")
    return None

def fetch_from_fec(query):
    api_key = os.getenv("FEC_API_KEY")
    if not api_key:
        logging.error("FEC_API_KEY not set.")
        return None
    url = f"https://api.open.fec.gov/v1/search/?api_key={api_key}&query={query}"
    try:
        resp = requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"FEC API request failed: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return data.get("results", [])
    elif resp.status_code == 429:
        raise RateLimitException("FEC API rate limit hit.")
    else:
        logging.error(f"FEC API error: {resp.status_code} {resp.text}")
    return None

def fetch_legislation_data(query: str):
    for api_func in [fetch_from_congress_gov, fetch_from_govinfo, fetch_from_fec]:
        result = try_api_call(api_func, query)
        if result:
            return result
    logging.error(f"All government APIs failed for query: {query}")
    return []

# --- Classification ---
def is_political_question(question: str) -> bool:
    """
    Heuristic to determine if a question is political.
    Returns True if political, False otherwise.
    """
    political_keywords = [
        'election', 'congress', 'senate', 'house', 'president', 'republican', 'democrat',
        'policy', 'government', 'law', 'bill', 'politics', 'campaign', 'vote', 'voting',
        'supreme court', 'governor', 'mayor', 'legislation', 'political', 'partisan',
        'white house', 'administration', 'federal', 'state', 'local government',
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in political_keywords)

def is_partisan_topic(question: str) -> bool:
    """
    Returns True if the question is about a partisan issue or debate, based on keywords.
    """
    partisan_keywords = [
        'immigration', 'abortion', 'gun control', 'tax', 'healthcare', 'climate', 'minimum wage',
        'lgbt', 'transgender', 'border', 'race', 'affirmative action', 'voting rights',
        'police', 'crime', 'education', 'student loan', 'welfare', 'social security',
        'medicare', 'medicaid', 'environment', 'energy', 'foreign policy', 'israel',
        'ukraine', 'china', 'trade', 'tariff', 'military', 'defense', 'war', 'peace',
        'republican', 'democrat', 'bipartisan', 'partisan', 'conservative', 'liberal',
        'progressive', 'right-wing', 'left-wing', 'supreme court', 'court decision',
        'election', 'campaign', 'ballot', 'primary', 'senate race', 'house race',
        'presidential race', 'presidential debate', 'political debate', 'policy debate',
        'controversy', 'scandal', 'investigation', 'indictment', 'impeachment',
    ]
    q = question.lower()
    return any(k in q for k in partisan_keywords)

# --- Response Synthesis ---
def synthesize_response(question: str, articles: List[Dict[str, Any]], legislation: List[Dict[str, Any]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[Error: OPENAI_API_KEY environment variable not set. Please set your OpenAI API key.]"

    # System prompt for neutrality, citation, and multi-perspective analysis
    system_prompt = (
        "You are a political events AI assistant. Your job is to answer only questions about political events. "
        "For every answer:\n"
        "- Use only verifiable facts from reputable sources (news APIs, government data, etc.).\n"
        "- Provide proper citations (with URLs) for every factual claim.\n"
        "- On partisan issues, always present both Republican and Democratic viewpoints, clearly separated and neutrally worded.\n"
        "- Explicitly check for and correct any partisan language or framing.\n"
        "- If you cannot maintain strict neutrality or provide citations for every claim, politely refuse to answer.\n"
        "- If a question is not about political events, politely refuse and explain your scope.\n"
        "- Never make up facts or hallucinate information. If you cannot verify something, say so.\n"
        "- For legislative, election, or court questions, include dates, vote counts, and official statements where possible.\n"
        "- Always maintain strict neutrality and avoid partisan framing.\n"
        "- If you are unsure about neutrality or citation, state your uncertainty and ask for clarification."
    )

    # Prepare context for the model (include articles/legislation as context if available)
    # print("Articles passed to LLM:", articles)
    context = ""
    if articles:
        context += "Relevant news articles:\n"
        for art in articles[:3]:
            context += f"- {art.get('title', '')} ({art.get('source', '')}, {art.get('publishedAt', '')}): {art.get('url', '')}\n"
            context += f"  Summary: {art.get('content', '')}\n"
    if legislation:
        context += "Relevant legislative data:\n"
        for leg in legislation[:3]:
            context += f"- {leg.get('title', '')} ({leg.get('date', '')}): {leg.get('url', '')}\n"
    if context:
        context += "\nUse the above sources for your answer.\n"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context + question}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        content = response.choices[0].message.content
        if content:
            return content.strip()
        else:
            return "[OpenAI API returned no content in the response.]"
    except Exception as e:
        return f"[OpenAI API error: {e}]"

# --- Post-processing for Neutrality, Citations, and Perspective ---
def detect_partisan_language(response: str) -> bool:
    # Focus on truly partisan or inflammatory language only
    partisan_keywords = [
        r"\b(radical left|far[- ]?left|far[- ]?right|extremist|MAGA|woke|Trumpist|Bidenomics|partisan attack|partisan agenda|leftist|rightist|ultra-conservative|ultra-liberal|socialist agenda|fascist|communist|RINO|snowflake|libtard|fake news|enemy of the people|traitor|un-American|patriot act|witch hunt|deep state|cancel culture|culture war|gaslighting|dog whistle|race-baiting|fearmongering|hate speech|incitement|authoritarian|totalitarian|dictatorship|coup|insurrection|sedition|treason)\b",
        r"\b(slam|attack|vilify|condemn|denounce|smear campaign|scapegoat|demonize|weaponize|fearmonger|race-bait|gaslight|dog-whistle)\b"
    ]
    for pattern in partisan_keywords:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    return False

def check_citations(response: str) -> bool:
    # Require at least one URL per paragraph or claim
    url_pattern = r"https?://[\w\.-/]+"
    paragraphs = [p for p in response.split('\n') if p.strip()]
    for p in paragraphs:
        if any(word in p.lower() for word in ["according to", "reports", "states", "says", "claims", "announced", "ruled", "decided", "voted", "passed", "signed"]):
            if not re.search(url_pattern, p):
                return False
    return True

def check_perspective_balance(response: str) -> bool:
    # Look for both "Republican" and "Democrat" (or synonyms) in the response
    rep_keywords = ["Republican", "GOP", "conservative", "right-wing"]
    dem_keywords = ["Democrat", "liberal", "left-wing", "progressive"]
    rep_found = any(k.lower() in response.lower() for k in rep_keywords)
    dem_found = any(k.lower() in response.lower() for k in dem_keywords)
    return rep_found and dem_found

def flag_unverified_claims(response: str) -> list:
    # Return sentences that make claims but lack a URL
    url_pattern = r"https?://[\w\.-/]+"
    sentences = re.split(r'[.!?]\s+', response)
    flagged = []
    for s in sentences:
        if any(word in s.lower() for word in ["according to", "reports", "states", "says", "claims", "announced", "ruled", "decided", "voted", "passed", "signed"]):
            if not re.search(url_pattern, s):
                flagged.append(s.strip())
    return flagged

def inline_flag_unverified_claims(response: str) -> str:
    # Highlight sentences that make claims but lack a URL
    url_pattern = r"https?://[\w\.-/]+"
    sentences = re.split(r'([.!?]\s+)', response)  # Keep punctuation as separate tokens
    flagged = []
    rebuilt = ""
    for i in range(0, len(sentences), 2):
        s = sentences[i]
        punct = sentences[i+1] if i+1 < len(sentences) else ""
        if any(word in s.lower() for word in ["according to", "reports", "states", "says", "claims", "announced", "ruled", "decided", "voted", "passed", "signed"]):
            if not re.search(url_pattern, s):
                rebuilt += f"[UNCITED CLAIM: {s.strip()}]{punct}"
                continue
        rebuilt += s + punct
    return rebuilt

def regenerate_with_citations(question: str, articles: list, legislation: list, api_key: str) -> str:
    """
    Ask the LLM to regenerate the answer, requiring citations for every factual claim.
    """
    system_prompt = (
        "You are a political events AI assistant. Your job is to answer only questions about political events. "
        "For every answer:\n"
        "- Use only verifiable facts from reputable sources (news APIs, government data, etc.).\n"
        "- Provide proper citations (with URLs) for every factual claim.\n"
        "- Do NOT include any factual claim without a citation.\n"
        "- On partisan issues, always present both Republican and Democratic viewpoints, clearly separated and neutrally worded.\n"
        "- Explicitly check for and correct any partisan language or framing.\n"
        "- If you cannot maintain strict neutrality or provide citations for every claim, politely refuse to answer.\n"
        "- If a question is not about political events, politely refuse and explain your scope.\n"
        "- Never make up facts or hallucinate information. If you cannot verify something, say so.\n"
        "- For legislative, election, or court questions, include dates, vote counts, and official statements where possible.\n"
        "- Always maintain strict neutrality and avoid partisan framing.\n"
        "- If you are unsure about neutrality or citation, state your uncertainty and ask for clarification."
    )
    context = ""
    if articles:
        context += "Relevant news articles:\n"
        for art in articles[:3]:
            context += f"- {art.get('title', '')} ({art.get('source', '')}, {art.get('publishedAt', '')}): {art.get('url', '')}\n"
            context += f"  Summary: {art.get('content', '')}\n"
    if legislation:
        context += "Relevant legislative data:\n"
        for leg in legislation[:3]:
            context += f"- {leg.get('title', '')} ({leg.get('date', '')}): {leg.get('url', '')}\n"
    if context:
        context += "\nUse the above sources for your answer.\n"
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context + question + "\n\nRegenerate your answer, ensuring every factual claim is followed by a proper citation (URL). Do not include any claim without a citation."}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        content = response.choices[0].message.content
        if content:
            return content.strip()
        else:
            return "[OpenAI API returned no content in the regenerated response.]"
    except Exception as e:
        return f"[OpenAI API error during regeneration: {e}]"

# --- Secondary LLM Review ---
def secondary_llm_review(response: str, api_key: str) -> str:
    """
    Use the LLM to review the response for neutrality, perspective balance, and citation compliance.
    Returns the review result or suggested corrections.
    """
    review_prompt = (
        "Review the following answer for strict political neutrality, balanced Republican and Democratic perspectives, and proper citations for every factual claim. "
        "If the answer is neutral, balanced, and fully cited, reply ONLY with 'PASS'. "
        "If not, explain the issues and suggest corrections.\n\n"
        f"Answer to review:\n{response}"
    )
    try:
        client = openai.OpenAI(api_key=api_key)
        review = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a political AI quality assurance reviewer."},
                {"role": "user", "content": review_prompt}
            ],
            temperature=0.0,
            max_tokens=400,
        )
        review_content = review.choices[0].message.content
        if review_content is not None:
            return review_content.strip()
        else:
            return "[Review LLM error: No content returned.]"
    except Exception as e:
        return f"[Review LLM error: {e}]"

# Stub for confidence scoring and fact cross-referencing
def score_fact_confidence(articles: list, response: str) -> dict:
    """
    Placeholder for future implementation: Cross-reference facts in the response with articles,
    and assign a confidence score based on agreement and source credibility.
    """
    # To be implemented: parse facts, check agreement, score credibility
    return {}

# --- Main Chatbot Logic ---
def chatbot_response(user_input: str) -> str:
    if not is_political_question(user_input):
        return "I'm sorry, I can only answer questions about political events."
    # Fetch data from APIs
    articles = fetch_news_articles(user_input)
    legislation = fetch_legislation_data(user_input)
    # Synthesize response
    response = synthesize_response(user_input, articles, legislation)
    api_key = os.getenv("OPENAI_API_KEY")
    warning = None
    # Only run partisan language check for partisan topics
    if is_partisan_topic(user_input):
        if detect_partisan_language(response):
            warning = "[Warning: The generated response may contain partisan language. Please rephrase your question or consult multiple sources.]\n"
    # If no reputable sources found at all, return a clear message
    if not articles and not legislation:
        return "[No reputable sources or citations were found for your query. Please provide more context or check official legislative records.]"
    # Citation check and regeneration
    if not check_citations(response):
        if api_key:
            regenerated = regenerate_with_citations(user_input, articles, legislation, api_key)
            if is_partisan_topic(user_input):
                if detect_partisan_language(regenerated):
                    warning = "[Warning: The regenerated response may contain partisan language. Please rephrase your question or consult multiple sources.]\n"
            if not check_citations(regenerated):
                # Show answer with inline warnings for uncited claims
                inline = inline_flag_unverified_claims(regenerated)
                return (warning or "") + inline
            if is_partisan_topic(user_input):
                if not check_perspective_balance(regenerated):
                    return (warning or "") + "[Warning: The regenerated response may not present both Republican and Democratic perspectives. Please seek additional viewpoints.]"
            unverified = flag_unverified_claims(regenerated)
            if unverified:
                inline = inline_flag_unverified_claims(regenerated)
                return (warning or "") + inline
            # Secondary LLM review step for regenerated answer
            review_result = secondary_llm_review(regenerated, api_key)
            if review_result != "PASS":
                return (warning or "") + f"[LLM Review Warning or Correction]:\n{review_result}"
            return (warning or "") + regenerated
        else:
            inline = inline_flag_unverified_claims(response)
            return (warning or "") + inline
    if is_partisan_topic(user_input):
        if not check_perspective_balance(response):
            return (warning or "") + "[Warning: The response may not present both Republican and Democratic perspectives. Please seek additional viewpoints.]"
    unverified = flag_unverified_claims(response)
    if unverified:
        inline = inline_flag_unverified_claims(response)
        return (warning or "") + inline
    # Secondary LLM review step
    if api_key:
        review_result = secondary_llm_review(response, api_key)
        if review_result != "PASS":
            return (warning or "") + f"[LLM Review Warning or Correction]:\n{review_result}"
    return (warning or "") + response

# --- CLI for Testing (to be replaced by Gradio UI) ---
def main():
    print("Welcome to the Political AI Chatbot! Ask me any question about political events.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        response = chatbot_response(user_input)
        print(response)

if __name__ == "__main__":
    main()