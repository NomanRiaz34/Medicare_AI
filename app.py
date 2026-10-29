"""MediGuide AI: run with `streamlit run app.py`. All state is browser-session scoped."""
from collections import Counter
from datetime import datetime, timezone
import secrets
import uuid
import streamlit as st
from pydantic import ValidationError
from langchain_core.globals import set_llm_cache
from src.config import (DEFAULT_MODEL, DATA_DIR, LANGUAGES, SYMPTOMS,
                        DURATIONS, GENDERS, DISCLAIMER, EMERGENCY_TEXT)
from src.models import PatientInput, Assessment
from src.cache_manager import CacheManager
from src.chains import assess, stream_narrative, message_demo
from src.safety import RED_FLAGS, minimum_urgency
from src.utils import InvalidAssessment
from src.reports import create_report
from src.voice import transcribe_audio
from src.auth import validate_api_key, KeyValidationError, disconnect_session
from src.ui import apply_theme, brand, login_story, home_hero, section, empty_history

st.set_page_config(page_title="MediGuide AI", page_icon="✚", layout="wide")

@st.cache_resource
def initialize_cache_policy():
    # Register ONCE; individual models receive their own session-owned cache objects.
    # Never switch a process-global cache when a different browser user changes modes.
    set_llm_cache(None)
    return True

initialize_cache_policy()

# This gate runs BEFORE the assessment UI or patient state is rendered.
# Do not use an environment key as a fallback; every visitor connects their own key.
if not st.session_state.get("connected", False):
    apply_theme(st.session_state.get("dark_mode", False))
    top_left, top_right = st.columns([6, 1])
    with top_right:
        st.toggle("Dark mode", key="dark_mode")
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        login_story()
    with right:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        with st.form("connect_form", clear_on_submit=True):
            st.markdown("### Welcome to MediGuide")
            st.caption("Connect your own OpenAI API key to open your workspace.")
            entered_key = st.text_input("OpenAI API key", type="password", key="key_entry",
                placeholder="sk-...", max_chars=512,
                help="Sent over your connection to this app server, then used to contact OpenAI. Never enter a key in a public or untrusted app.")
            accepted = st.checkbox("I understand my key is used by this app server to contact OpenAI, and API usage is billed to my account.", key="key_consent")
            login = st.form_submit_button("Verify key & continue", type="primary", use_container_width=True)
            st.caption("Your key stays in server memory for this browser session. It is not written to files, a shared cache, or a URL by this app.")
        if login:
            if not accepted:
                st.warning("Please acknowledge how your API key will be used.")
            else:
                try:
                    with st.spinner("Checking your key with OpenAI..."):
                        verified = validate_api_key(entered_key, DEFAULT_MODEL)
                    # Only retain credentials AFTER a successful authenticated lookup.
                    st.session_state.session_api_key = entered_key.strip()
                    st.session_state.verified_model = verified.model
                    st.session_state.connected = True
                    st.rerun()
                except KeyValidationError as error:
                    st.error(str(error))
                except Exception:
                    st.error("The connection check could not be completed. Please try again. No key has been saved.")
        st.info("A successful check confirms key authentication and model metadata access. Billing quota, generation and transcription permissions are checked when those features are used.")
        st.link_button("Get an OpenAI API key ↗", "https://platform.openai.com/api-keys", use_container_width=True)
    st.divider()
    st.warning(DISCLAIMER)
    st.caption("This is an API-key connection screen, not a patient-account login. If you may be having an emergency, contact local emergency services immediately without signing in.")
    st.stop()

# Hidden login widgets are dropped immediately after a successful connection.
for key in ("key_entry", "key_consent"):
    st.session_state.pop(key, None)
