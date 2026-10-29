# Current requirements mapping

| Requirement | Implementation |
| --- | --- |
| Welcome page before main app | Top-level connection gate in `app.py` |
| Masked API key | Password input inside a clearing form |
| Check key before access | Authenticated OpenAI model lookup in `src/auth.py` |
| Invalid key keeps app locked | Safe failure messages; no connected state set |
| Session-specific credentials | Explicit key propagation to assessment, streaming and voice |
| Sign out | Clear key, history and widget state; attempt session cache deletion |
| Improved UI | Teal/navy palettes, split welcome screen, branded sidebar, hero, cards, numbered sections |
| Direct Streamlit deployment | `requirements.txt`, `.streamlit/config.toml`, deployment guide; Python 3.12 |
| Patient information and symptoms | Required form widgets + Pydantic validation |
| ChatOpenAI + LLMChain | `src/chains.py` and `langchain-classic` |
| PromptTemplate / ChatPromptTemplate | `src/prompts.py` |
| Explicit System / Human / AI messages | `message_demo()` and result expander |
| Six-key structured JSON | Exact Pydantic schema, fenced/prose JSON parsing |
| Live model streaming | `.stream()` → `st.write_stream()` |
| Both cache implementations | Session-owned InMemoryCache and SQLiteCache |
| Medical disclaimers and urgency colours | Welcome page, sidebar, tabs, results and reports |
| Session history | Last 20 records; open/delete controls |
| PDF export | Unicode font + shaping, generated in memory |
| Multiple languages | English, Urdu, Arabic, Spanish, French, German |
| Dark/light toggle | Login and workspace toggle |
| Voice input | Consent → record → transcribe → editable text → submit |
| Analytics | Session urgency metrics and chart |

The original assignment PDF remains unchanged as reference material. The latest user request supersedes its original deployment bonus. Hosted SQLite and session history are not durable medical-record storage, and metadata access does not guarantee generation or transcription access.
