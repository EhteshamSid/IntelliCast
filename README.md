# IntelliCast 2.0 — Advanced Agentic Political Chatbot

**Author: Ehtesham Siddiqui**

---

## Executive Summary
IntelliCast 2.0 is a production-quality, agentic political chatbot designed for advanced reasoning, strict neutrality, and real-time factuality. Built for the LLM Engineer Candidacy Project, it leverages OpenAI’s GPT-4, aggregates data from multiple APIs and authoritative sources, and enforces principled boundaries. Each session maintains its own persistent memory profile, enabling context-rich, multi-turn conversations with robust bias mitigation and multi-perspective analysis. The system is engineered for reliability, transparency, and compliance with best practices in political information delivery.

---

## Features

- **Strict Neutrality:** Enforces unbiased, factual answers with both Republican and Democratic perspectives where relevant.
- **Principled Boundaries:** Uses an LLM-based YES/NO classifier to strictly refuse non-political questions with a fixed message (no sources shown).
- **Real-Time Information Retrieval:** Aggregates up-to-date data from NewsAPI, The Guardian, Serper, Brave, Congress, FEC, and scrapes Wikipedia/White House for authoritative facts.
- **Multi-Perspective Analysis:** Always presents multiple viewpoints on partisan or controversial issues.
- **Session Memory:** Each chat session has its own persistent memory and conversation history, supporting context-rich, multi-turn interactions.
- **Advanced Prompt Engineering:** System prompt enforces neutrality, disables LLM-generated sources, and includes the last 4 turns of conversation for continuity.
- **Bias Mitigation:** After each answer, the LLM self-reflects for bias and revises if needed.
- **Citations & Confidence:** Only URLs actually referenced in the answer are cited at the bottom; every answer includes a confidence score.
- **Modern Web UI:** Responsive, ChatGPT-style interface with sidebar, chat bubbles, and persistent chat history.
- **API Integration:** Modular design makes it easy to add or swap data sources.

---

## Setup

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Create a `.env` file with your API keys:**
   ```
   OPENAI_API_KEY=your_openai_key_here
   NEWS_API_KEY=your_newsapi_key_here
   GUARDIAN_API_KEY=your_guardian_key_here
   BRAVE_API_KEY=your_brave_key_here
   CONGRESS_API_KEY=your_congress_key_here
   FEC_API_KEY=your_fec_key_here
   SERPER_API_KEY=your_serper_key_here
   BING_API_KEY=your_bing_key_here
   REUTERS_API_KEY=your_reuters_key_here
   ```
   > Only the keys you provide will be used. The more you add, the richer the answers.

3. **Run the chatbot (web UI):**
   ```
   python app.py
   ```
   Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Usage

### **Web Interface**
- Start a new chat, switch between sessions, or delete old ones from the sidebar.
- Ask any political, government, or public policy question — the bot will answer with both perspectives, sources, and a confidence score.
- The bot will strictly refuse non-political questions with a fixed message and no sources.
- Click "Summarize" to get a quick overview of any session.
- All your chats are saved and can be revisited anytime.

### **CLI (for advanced users)**
- You can also run the CLI version:
  ```
  python main.py
  ```
- Use `history` to see your conversation, `summary` for stats, and `quit` to exit.

---

## .env Example
```
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...
GUARDIAN_API_KEY=...
BRAVE_API_KEY=...
CONGRESS_API_KEY=...
FEC_API_KEY=...
SERPER_API_KEY=...
BING_API_KEY=...
REUTERS_API_KEY=...
```

---

## Project Structure
- `app.py` — Flask backend for the web UI
- `main.py` — CLI version (optional)
- `politics_bot.py` — Core agentic chatbot logic (neutrality, bias/citation checks, session memory)
- `news_sources.py` — API clients for news/search/government data
- `topic_classifier.py` — LLM-based classifier for political queries
- `settings.py` — Loads config and API keys
- `static/` — CSS and JS for the web UI
- `templates/` — HTML for the web UI

---

## Troubleshooting & Tips
- If you get "Invalid session" errors, try refreshing the page or starting a new chat.
- If answers seem limited, check your `.env` for missing or expired API keys.
- For best results, provide as many API keys as possible.
- The bot will politely refuse non-political questions (e.g., "What's the weather?").
- All code and UI are written and organized by me, Ehtesham Siddiqui.

---

## Personal Notes
This project is a showcase of advanced prompt engineering, agentic reasoning, API integration, and user-friendly AI tool design. If you have feedback or want to extend the bot with more sources or features, feel free to reach out! 