api_key = st.session_state.session_api_key
for key, default in {"history": [], "selected_id": None, "other_symptoms": "",
                     "session_token": secrets.token_urlsafe(32), "raw_error": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    brand()
    st.markdown('<div class="mg-session">● &nbsp; Connected to OpenAI<small>Your key · your browser session</small></div>', unsafe_allow_html=True)
    if st.button("Sign out", key="sign_out", use_container_width=True):
        disconnect_session(st.session_state)
        st.rerun()
    st.toggle("Dark mode", key="dark_mode")
    st.divider()
    st.subheader("Personalize your guidance")
    language = st.selectbox("Answer language", LANGUAGES)
    narrative_enabled = st.toggle("Live explanation", value=True,
        help="A separate model call adds cost, even on an assessment cache hit.")
    with st.expander("Model & caching"):
        model = st.text_input("OpenAI chat model", value=st.session_state.verified_model,
            help="This model must support JSON mode and temperature=0. Only the sign-in model's metadata access was checked.")
        cache_mode = st.selectbox("Assessment cache", ["Off", "Memory", "SQLite"])
        sqlite_consent = True
        if cache_mode == "SQLite":
            sqlite_consent = st.checkbox("Allow unencrypted health data in a session-specific cache on the app server")
            st.caption("On Community Cloud, local storage is temporary. This is not a patient database or a private file on your computer. Sign-out attempts to delete this session's cache.")
        namespace = st.session_state.session_token
        if "cache_manager" not in st.session_state:
            st.session_state.cache_manager = CacheManager(DATA_DIR, namespace)
        manager = st.session_state.cache_manager
        if st.button("Clear selected cache", use_container_width=True):
            if cache_mode == "SQLite" and sqlite_consent:
                manager.get("SQLite")
            manager.clear()
            st.success("Current cache entries cleared.")
    with st.expander("Session controls"):
        st.caption("Your last 20 assessments stay in this browser session. A new session may lose them.")
        if st.button("Delete session history", use_container_width=True):
            st.session_state.history = []
            st.session_state.selected_id = None
            st.session_state.raw_error = None
            st.rerun()
    st.divider()
    st.warning(DISCLAIMER)
    st.caption("Educational prototype · Consult a professional")

apply_theme(st.session_state.get("dark_mode", False))
home_hero()
st.warning(DISCLAIMER)
st.caption("Privacy first: leave out names, addresses and identity numbers. Submitted health information is sent to OpenAI only with your consent.")

assessment_tab, history_tab, analytics_tab, about_tab = st.tabs(
    ["Symptom assessment", "Session history", "Analytics", "How it works"])

with assessment_tab:
    section("01", "Start with a safety check")
    st.caption("If these signs are happening now, get emergency help immediately. This checklist is not exhaustive.")
    flags = st.multiselect("Current emergency warning signs", RED_FLAGS)
    if flags:
        st.error(EMERGENCY_TEXT[language])
    with st.expander("Describe symptoms by voice"):
        audio_consent = st.checkbox("I agree to send this recording to OpenAI for transcription")
        audio = st.audio_input("Record a short symptom description")
        if st.button("Transcribe recording", disabled=audio is None):
            if not audio_consent:
                st.warning("Agree to audio processing before transcription.")
            else:
                try:
                    with st.spinner("Transcribing your recording..."):
                        transcript = transcribe_audio(audio.getvalue(), api_key)
                    st.session_state.other_symptoms = transcript
                    st.success("Transcript added below. Review and correct it before submitting.")
                except Exception:
                    st.error("Transcription failed. Check your key, model access and connection, or type your symptoms.")
        st.caption("Recordings are not written to disk by this app. Transcription can mishear words; always review it.")
    with st.form("intake"):
        section("02", "Tell us what you are experiencing")
        left, right = st.columns(2)
        with left:
            age = st.text_input("Patient age in whole years", placeholder="For example: 25", max_chars=3)
            symptoms = st.multiselect("Symptoms", SYMPTOMS)
            duration = st.selectbox("Duration of symptoms", DURATIONS)
        with right:
            gender = st.selectbox("Gender", GENDERS)
            severity = st.slider("Overall symptom severity", 1, 10, 3,
                                  help="1 = mild; 10 = most severe. Not a clinical pain scale.")
            st.caption("For infants, use age 0 and specify age in months in notes. "
                       "This prototype is not validated for children or pregnancy.")
        other = st.text_area("Other symptoms / reviewed voice transcript", key="other_symptoms", max_chars=2000)
        left, right = st.columns(2)
        with left:
            conditions = st.text_area("Existing medical conditions", max_chars=2000)
        with right:
            medications = st.text_area("Current medications", max_chars=2000)
        st.divider()
        notes = st.text_area("Additional notes (include relevant context)", max_chars=2000)
        consent = st.checkbox("I understand the limitations and agree to send this information to OpenAI for educational guidance")
        submitted = st.form_submit_button("Assess symptoms", type="primary", use_container_width=True)
    if submitted:
        # Hide any old result so a failed new submission cannot look like a fresh assessment.
        st.session_state.selected_id = None
        st.session_state.raw_error = None
        try:
            if not age.strip().isascii() or not age.strip().isdigit():
                raise ValueError("Enter a whole-number age from 0 to 120.")
            patient = PatientInput(age=int(age.strip()), gender=gender, symptoms=symptoms,
                other_symptoms=other, duration=duration, severity=severity,
                existing_conditions=conditions, medications=medications, notes=notes,
                language=language, red_flags=flags)
            is_emergency = minimum_urgency(patient) == "EMERGENCY"
            if not is_emergency and not consent:
                raise ValueError("Please acknowledge the data-processing and educational-use notice.")
            if not is_emergency and cache_mode == "SQLite" and not sqlite_consent:
                raise ValueError("Consent to local SQLite storage or choose Off / Memory caching.")
            with st.spinner("Preparing safety-focused guidance..."):
                cache = False if is_emergency else manager.get(cache_mode)
                result, meta = assess(patient, api_key, model, cache)
            record = {"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "patient": patient.model_dump(), "assessment": result.model_dump(),
                      "metadata": meta, "model": model, "narrative": None}
            st.session_state.history = ([record] + st.session_state.history)[:20]
            st.session_state.selected_id = record["id"]
        except InvalidAssessment as error:
            st.error(str(error))
            st.session_state.raw_error = error.raw
        except (ValueError, ValidationError) as error:
            st.warning(str(error))
        except Exception:
            # Never show provider exceptions, headers, API credentials or raw prompts.
            st.error("The assessment service is unavailable. Check your API key, model access, quota and connection. "
                     "Consult a healthcare professional rather than relying on this app.")
    if st.session_state.raw_error:
        with st.expander("Unvalidated response - debugging only; not medical guidance"):
            st.code(st.session_state.raw_error, language="text")

    current = next((r for r in st.session_state.history if r["id"] == st.session_state.selected_id), None)
    if current:
        result = Assessment.model_validate(current["assessment"])
        st.divider()
        section("03", "Your guidance dashboard")
        st.warning(DISCLAIMER)
        a, b, c = st.columns(3)
        a.metric("Suggested urgency", result.urgency_level)
        b.metric("Assessment time", f'{current["metadata"]["seconds"]:.2f} s')
        c.metric("Assessment source", current["metadata"]["source"])
        display = {"LOW": st.success, "MEDIUM": st.info, "HIGH": st.warning, "EMERGENCY": st.error}
        display[result.urgency_level]("Suggested urgency: " + result.urgency_level +
            ". AI guidance may be wrong; seek professional advice if you are concerned.")
        if result.urgency_level == "EMERGENCY":
            st.error(EMERGENCY_TEXT[current["patient"]["language"]])
        if result.urgency_level == "HIGH":
            st.warning("Arrange urgent assessment by a healthcare professional. If symptoms are severe or worsening, seek emergency help.")
        st.write(result.summary)
        one, two = st.columns(2)
        with one:
            st.subheader("Recommended next steps")
            for item in result.recommended_next_steps:
                st.write("• " + item)
            st.subheader("Questions for your doctor")
            for item in result.questions_for_doctor:
                st.write("• " + item)
        with two:
            st.subheader("Warning signs")
            for item in result.warning_signs:
                st.write("• " + item)
            with st.expander("Educational possibilities - not a diagnosis"):
                for item in result.possible_conditions:
                    st.write(item.name + ": " + item.reason)
                if not result.possible_conditions:
                    st.write("No condition suggestions are needed for this safety alert.")
        if narrative_enabled and result.urgency_level != "EMERGENCY":
            with st.expander("Live explanation - supplemental AI text", expanded=True):
                st.caption("This generated explanation may contain errors. Follow the structured guidance and consult a professional.")
                if current["narrative"] is None:
                    chunks = []
                    def tracked_stream():
                        for chunk in stream_narrative(api_key, current["model"], result, current["patient"]["language"]):
                            chunks.append(chunk)
                            yield chunk
                    try:
                        st.write_stream(tracked_stream())
                        current["narrative"] = "".join(chunks)
                    except Exception:
                        # Keep structured assessment available even if a stream fails halfway.
                        current["narrative"] = "Explanation unavailable. Use the structured guidance above."
                        st.info(current["narrative"])
                else:
                    st.write(current["narrative"])
        try:
            st.download_button("Download guidance as PDF", create_report(current),
                file_name="MediGuide_Guidance.pdf", mime="application/pdf")
        except Exception:
            st.info("PDF export is unavailable. Check font and PDF dependencies in the README.")
        with st.expander("Validated JSON and message roles (course demonstration)"):
            st.json(result.model_dump())
            messages = message_demo(PatientInput.model_validate(current["patient"]), result)
            st.write(" → ".join(type(message).__name__ for message in messages))
        st.caption("Record created: " + current["created_at"] + " (UTC)")

with history_tab:
    st.subheader("Your session history")
    st.warning(DISCLAIMER)
    st.caption("Up to 20 assessments in this browser session; includes repeat submissions. "
               "History is not durable patient storage and is not shared with other browser sessions.")
    if not st.session_state.history:
        empty_history()
    for record in st.session_state.history:
        with st.expander(record["created_at"] + " · " + record["assessment"]["urgency_level"]):
            st.write(record["assessment"]["summary"])
            if st.button("Open assessment", key=record["id"]):
                st.session_state.selected_id = record["id"]
                st.rerun()
            st.caption("Open the Symptom assessment tab to view the selected dashboard.")

with analytics_tab:
    st.subheader("Session urgency distribution")
    st.warning(DISCLAIMER)
    st.caption("Descriptive counts of AI outputs in this session, including repeat submissions. "
               "Not diagnostic performance, population health statistics, or clinical evidence.")
    counts = Counter(r["assessment"]["urgency_level"] for r in st.session_state.history)
    cols = st.columns(4)
    for col, level in zip(cols, ["LOW", "MEDIUM", "HIGH", "EMERGENCY"]):
        col.metric(level, counts[level])
    if counts:
        st.bar_chart({"Assessments": {level: counts[level] for level in ["LOW", "MEDIUM", "HIGH", "EMERGENCY"]}})
    else:
        st.info("Complete an assessment to see your session distribution.")

with about_tab:
    st.subheader("How MediGuide AI works")
    st.warning(DISCLAIMER)
    st.write("Validated intake → local emergency check → LangChain assessment → strict JSON validation "
             "→ urgency safeguard → structured dashboard → optional live explanation and PDF export.")
    st.write("The local check uses the current warning-sign checklist and selected symptoms. "
             "It cannot reliably understand all free text, negation, languages, or emergency situations. "
             "It is not a clinically validated triage system. No screen can rule out a serious illness.")
    st.write("Six answer languages: English, Urdu, Arabic, Spanish, French and German. "
             "The navigation is English. Translation quality requires human review.")
    st.write("Assessment caching can be off, session memory, or a session-specific SQLite file on the app server. "
             "Cloud files are temporary; persistence is not guaranteed. Live explanation and transcription are separate uncached API calls.")
    st.write("Includes session history, PDF reports, six answer languages, dark/light mode, "
             "voice input and session analytics. Deployment is configured for Streamlit Community Cloud.")
    st.caption("Educational assignment implementation. Real patient use needs clinical validation, "
               "secure deployment, access controls, retention rules and applicable regulatory review.")

st.markdown('<div class="mg-foot">MediGuide AI · Educational guidance, thoughtfully presented.<br>Always consult a qualified healthcare professional.</div>', unsafe_allow_html=True)
