# Engineering review — Streamlit edition

This revision implements the latest request: a verified API-key welcome screen before the main application, a visual refresh and direct Streamlit Community Cloud deployment.

## Connection architecture

The gate executes before patient widgets or history initialization. An authenticated `models.retrieve` request validates the submitted key and metadata access for the configured model. Only success writes the key to session memory and reruns into the workspace. Prefix checks alone never unlock the app. Successful metadata lookup does not prove generation quota, billing eligibility or transcription access.

The key is deliberately not loaded from a shared environment fallback. It is passed explicitly to each assessment, narrative and transcription call, and official API destinations are fixed. Credentials are not sent to an environment-overridden third-party API endpoint. Patient input, API keys and model output are never interpolated into the source-authored unsafe HTML components.

Sign-out attempts session-cache deletion and clears all session state even if disk cleanup fails. This is a connection gate, not verified patient identity or multi-user medical-record authorization. Browser refreshes or server restarts may create a new session.

## UI structure

A split welcome screen introduces the workflow beside a masked key form. The connected workspace uses a branded sidebar, connection status without key disclosure, a hero panel, themed metrics, numbered assessment sections, history empty state and tabbed results. The app's built-in dark/light toggle styles the major surfaces and controls; embedded third-party components can still use their native theme.

The assessment core remains modular: typed input, local emergency safeguard, versioned prompt, LLMChain, ChatOpenAI, strict JSON parsing, urgency floor, dashboard, optional narration and PDF export. LLMChain is retained for rubric compatibility despite deprecation.

## Hosting and storage

The canonical deployment dependency file is `requirements.txt`; tests use `requirements-dev.txt`. Python 3.12 is the target. The bundled font supports PDF text shaping without additional container infrastructure. Optional model settings can be configured in source or environment; a shared owner key is not required.

Memory/SQLite caches are explicitly session-owned. Hosted SQLite requires storage consent and uses a random per-session namespace, with no cross-session private phrase. Local cloud storage is ephemeral and unencrypted. The app does not promise clinical storage, encrypted databases, durable records, or guaranteed secure erasure. History and analytics are bounded browser-session state.

## Verification and remaining limits

Automated tests check the connection gate, safe provider errors, key propagation, reruns, logout, session isolation and the existing assessment features using fake API responses. No real key was supplied, so account-specific authentication, quota, model outputs and speech recognition still need live verification. This remains an educational prototype, not a clinically validated patient service.
