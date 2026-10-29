# MediGuide AI — Streamlit Edition

An educational symptom-guidance application with a verified API-key welcome screen, a redesigned Streamlit workspace, voice input, multilingual guidance, PDF reports, history and session analytics.

**Educational AI only. Not a doctor, diagnosis, treatment or emergency service. Consult a qualified healthcare professional. For a possible emergency, contact local emergency services immediately without using or signing in to this app.**

## What changed in this edition

- A masked OpenAI API-key entry screen now appears first. The assessment dashboard is not rendered until the key has passed an authenticated check.
- Invalid, revoked, restricted or unreachable keys receive friendly error messages; provider error bodies and credentials are not displayed.
- Each visitor brings their own key. Assessment, narration and transcription use that session's key, with no shared owner-key fallback.
- Sign-out clears the key, patient intake, history, widget state and session cache references; it attempts to delete that session's SQLite files.
- Welcome screen, typography, teal/navy palettes, cards, sidebar, numbered form sections and history empty state have been refreshed.
- Deployment targets Streamlit Community Cloud directly. Container configuration has been removed as requested.
- Existing assessment, JSON parsing, caching, streaming, voice, PDF, six answer languages, session history and analytics remain.

## Quick local setup (Windows)

Use Python **3.12**. Extract the ZIP and open a terminal inside the folder containing `app.py`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell activation is restricted, you can use `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m streamlit run app.py` without changing execution policies.

For macOS/Linux, activate with `source .venv/bin/activate` instead. Then open the local URL printed by Streamlit, enter your own API key, acknowledge how it is used, and select **Verify key & continue**.

No `.env` file or shared API-key secret is required. `.env.example` contains optional, non-secret model/storage settings only. An existing `OPENAI_API_KEY` environment variable does not unlock the welcome screen or supply the assessment key.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository and upload the **contents** of `mediguide_ai` to its root, so `app.py`, `requirements.txt`, `src`, `assets` and `.streamlit` are at the top level.
2. Keep `.env`, `.streamlit/secrets.toml`, `.data`, virtual environments and local reports out of Git. Ignore rules are included.
3. Sign in at https://share.streamlit.io and create an app using the repository and branch.
4. Set the main file path to **`app.py`**. If you uploaded the outer folder instead of its contents, use **`mediguide_ai/app.py`**.
5. In Advanced settings, choose **Python 3.12**, matching the tested environment.
6. Deploy. Streamlit installs `requirements.txt` automatically.
7. Visit your `streamlit.app` URL. It should show the API-key welcome screen. Each visitor enters their own key.

**Do not add an owner's OpenAI API key to Cloud secrets for this edition.** It is not needed and the UI intentionally does not use it as a fallback.

The default model is `gpt-4o-mini`. If you need another model, update `DEFAULT_MODEL`'s fallback in `src/config.py` before deployment or configure `OPENAI_MODEL` as an environment setting. Use a model compatible with JSON mode and `temperature=0`; model access differs by account. The sidebar model setting applies after connection; only the welcome-screen model's metadata access is checked during sign-in.

There is no mandatory system package installation: the Unicode PDF font is bundled and HarfBuzz shaping is supplied by a Python dependency. If dependency installation fails, inspect the Cloud build logs and confirm Python 3.12 and the supplied requirements file.

See `docs/STREAMLIT_DEPLOYMENT.md` for the deployment checklist and troubleshooting.

## How key verification works

`src/auth.py` calls `OpenAI(...).models.retrieve(DEFAULT_MODEL)` using the submitted key. This makes an actual authenticated model metadata request, rather than accepting an `sk-` prefix as proof of validity. No chat-generation request is made during this check.

A successful check confirms authentication and metadata access for that model. It **does not** guarantee generation billing quota, JSON-mode support, or transcription permissions. Those requests can still fail later; the application handles them separately. A restricted key without permission for the model metadata endpoint may be rejected even if it has some other API permissions.

This is a **bring-your-own-key connection gate**, not a patient identity system, username/password account, OAuth flow, or medical-record access-control system. Sessions are browser/WebSocket scoped; a refresh/reconnection may require signing in again. Ordinary widget reruns do not revalidate the key or call the welcome-screen API check again.

### Key handling

- Input is a password widget, and the login form clears on submission.
- The successful key is kept in the session's server-side memory. It is never put into a URL, cookie, patient prompt, PDF, shared Streamlit resource cache or disk file by this app.
- Validation, assessment and transcription explicitly use `https://api.openai.com/v1`; an alternate API base URL from the environment is not used for visitor keys.
- Keys are sent from the browser to the server hosting this app, then used to contact OpenAI. Only enter a key into a deployment and app operator you trust; server-side code necessarily has access to it during the session.
- Keys are not displayed in the sidebar. Sign out when finished. Revoking a key at OpenAI is separate from signing out here.
- No raw provider exception is displayed on connection failure. The app does not claim control over hosting infrastructure logs or OpenAI's data retention.

## Architecture

