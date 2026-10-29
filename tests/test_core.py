import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_classic.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.models import PatientInput, Assessment
from src.utils import parse_assessment, InvalidAssessment
from src.safety import minimum_urgency, enforce_floor, RED_FLAGS
from src.cache_manager import CacheManager
from src.chains import assess, message_demo
from src.prompts import ASSESSMENT_CHAT_TEMPLATE, PATIENT_TEMPLATE
from src.reports import create_report
from src.config import LANGUAGES

@pytest.fixture
def patient():
    return PatientInput(age=25, gender="Prefer not to say", symptoms=["Runny nose", "Sore throat"],
                        duration="1-3 days", severity=2)

@pytest.fixture
def valid():
    return dict(summary="Mild symptoms; this is educational guidance, not a diagnosis.",
                possible_conditions=[{"name":"Common cold", "reason":"One educational possibility."}],
                urgency_level="LOW", recommended_next_steps=["Consult a professional if symptoms persist or worsen."],
                questions_for_doctor=["What changes should prompt a review?"],
                warning_signs=["Seek urgent help for severe breathing difficulty."])

@pytest.mark.parametrize("age", [-1, 121, "25", 2.5, True])
def test_bad_age(patient, age):
    with pytest.raises(ValidationError):
        PatientInput.model_validate({**patient.model_dump(), "age":age})

def test_empty_symptoms(patient):
    with pytest.raises(ValidationError):
        PatientInput.model_validate({**patient.model_dump(), "symptoms":[], "other_symptoms":"   "})

@pytest.mark.parametrize("wrapper", ["{}", "```json\n{}\n```", "Here is the output: {} trailing text"])
def test_json_extraction(valid, wrapper):
    result = parse_assessment(wrapper.replace("{}", json.dumps(valid)))
    assert result.urgency_level == "LOW"

@pytest.mark.parametrize("mutation", [{"urgency_level":"SAFE"}, {"summary":""},
    {"recommended_next_steps":[]}, {"possible_conditions":[{"name":"x"}]},
    {"unexpected":"field"}, {"summary":42}])
def test_invalid_schema(valid, mutation):
    with pytest.raises(InvalidAssessment):
        parse_assessment(json.dumps({**valid, **mutation}))

@pytest.mark.parametrize("raw", ["not JSON", "{}", "[]", "{broken", None])
def test_corrupt_json(raw):
    with pytest.raises(InvalidAssessment):
        parse_assessment(raw)

def test_quoted_braces(valid):
    valid["summary"] = 'Notes contain } and { and "quotes".'
    assert parse_assessment(json.dumps(valid)).summary == valid["summary"]

@pytest.mark.parametrize("flag", RED_FLAGS)
def test_red_flags(patient, flag):
    assert minimum_urgency(patient.model_copy(update={"red_flags":[flag]})) == "EMERGENCY"

def test_chest_breathing_no_api(patient):
    p = patient.model_copy(update={"symptoms":["Chest pain", "Shortness of breath"]})
    result, meta = assess(p, "", "unused")
    assert result.urgency_level == "EMERGENCY"
    assert "immediately" in result.summary
    assert meta["source"] == "Local emergency safeguard"

def test_severity_floor(patient, valid):
    p = patient.model_copy(update={"severity":9})
    assert enforce_floor(Assessment(**valid), p).urgency_level == "HIGH"

def test_emergency_model_output_is_not_reassuring(patient, valid):
    result = enforce_floor(Assessment(**{**valid,"urgency_level":"EMERGENCY"}), patient)
    assert result.possible_conditions == []
    assert "immediately" in result.summary

def test_message_roles(patient, valid):
    messages = message_demo(patient, Assessment(**valid))
    assert [type(m) for m in messages] == [SystemMessage, HumanMessage, AIMessage]

def test_templates(patient):
    text = PATIENT_TEMPLATE.format(**patient.model_dump())
    assert "Age: 25" in text
    messages = ASSESSMENT_CHAT_TEMPLATE.format_messages(patient_json=patient.model_dump_json(),
        patient_text=text, language="Urdu", safety_floor="LOW")
    assert "Urdu" in messages[1].content
    assert "Never confirm" in messages[0].content

