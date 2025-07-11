from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import asyncio
from datetime import datetime
import re

from settings import Config
from news_sources import DataAggregator

class PoliticsChatbotAgentic:
    """Agentic chatbot class for political queries with advanced reasoning and neutrality"""
    def __init__(self):
        api_key = Config.OPENAI_API_KEY if Config.OPENAI_API_KEY else None
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=api_key
        )
        self.data_aggregator = DataAggregator()

    async def chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if conversation_history is None:
            conversation_history = []
        try:
            # 1. LLM-based query classification (strict YES/NO)
            classification_prompt = f"""
            SYSTEM: You are an expert political assistant. Is the following user question about politics, government, public policy, or a public controversy involving a political figure? If the question could plausibly relate to politics, answer YES. Otherwise, answer NO.
            
            Examples:
            Q: Why did he feud with Elon Musk?\nA: YES
            Q: What are Taylor Swift's political views?\nA: YES
            Q: Who won the NBA finals?\nA: NO
            Q: What is the US immigration policy?\nA: YES
            Q: Tell me about the latest Marvel movie.\nA: NO
            USER: {message}
            """
            classification = self.llm.invoke([HumanMessage(content=classification_prompt)])
            classification_text = str(classification.content) if hasattr(classification, 'content') else str(classification)
            is_political = classification_text.strip().lower().startswith("yes")
            if not is_political:
                refusal_message = (
                    "I'm sorry, but I can only answer questions about politics, government, or public policy. "
                    "If you have a political question, please ask!"
                )
                return {
                    "response": refusal_message,
                    "is_political": False,
                    "confidence_score": 0,
                    "bias_analysis": {},
                    "citation_analysis": {},
                    "sources": "",
                    "timestamp": datetime.now().isoformat()
                }
            # 2. Retrieve up-to-date context from all APIs
            data = await self.data_aggregator.get_comprehensive_political_data(message)
            context = self._create_context_from_data(data)
            print("[DEBUG] Context for LLM prompt:\n", context)  # Debug print
            # 3. Build advanced prompt for neutrality, multi-perspective analysis, and self-reflection
            # Add last 4 turns of conversation history for context
            history_str = ""
            for turn in conversation_history[-4:]:
                user_msg = turn.get('message', '')
                assistant_msg = turn.get('response', '')
                history_str += f"USER: {user_msg}\n"
                history_str += f"ASSISTANT: {assistant_msg}\n"
            prompt = f"""
            SYSTEM: You are a political information assistant. You MUST use ONLY the CONTEXT below to answer the user's question.
            - Present both Republican and Democratic perspectives on the issue, if relevant.
            - Maintain a neutral, factual tone and do not express personal opinions.
            - Do not guess or use your own knowledge; only use the CONTEXT.
            - Do not include a 'Sources' section in your answer; sources will be appended automatically.
            - Do not answer any non-political questions, if you think a question has some political context then only answer.

            CONTEXT:
            {context}
            {history_str}
            USER: {message}
            """
            response = self.llm.invoke([HumanMessage(content=prompt)])
            response_content = str(response.content) if hasattr(response, 'content') else str(response)
            # 4. Self-reflection for bias/neutrality
            critique_prompt = (
                "Review your previous answer for bias or lack of neutrality. "
                "If any, revise to be more balanced. Otherwise, reply: 'No revision needed.'\n"
                f"Answer:\n{response_content}"
            )
            critique = self.llm.invoke([HumanMessage(content=critique_prompt)])
            critique_content = str(critique.content) if hasattr(critique, 'content') else str(critique)

            if critique_content.strip().lower().startswith("no revision needed"):
                llm_answer = response_content
            else:
                if critique_content.strip() == response_content.strip():
                    llm_answer = response_content
                elif critique_content.strip() and critique_content.strip() != response_content.strip():
                    llm_answer = f"{critique_content}\n\n[Original Answer:]\n{response_content}"
                else:
                    llm_answer = response_content
            # Remove any LLM-generated 'Sources' section
            llm_answer = re.sub(r"(?i)\n*Sources?:\n.*", "", llm_answer, flags=re.DOTALL)
            # 5. Append only important sources at the bottom
            sources_section = self._extract_sources(data, llm_answer)
            final_answer = f"{llm_answer}\n\nSources:\n{sources_section}"
            confidence_score = self.data_aggregator.calculate_confidence_score(data)
            return {
                "response": final_answer,
                "is_political": True,
                "confidence_score": confidence_score,
                "bias_analysis": critique_content,
                "citation_analysis": {},
                "sources": sources_section,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }

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
    def _create_context_from_data(self, data: Dict[str, Any]) -> str:
        context_parts = []
        if data.get('news_articles'):
            context_parts.append("Recent News Articles:")
            for article in data['news_articles'][:2]:
                title = article.get('title', 'No title')
                desc = article.get('description', '')
                context_parts.append(f"- {title}: {desc} ({article.get('source', {}).get('name', 'Unknown source')})")
        if data.get('guardian_articles'):
            context_parts.append("\nGuardian Articles:")
            for article in data['guardian_articles'][:2]:
                title = article.get('webTitle', 'No title')
                desc = article.get('fields', {}).get('trailText', '')
                context_parts.append(f"- {title}: {desc} (The Guardian)")
        if data.get('search_results'):
            context_parts.append("\nSearch Results:")
            for result in data['search_results'][:2]:
                title = result.get('title', 'No title')
                snippet = result.get('snippet', '')
                link = result.get('link', 'No link')
                context_parts.append(f"- {title}: {snippet} ({link})")
        if data.get('brave_results'):
            context_parts.append("\nBrave Search Results:")
            for result in data['brave_results'][:2]:
                title = result.get('title', 'No title')
                desc = result.get('description', '')
                url = result.get('url', 'No url')
                context_parts.append(f"- {title}: {desc} ({url})")
        if data.get('government_data'):
            context_parts.append("\nGovernment Data:")
            for item in data['government_data'][:1]:
                title = item.get('title', 'No title')
                desc = item.get('summary', '')
                context_parts.append(f"- {title}: {desc}")
        # Add scraped summaries from Wikipedia/White House
        if data.get('scraped_summaries'):
            context_parts.append("\nScraped Summaries (Wikipedia/White House):")
            for item in data['scraped_summaries']:
                url = item.get('url', '')
                summary = item.get('summary', '')
                context_parts.append(f"- {summary} (Source: {url})")
        return "\n".join(context_parts) if context_parts else "No specific data available"
    def _extract_sources(self, data: Dict[str, Any], answer: str) -> str:
        all_urls = set()
        for article in data.get('news_articles', []):
            url = article.get('url') or article.get('link')
            if url:
                all_urls.add(url)
        for result in data.get('search_results', []):
            url = result.get('link')
            if url:
                all_urls.add(url)
        for result in data.get('brave_results', []):
            url = result.get('url')
            if url:
                all_urls.add(url)
        for item in data.get('scraped_summaries', []):
            url = item.get('url')
            if url:
                all_urls.add(url)
        for item in data.get('government_data', []):
            url = item.get('url')
            if url:
                all_urls.add(url)
        # Only include URLs that are actually referenced in the answer
        important_urls = [url for url in all_urls if url and url in answer]
        return "\n".join(important_urls) if important_urls else "No important sources cited." 