| File | Purpose |
| --- | --- |
| `app.py` | Connection gate, sidebar, form, dashboard, session history and analytics |
| `src/auth.py` | Authenticated key check, safe error mapping and session disconnection |
| `src/ui.py` | Theme styles and source-authored visual components |
| `src/config.py` | Non-secret settings, languages, choices and safety messages |
| `src/models.py` | Validated patient input and exact six-key response schema |
| `src/prompts.py` | PromptTemplate, ChatPromptTemplate and safety instructions |
| `src/chains.py` | ChatOpenAI, assignment-required LLMChain, streaming and message roles |
| `src/cache_manager.py` | Isolated memory/SQLite caches, real cache-hit reporting and cleanup |
| `src/voice.py` | Transcribe audio using the session key; review before submission |
| `src/reports.py` | In-memory Unicode PDF generation |
| `src/utils.py` | Safe JSON extraction and validation errors |
| `src/safety.py` | Limited local emergency safeguards and urgency floor |

## Features retained from the assignment

The intake collects age, gender, selected/free-text symptoms, duration, severity, existing conditions, current medications, notes and answer language. Age and other inputs are validated before an assessment request. JSON mode plus Pydantic validates the exact output structure:

```json
{
  "summary": "...",
  "possible_conditions": [{"name": "...", "reason": "..."}],
  "urgency_level": "LOW",
  "recommended_next_steps": ["..."],
  "questions_for_doctor": ["..."],
  "warning_signs": ["..."]
}
```

Metadata and intake stay outside that six-key object. Urgency is LOW, MEDIUM, HIGH or EMERGENCY. Generated text values can be English, Urdu, Arabic, Spanish, French or German; schema keys and enum values remain English. Navigation labels remain English.

The structured dashboard is shown before optional model narration. Narration uses `.stream()` and `st.write_stream()`, is labelled supplemental AI text, and is a separate model call. PDF export includes validated structured guidance rather than unvalidated narration.

The deprecated `LLMChain` is intentionally retained through `langchain-classic` for the original assignment rubric. The System/Human/AI message demonstration remains in the result expander. The original assignment PDF is retained as source documentation; the latest user instruction overrides its container-deployment bonus.

## Caching, history and cloud storage

| Mode | Storage | Notes |
| --- | --- | --- |
| Off | No new assessment cache entries | Prior cached entries are not automatically erased |
| Memory | Session-owned RAM cache | Does not survive a new app process/session |
| SQLite | Session-specific file on the app server | Explicit consent; unencrypted; cloud persistence not guaranteed |

The global LangChain default is initialized once; each visitor receives their own explicit cache object and random namespace. There is no reusable cross-session cache phrase in this hosted edition. API keys are not cache namespaces and are not part of the patient prompt. Both cache backends are demonstrated and tested.

On Community Cloud, SQLite is on the **app server**, not the visitor's computer, and is not a durable medical-record database. Prefer Off or Memory. Sign-out attempts to clear and remove this session's files, but an abrupt disconnect, process crash or hosting permissions may leave files until the host recycles them. Neither secure disk erasure nor durable persistence is promised. Use fictional data for demonstrations.

Session history keeps up to 20 assessments. Analytics describe those session records, including repeats; they are not clinical performance metrics. Deleting history does not delete cache entries. Clearing cache does not delete history. Sign-out clears both at the application level and attempts cache-file cleanup.

Repeated identical assessments can hit the chosen cache, but live narration and audio transcription are separate uncached API calls. Turn off **Live explanation** when demonstrating assessment-cache speed. Model, language, prompt and intake changes can produce a cache miss.

## Safety and limitations

- Disclaimers stay visible on the welcome page, main workspace, sidebar, results, other tabs and reports.
- For explicit current warning signs or selected chest pain plus shortness of breath, the connected workspace gives immediate local guidance without an assessment model call. The sign-in page also tells users never to wait for AI in an emergency.
- The local safeguard is not a clinically validated triage algorithm. It cannot reliably understand every emergency, negation or non-English free-text description.
- Possible conditions are educational possibilities, not confirmed diagnoses. The prompt forbids prescriptions and medicine dosages, but schema validation cannot establish clinical correctness.
- Text processing and audio processing have separate consent steps. Voice transcripts must be reviewed before submission.
- Cloud hosting and the key gate do not make this suitable for real patient use. Clinical validation, secure deployment decisions and applicable privacy review remain necessary.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Tests use fictional data and mock OpenAI responses; they do not need a real key or make paid calls. Coverage includes the welcome-screen gate, rejected-key behavior, consent, reruns, sign-out, session-key propagation, provider errors, session isolation, parsing, caches, emergency path, voice behavior, streaming and PDFs.

See `docs/TEST_RESULTS.md` for what was actually verified and the remaining live checks. `docs/VERIFIED_ENVIRONMENT.txt` records the local test environment as information, not an alternative Cloud dependency file.

## Useful official references

- Deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Dependency placement: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- Authenticated model lookup: https://developers.openai.com/api/reference/resources/models/methods/retrieve