@pytest.mark.parametrize("mode", ["Memory", "SQLite"])
def test_cache_repeated_calls(tmp_path, patient, valid, mode):
    cache = CacheManager(tmp_path, "a"*40).get(mode)
    fake = FakeListChatModel(responses=[json.dumps(valid), "INVALID"], cache=cache)
    chain = LLMChain(llm=fake, prompt=ASSESSMENT_CHAT_TEMPLATE, output_key="assessment")
    first, first_meta = assess(patient, "", "fake", cache=cache, chain=chain)
    second, second_meta = assess(patient, "", "fake", cache=cache, chain=chain)
    assert first == second
    assert first_meta["source"] == "Model"
    assert second_meta["source"] == "Cache"
    if mode == "SQLite":
        new_cache = CacheManager(tmp_path, "a"*40).get(mode)
        assert new_cache.lookup("persist", "model") is None
        from langchain_core.outputs import Generation
        new_cache.update("persist", "model", [Generation(text="saved")])
        assert CacheManager(tmp_path,"a"*40).get(mode).lookup("persist", "model")[0].text == "saved"


def test_cache_isolation_and_clear(tmp_path):
    from langchain_core.outputs import Generation
    a, b = CacheManager(tmp_path,"a"), CacheManager(tmp_path,"b")
    for mode in ["Memory", "SQLite"]:
        a.get(mode).update("prompt", "model", [Generation(text="private")])
        assert b.get(mode).lookup("prompt", "model") is None
    a.clear()
    assert a.get("Memory").lookup("prompt", "model") is None
    assert a.get("SQLite").lookup("prompt", "model") is None

@pytest.mark.parametrize("language", LANGUAGES)
def test_report_export(tmp_path, patient, valid, language):
    texts = {"English":"Educational guidance", "Urdu":"طبی رہنمائی", "Arabic":"إرشادات طبية",
             "Spanish":"Orientación médica", "French":"Conseils médicaux", "German":"Medizinische Hinweise"}
    record = {"created_at":"2026-10-25T12:00:00+00:00", "patient": {**patient.model_dump(), "language":language},
              "assessment":{**valid, "summary":texts[language]}}
    data = create_report(record)
    assert data.startswith(b"%PDF-")
    (tmp_path / f"report-{language}.pdf").write_bytes(data)


def test_no_key_raises(patient):
    with pytest.raises(ValueError, match="Connect"):
        assess(patient, "", "fake")


def test_streaming_uses_model_chunks(monkeypatch, valid):
    from src import chains
    from langchain_core.messages import AIMessageChunk
    class FakeStream:
        def stream(self, messages):
            assert "Urdu" in messages[0].content
            yield AIMessageChunk(content="پہلا ")
            yield AIMessageChunk(content="حصہ")
    monkeypatch.setattr(chains, "build_llm", lambda *args, **kwargs: FakeStream())
    assert "".join(chains.stream_narrative("unused", "fake", Assessment(**valid), "Urdu")) == "پہلا حصہ"


def test_voice_requires_key_and_size():
    from src.voice import transcribe_audio
    with pytest.raises(ValueError):
        transcribe_audio(b"audio", "")
    with pytest.raises(ValueError):
        transcribe_audio(b"", "fake")
    with pytest.raises(ValueError):
        transcribe_audio(b"x" * (10 * 1024 * 1024 + 1), "fake")


def test_voice_returns_reviewable_transcript(monkeypatch):
    from types import SimpleNamespace
    from src import voice
    class FakeClient:
        def __init__(self, **kwargs):
            self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self.create))
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def create(self, **kwargs):
            assert kwargs["file"][0] == "symptoms.wav"
            return SimpleNamespace(text="  Fever and cough  ")
    monkeypatch.setattr(voice, "OpenAI", FakeClient)
    assert voice.transcribe_audio(b"fake-recording", "fake-key") == "Fever and cough"


def test_real_chatopenai_chain_constructs_without_network(monkeypatch):
    # The host may use a SOCKS proxy without optional SOCKS packages installed.
    for name in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
        monkeypatch.delenv(name, raising=False)
    from src.chains import build_assessment_chain
    from langchain_openai import ChatOpenAI
    chain = build_assessment_chain("fake-not-a-real-key", "gpt-4o-mini")
    assert isinstance(chain, LLMChain)
    assert isinstance(chain.llm, ChatOpenAI)
