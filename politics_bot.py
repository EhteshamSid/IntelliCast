from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import SecretStr
import asyncio
import json
from datetime import datetime

from settings import Config
from news_sources import DataAggregator
from topic_classifier import PoliticalClassifier, BiasDetector, CitationChecker

class PoliticsChatbotSimple:
    """Main chatbot class - handles political queries with balanced responses"""
    
    def __init__(self):
        # Set up OpenAI client with proper API key handling
        api_key = SecretStr(Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
        
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,  # Low temp for consistent responses
            api_key=api_key
        )
        
        # Initialize our helper classes
        self.data_aggregator = DataAggregator()
        self.political_classifier = PoliticalClassifier()
        self.bias_detector = BiasDetector()
        self.citation_checker = CitationChecker()
    
    async def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Main chat method - processes user input and returns response"""
        if conversation_history is None:
            conversation_history = []
        
        try:
            # First, figure out if this is actually a political question
            is_political, confidence, reasoning = self.political_classifier.classify_query(message)
            
            # If it's not political or we're not confident, politely decline
            if not is_political or confidence < 0.3:
                rejection_message = f"I'm designed to help with political information and current events. I cannot assist with this topic. {reasoning}\n\nPlease ask me about political events, policies, elections, or government activities."
                
                return {
                    "response": rejection_message,
                    "is_political": False,
                    "confidence_score": 0,
                    "bias_analysis": {},
                    "citation_analysis": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            # Gather relevant data from various sources
            data = await self.data_aggregator.get_comprehensive_political_data(message)
            confidence_score = self.data_aggregator.calculate_confidence_score(data)
            
            # Build context from the gathered data
            context = self._create_context_from_data(data)
            
            # Prepare the prompt for the LLM
            messages = [
                SystemMessage(content=Config.SYSTEM_PROMPT),
                HumanMessage(content=f"Query: {message}\n\nContext: {context}\n\nPlease provide a balanced, well-cited response.")
            ]
            
            # Get response from the language model
            response = self.llm.invoke(messages)
            
            # Extract the response content (handle different response formats)
            if hasattr(response, 'content'):
                response_content = str(response.content)
            elif hasattr(response, 'text'):
                response_content = str(response.text)
            else:
                response_content = str(response)
            
            # Analyze the response for bias and citations
            bias_analysis = self.bias_detector.detect_bias(response_content)
            citation_analysis = self.citation_checker.check_citations(response_content)
            
            # Add sources and confidence info to the final response
            sources = self._extract_sources(data)
            final_response = f"{response_content}\n\nConfidence Score: {confidence_score}/10\n\nSources: {sources}"
            
            return {
                "response": final_response,
                "is_political": True,
                "confidence_score": confidence_score,
                "bias_analysis": bias_analysis,
                "citation_analysis": citation_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Handle any errors gracefully
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_context_from_data(self, data: Dict[str, Any]) -> str:
        """Build context string from the gathered data sources"""
        context_parts = []
        
        # Add recent news articles
        if data.get('news_articles'):
            context_parts.append("Recent News Articles:")
            for article in data['news_articles'][:2]:
                context_parts.append(f"- {article.get('title', 'No title')} ({article.get('source', {}).get('name', 'Unknown source')})")
        
        # Add Guardian articles
        if data.get('guardian_articles'):
            context_parts.append("\nGuardian Articles:")
            for article in data['guardian_articles'][:2]:
                context_parts.append(f"- {article.get('webTitle', 'No title')} (The Guardian)")
        
        # Add search results
        if data.get('search_results'):
            context_parts.append("\nSearch Results:")
            for result in data['search_results'][:2]:
                context_parts.append(f"- {result.get('title', 'No title')} ({result.get('link', 'No link')})")
        
        # Add Brave results
        if data.get('brave_results'):
            context_parts.append("\nBrave Search Results:")
            for result in data['brave_results'][:2]:
                context_parts.append(f"- {result.get('title', 'No title')} ({result.get('url', 'No url')})")
        
        # Add government data if available
        if data.get('government_data'):
            context_parts.append("\nGovernment Data:")
            for item in data['government_data'][:1]:
                context_parts.append(f"- {item.get('title', 'No title')}")
        
        return "\n".join(context_parts) if context_parts else "No specific data available"
    
    def _extract_sources(self, data: Dict[str, Any]) -> str:
        """Extract and format source information from the data"""
        sources = []
        
        # Get news sources
        for article in data.get('news_articles', [])[:2]:
            source_name = article.get('source', {}).get('name', 'Unknown')
            sources.append(source_name)
        
        # Guardian
        if data.get('guardian_articles'):
            sources.append('The Guardian')
        
        # Get search result sources
        for result in data.get('search_results', [])[:1]:
            link = result.get('link', '')
            if link:
                domain = link.split('/')[2] if len(link.split('/')) > 2 else link
                sources.append(domain)
        
        # Brave
        for result in data.get('brave_results', [])[:1]:
            url = result.get('url', '')
            if url:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                sources.append(domain)
        
        # Add government sources
        if data.get('government_data'):
            sources.append("Congress.gov")
        
        return ", ".join(set(sources)) if sources else "Multiple sources"
    
    def get_conversation_summary(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of the conversation statistics"""
        political_queries = sum(1 for msg in conversation_history if msg.get("is_political", False))
        total_queries = len(conversation_history)
        
        return {
            "total_queries": total_queries,
            "political_queries": political_queries,
            "non_political_queries": total_queries - political_queries,
            "political_percentage": (political_queries / total_queries * 100) if total_queries > 0 else 0
        } 