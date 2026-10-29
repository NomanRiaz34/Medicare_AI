# Verification record — Streamlit edition

Date: 29 October 2026. Environment: Linux, CPython 3.12. Runtime dependency versions are in `requirements.txt`; `VERIFIED_ENVIRONMENT.txt` records the local environment for reference.

## Automated tests

Command: `python -m pytest tests -q --disable-warnings`

Result: **68 passed**. Fictional keys and patient inputs are used; no paid OpenAI calls are made.

Coverage includes:

- Strict patient-input validation, empty symptoms, exact JSON schema, fenced/prose JSON extraction, braces inside strings and corrupt responses.
- Explicit emergency signs, local chest-pain-plus-breathlessness guidance, urgency floor and removal of reassuring emergency output.
- Both LangChain cache backends, repeated requests, namespace isolation, clearing, SQLite reopen and session-only disk cleanup.
- Prompt templates, System/Human/AI message roles, real ChatOpenAI/LLMChain client construction without network calls, streaming chunks and partial stream failure.
- Six-language PDF generation, voice input size/key checks and fake transcription behavior.
- Real SDK model-lookup contract through a mocked OpenAI client; authentication/permission/not-found/rate/connection/server failures mapped to authored messages without exposing provider error bodies or keys.
- Locked initial screen even if an environment owner-key exists, masked input, consent, rejected key, successful connection, reruns without repeated validation, logout, per-session cache identity and session-key propagation into assessment/narration.

Expected deprecation/test-runtime warnings remain; they do not indicate test failures.

## Browser checks and visual inspection

A local Chromium browser exercised the application through an external test-only harness with mocked OpenAI key verification and fictional assessment/narrative results. The harness is **not** included in the project. Production `app.py` has no demonstration login bypass.

Checks passed for the masked initial gate, connecting, light/dark switching, fictional assessment results, PDF download control, sign-out, narrow welcome-page layout and horizontal-overflow check at 390 pixels. Desktop welcome/workspace/result samples, both theme samples, and the narrow login form were visually inspected. A header overlap and dark-theme link/section styling issues found during inspection were corrected.

This verifies the tested browser flows and sample layouts. It does not establish clinical correctness, linguistic quality, or accessibility conformance.

## Still requires a real account/deployment

- Successful verification with a real OpenAI key and the account's configured model permissions.
- Real assessment generation, billing/quota behavior, clinical content and language quality.
- Hardware microphone permission and live transcription.
- Actual Streamlit Community Cloud publication and hosting-account configuration.
- Real-patient suitability, clinical validation and applicable privacy/regulatory review.

Use `DEMO_CHECKLIST.md` and `STREAMLIT_DEPLOYMENT.md` to complete these live checks. The package has been prepared for deployment; it has not been published to your account.
