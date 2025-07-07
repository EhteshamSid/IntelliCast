import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4-turbo-preview"
    
    # News APIs
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
    REUTERS_API_KEY = os.getenv("REUTERS_API_KEY")
    
    # Search APIs
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    BING_API_KEY = os.getenv("BING_API_KEY")
    
    # Government APIs
    CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")
    FEC_API_KEY = os.getenv("FEC_API_KEY")
    
    # Political News Sources (for web scraping fallback)
    POLITICAL_NEWS_SOURCES = [
        "reuters.com",
        "apnews.com", 
        "npr.org",
        "bbc.com/news",
        "cnn.com",
        "foxnews.com",
        "msnbc.com",
        "politico.com",
        "thehill.com",
        "rollcall.com"
    ]
    
    # Government Data Sources
    GOVERNMENT_SOURCES = [
        "congress.gov",
        "fec.gov",
        "govinfo.gov",
        "senate.gov",
        "house.gov",
        "whitehouse.gov"
    ]
    
    # System Prompts
    SYSTEM_PROMPT = """You are a political information assistant. Your role is to provide accurate, balanced, and well-cited information about political events and issues in the United States.

CRITICAL RULES:
1. ONLY answer questions about political events, policies, elections, and government activities
2. ALWAYS present both Republican and Democratic perspectives on partisan issues
3. REFUSE to answer non-political questions politely but firmly
4. CITE sources for every factual claim
5. Maintain strict political neutrality
6. Verify information across multiple reputable sources
7. Express confidence levels based on source reliability and consensus

When presenting partisan issues, structure your response as:
- Republican perspective: [viewpoint with citations]
- Democratic perspective: [viewpoint with citations]
- Neutral analysis: [balanced assessment]

For non-political requests, respond: "I'm designed to help with political information and current events. I cannot assist with [topic]. Please ask me about political events, policies, elections, or government activities."

Always end responses with a confidence score (1-10) and list your primary sources."""

    # Bias Detection Keywords
    BIAS_KEYWORDS = {
        "partisan": ["radical", "extreme", "far-left", "far-right", "radical left", "radical right"],
        "emotional": ["outrageous", "shocking", "terrible", "amazing", "incredible"],
        "absolute": ["always", "never", "everyone", "nobody", "completely", "totally"]
    }
    
    # Confidence Scoring Criteria
    CONFIDENCE_CRITERIA = {
        "multiple_reputable_sources": 3,
        "government_official_source": 2,
        "recent_information": 1,
        "cross_verified": 2,
        "official_documentation": 2
    }
    
    # Rate Limiting
    API_RATE_LIMITS = {
        "news_api": 1000,  # requests per day
        "openai": 5000,    # requests per minute
        "serper": 100,     # requests per day
        "brave": 100       # requests per day
    } 