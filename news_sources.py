import requests
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from settings import Config
import json
from bs4 import BeautifulSoup

def fetch_first_paragraph(url):
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Wikipedia: first <p> after the infobox
        if 'wikipedia.org' in url:
            paragraphs = soup.select('div.mw-parser-output > p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    return text
        # White House: first <p>
        elif 'whitehouse.gov' in url:
            p = soup.find('p')
            if p:
                return p.get_text(strip=True)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return ""

class NewsAPIClient:
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_political_news(self, query: str, days_back: int = 7) -> List[Dict]:
        """Get political news from NewsAPI"""
        if not self.api_key:
            return []
            
        params = {
            'q': f"{query} AND (politics OR government OR election OR congress OR senate)",
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 20,
            'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/everything", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])
            return []

class GuardianAPIClient:
    def __init__(self):
        self.api_key = Config.GUARDIAN_API_KEY
        self.base_url = "https://content.guardianapis.com/search"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_political_news(self, query: str, days_back: int = 7) -> List[Dict]:
        if not self.api_key:
            return []
        params = {
            'q': f"{query} politics government election",
            'api-key': self.api_key,
            'section': 'politics',
            'from-date': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
            'show-fields': 'headline,trailText,byline,webPublicationDate,bodyText',
            'page-size': 20
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', {}).get('results', [])
            return []

class SerperSearchClient:
    def __init__(self):
        self.api_key = Config.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_political_info(self, query: str) -> List[Dict]:
        """Search for political information using Serper API"""
        if not self.api_key:
            return []
            
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': f"{query} politics government election",
            'num': 10,
            'gl': 'us',
            'hl': 'en'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get('organic', [])
            return []

class BraveSearchClient:
    def __init__(self):
        self.api_key = Config.BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_political_info(self, query: str) -> List[Dict]:
        if not self.api_key:
            return []
        headers = {
            'Accept': 'application/json',
            'X-Subscription-Token': self.api_key
        }
        params = {
            'q': f"{query} politics government election",
            'count': 10,
            'safesearch': 'strict',
            'country': 'us',
            'freshness': 'Day'
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('web', {}).get('results', [])
            return []

class GovernmentAPIClient:
    def __init__(self):
        self.congress_api_key = Config.CONGRESS_API_KEY
        self.fec_api_key = Config.FEC_API_KEY
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_congress_data(self, query: str) -> List[Dict]:
        """Get data from Congress.gov API"""
        if not self.congress_api_key:
            return []
            
        params = {
            'api_key': self.congress_api_key,
            'query': query,
            'format': 'json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.congress.gov/v3/bills", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('bills', [])
            return []

class FECAPIClient:
    def __init__(self):
        self.api_key = Config.FEC_API_KEY
        self.base_url = "https://api.open.fec.gov/v1/"
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_fec_data(self, query: str) -> List[Dict]:
        if not self.api_key:
            return []
        params = {
            'api_key': self.api_key,
            'q': query,
            'per_page': 10
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}search/", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []

class WebScraper:
    """Fallback web scraper for political news sources"""
    
    @staticmethod
    async def scrape_political_news(query: str) -> List[Dict]:
        """Scrape political news from trusted sources"""
        # This is a simplified version - in production you'd want more robust scraping
        sources = Config.POLITICAL_NEWS_SOURCES[:3]  # Limit to top 3 sources
        results = []
        
        for source in sources:
            try:
                # Simple search simulation - in production use proper scraping
                result = {
                    'title': f"Political news about {query}",
                    'url': f"https://{source}/search?q={query}",
                    'source': source,
                    'description': f"Latest political information about {query}",
                    'publishedAt': datetime.now().isoformat()
                }
                results.append(result)
            except Exception as e:
                print(f"Error scraping {source}: {e}")
                continue
                
        return results

class DataAggregator:
    """Aggregates data from multiple sources asynchronously"""
    def __init__(self):
        self.news_client = NewsAPIClient()
        self.guardian_client = GuardianAPIClient()
        self.search_client = SerperSearchClient()
        self.brave_client = BraveSearchClient()
        self.gov_client = GovernmentAPIClient()
        self.fec_client = FECAPIClient()  # Add FEC client if not present
        self.scraper = WebScraper()
    async def get_comprehensive_political_data(self, query: str) -> Dict[str, Any]:
        tasks = [
            self.news_client.get_political_news(query),
            self.guardian_client.get_political_news(query),
            self.search_client.search_political_info(query),
            self.brave_client.search_political_info(query),
            self.gov_client.get_congress_data(query),
            self.fec_client.get_fec_data(query),
            self.scraper.scrape_political_news(query)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        news_articles = results[0] if not isinstance(results[0], Exception) else []
        guardian_articles = results[1] if not isinstance(results[1], Exception) else []
        search_results = results[2] if not isinstance(results[2], Exception) else []
        brave_results = results[3] if not isinstance(results[3], Exception) else []
        government_data = results[4] if not isinstance(results[4], Exception) else []
        fec_data = results[5] if not isinstance(results[5], Exception) else []
        scraped_data = results[6] if not isinstance(results[6], Exception) else []

        data = {
            'news_articles': news_articles,
            'guardian_articles': guardian_articles,
            'search_results': search_results,
            'brave_results': brave_results,
            'government_data': government_data,
            'fec_data': fec_data,
        }
        # Ensure search_results and brave_results are lists, not exceptions
        search_results = search_results if isinstance(search_results, list) else []
        brave_results = brave_results if isinstance(brave_results, list) else []
        # Scrape Wikipedia/White House links for up-to-date info
        scraped_summaries = []
        for result in search_results + brave_results:
            link = result.get('link') or result.get('url')
            if link and ("wikipedia.org" in link or "whitehouse.gov" in link):
                summary = fetch_first_paragraph(link)
                if summary:
                    scraped_summaries.append({'url': link, 'summary': summary})
        data['scraped_summaries'] = scraped_summaries
        return data
    
    def calculate_confidence_score(self, data: Dict[str, Any]) -> int:
        """Calculate confidence score based on data quality and source reliability"""
        score = 0
        
        # Multiple sources
        if len(data.get('news_articles', [])) > 0:
            score += Config.CONFIDENCE_CRITERIA['multiple_reputable_sources']
        
        # Government sources
        if len(data.get('government_data', [])) > 0:
            score += Config.CONFIDENCE_CRITERIA['government_official_source']
        
        # Cross-verification
        if len(data.get('search_results', [])) > 0:
            score += Config.CONFIDENCE_CRITERIA['cross_verified']
        
        # Recent information
        if data.get('timestamp'):
            score += Config.CONFIDENCE_CRITERIA['recent_information']
        
        return min(score, 10)  # Cap at 10 