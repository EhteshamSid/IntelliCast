# IntelliCast 2.O — Political Events Chatbot

**Author: Ehtesham Siddiqui**

A modern, personal project for answering political questions with strict neutrality, real citations, and multi-perspective analysis. This chatbot is designed to help users get balanced, up-to-date information about U.S. political events, policies, and debates — all with a clean, simple web interface and persistent chat history.

---

## Features

- **Balanced Answers:** Always presents both Republican and Democratic viewpoints on partisan issues.
- **Strict Neutrality:** Refuses non-political requests and avoids partisan framing.
- **Citations & Confidence:** Every answer includes sources and a confidence score.
- **Bias Detection:** Warns if a response may be biased or missing citations.
- **Multi-Session Chat:** Start, switch, and delete chat sessions. Each session has its own history and summary.
- **Persistent History:** All chats are saved, so you never lose your conversations.
- **Modern Web UI:** Responsive, ChatGPT-like interface with sidebar, chat bubbles, and a personal footer.
- **API Integration:** Pulls data from OpenAI, NewsAPI, The Guardian, Brave Search, and Congress.gov (with more sources easy to add).

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
- Ask any political question — the bot will answer with both perspectives, sources, and a confidence score.
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
- `politics_bot.py` — Core chatbot logic (neutrality, bias/citation checks)
- `news_sources.py` — API clients for news/search/government data
- `topic_classifier.py` — Classifies if queries are political
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
This project is a showcase of my skills in prompt engineering, API integration, and building user-friendly AI tools. If you have feedback or want to extend the bot with more sources or features, feel free to reach out! 
