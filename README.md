# Political Events AI Assistant

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

A specialized chatbot that answers questions about political events with strict neutrality, balanced perspectives, and zero hallucinations.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation & Configuration](#installation--configuration)
5. [Usage](#usage)
6. [Architecture & Flow](#architecture--flow)
7. [Core Modules](#core-modules)
8. [Prompts & Neutrality Enforcement](#prompts--neutrality-enforcement)
9. [Extensibility](#extensibility)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Political Events AI Assistant** is a chatbot designed to fetch, verify, and cite political information from multiple sources, ensuring:

* **Strict Neutrality**: Presents both Republican and Democratic perspectives.
* **Citation Enforcement**: Every factual claim includes a source URL.
* **Zero Hallucinations**: Only verifiable facts are returned.

## Features

* **Multi-Source Integration**: NewsAPI, The Guardian, Serper, Brave Search, Wikipedia fallback.
* **Government Data Access**: Congress.gov, GovInfo, FEC APIs.
* **Web Scraping Fallback**: Reuters, AP News, BBC, NYTimes, Al Jazeera.
* **Scope Control**: Classifies and rejects non-political queries.
* **Bias Prevention**: Detects and flags partisan language.
* **Error Handling**: Retries with exponential backoff on rate limits.

## Prerequisites

* Python 3.8+
* OpenAI account with GPT-4 access
* API keys for:

  * NewsAPI
  * Guardian API
  * Serper (Google)
  * Brave Search
  * Congress.gov
  * GovInfo
  * FEC
* Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

## Installation & Configuration

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/political-events-ai.git
   cd political-events-ai
   ```
2. **Environment Variables**: Create a `.env` in the project root with:

   ```ini
   OPENAI_API_KEY=sk-...
   NEWSAPI_KEY=...
   GUARDIAN_API_KEY=...
   SERPER_API_KEY=...
   BRAVE_API_KEY=...
   CONGRESS_API_KEY=...
   GOVINFO_API_KEY=...
   FEC_API_KEY=...
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Launch the Streamlit UI:

```bash
streamlit run main.py
```

* Enter your query in the text box.
* Click **Response** to get the answer with citations.

## Architecture & Flow

1. **Input Classification**

   * `is_officeholder_question`: Shortcut for officeholder lookups.
   * `is_political_question`: Ensures only political queries are handled.

2. **Data Fetching**

   * Concurrent calls to news APIs with retries (`try_api_call`).
   * Wikipedia fallback if no news results.
   * Government data via Congress.gov, GovInfo, FEC.
   * Web scraping fallback for major outlets.

3. **Filtering**

   * `filter_us_articles`: Limits results to U.S. politics unless another country is specified.
   * Year extraction and filtering (`extract_target_year`).

4. **Response Synthesis**

   * `synthesize_response`: Constructs a system prompt enforcing neutrality and citations, then calls OpenAI.

5. **Post-Processing & QA**

   * Detects partisan language.
   * Ensures citations for all trigger-word claims.
   * Inline flags and regeneration if citations are missing.
   * Optional secondary LLM review for quality assurance.

## Core Modules

* `fetchers.py` — API fetch functions for news & government.
* `scrapers.py` — Web-scraping logic for fallback headlines.
* `classifiers.py` — Query classification and intent checks.
* `synthesizer.py` — Response generation and citation enforcement.
* `reviewer.py` — Bias detection, citation checks, secondary review.
* `main.py` — Streamlit UI orchestration.

## Prompts & Neutrality Enforcement

* **System Prompt**: Rules for neutrality, citation, and multi-perspective output.
* **Citation Prompt**: Strict regeneration prompt that forbids uncited claims.
* **Bias Detection**: Regex-based filters for partisan or inflammatory language.

## Extensibility

* **Add Sources**: Extend the `api_funcs` list or add new scraper functions.
* **Multi-Language**: Integrate translation or multilingual Wikipedia fallback.
* **Custom UI**: Swap Streamlit for Gradio or a full-stack interface.

## Troubleshooting

* **API Key Errors**: Verify `.env` keys and `load_dotenv()`.
* **Rate Limits**: Check logs for `429`, adjust `try_api_call` backoff.
* **Timeouts**: Increase request timeouts or optimize network.
* **Scraper Breakages**: Update selectors to match updated site HTML.
