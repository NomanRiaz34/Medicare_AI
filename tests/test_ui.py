"""No real keys and no paid calls. UI connection checks are mocked explicitly."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.auth import VerifiedConnection, KeyValidationError

APP = str(Path(__file__).resolve().parents[1] / "app.py")
FAKE_KEY = "sk-fictional-key-for-tests-only-123456789"

def button(at, label):
    return next(x for x in at.button if x.label == label)

def widget(items, label):
    return next(x for x in items if x.label == label)

@pytest.fixture
def connect(monkeypatch):
    from src import auth
    calls=[]
    def verify(key, model):
        calls.append((key, model))
        return VerifiedConnection(model)
    monkeypatch.setattr(auth,"validate_api_key",verify)
    def run():
        at=AppTest.from_file(APP).run(timeout=30)
        widget(at.text_input,"OpenAI API key").set_value(FAKE_KEY)
        next(c for c in at.checkbox if "API usage is billed" in c.label).check()
        button(at,"Verify key & continue").click().run(timeout=30)
        assert not at.exception
        return at
    run.calls=calls
    return run


def test_initial_screen_is_locked_even_with_env_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-environment-key-must-not-unlock-anything")
    at=AppTest.from_file(APP).run(timeout=30)
    assert not at.exception
    assert len(at.tabs)==0
    assert not any(b.label=="Assess symptoms" for b in at.button)
    field = widget(at.text_input,"OpenAI API key")
    enum = field.proto.DESCRIPTOR.fields_by_name["type"].enum_type
    assert enum.values_by_number[field.proto.type].name == "PASSWORD"
    assert "session_api_key" not in at.session_state


def test_consent_required_and_no_validation_call(monkeypatch):
    from src import auth
    def forbidden(*args):
        raise AssertionError("No network check without consent")
    monkeypatch.setattr(auth,"validate_api_key",forbidden)
    at=AppTest.from_file(APP).run(timeout=30)
    widget(at.text_input,"OpenAI API key").set_value(FAKE_KEY)
    button(at,"Verify key & continue").click().run()
    assert not at.exception
    assert any("acknowledge" in w.value for w in at.warning)
    assert len(at.tabs)==0


def test_rejected_key_stays_on_login(monkeypatch):
    from src import auth
    def fail(*args):
        raise KeyValidationError("OpenAI rejected this key.")
    monkeypatch.setattr(auth,"validate_api_key",fail)
    at=AppTest.from_file(APP).run(timeout=30)
    widget(at.text_input,"OpenAI API key").set_value(FAKE_KEY)
    next(c for c in at.checkbox if "API usage is billed" in c.label).check()
    button(at,"Verify key & continue").click().run()
    assert not at.exception
    assert len(at.tabs)==0
    assert any("rejected" in e.value for e in at.error)
    assert "session_api_key" not in at.session_state


def test_success_and_rerun_do_not_revalidate(connect):
    at=connect()
    assert len(at.tabs)==4
    assert at.session_state["session_api_key"]==FAKE_KEY
    assert "key_entry" not in at.session_state
    at.run()
    assert len(connect.calls)==1
    widget(at.toggle,"Dark mode").set_value(True).run()
    assert not at.exception
    assert len(connect.calls)==1


def test_signout_drops_key_and_history(connect):
    at=connect()
    at.session_state["history"]=[{"id":"fake"}]
    button(at,"Sign out").click().run(timeout=30)
    assert not at.exception
    assert len(at.tabs)==0
    assert "session_api_key" not in at.session_state
    assert "history" not in at.session_state


def test_invalid_form_does_not_crash(connect):
    at=connect()
    button(at,"Assess symptoms").click().run()
    assert not at.exception
    assert any("whole-number age" in w.value for w in at.warning)


def test_emergency_after_connection_does_not_call_assessment_model(connect):
    at=connect()
    widget(at.text_input,"Patient age in whole years").set_value("40")
    widget(at.multiselect,"Symptoms").set_value(["Chest pain","Shortness of breath"])
    button(at,"Assess symptoms").click().run(timeout=30)
    assert not at.exception
    assert any(m.value=="EMERGENCY" for m in at.metric)
    assert any("Seek emergency help immediately" in e.value for e in at.error)


def test_full_flow_uses_session_key_including_stream(connect, monkeypatch):
    from src import chains
    from src.models import Assessment
    keys=[]
    def fake_assess(patient,key,*args,**kwargs):
        keys.append(key)
        return Assessment(summary="Educational information; consult a professional.",possible_conditions=[],
            urgency_level="MEDIUM",recommended_next_steps=["Arrange a professional review."],
            questions_for_doctor=["What should I watch for?"],warning_signs=["Seek help if breathing becomes difficult."]), {"source":"Model","seconds":0.1}
    def failed_stream(key,*args,**kwargs):
        keys.append(key)
        yield "A partial explanation. "
        raise RuntimeError("Simulated connection failure")
    monkeypatch.setattr(chains,"assess",fake_assess)
    monkeypatch.setattr(chains,"stream_narrative",failed_stream)
    at=connect()
    widget(at.text_input,"Patient age in whole years").set_value("25")
    widget(at.multiselect,"Symptoms").set_value(["Cough"])
    next(c for c in at.checkbox if "agree to send this information" in c.label).check()
    button(at,"Assess symptoms").click().run(timeout=30)
    assert not at.exception
    assert keys==[FAKE_KEY,FAKE_KEY]
    assert len(at.session_state["history"])==1
    assert "unavailable" in at.session_state["history"][0]["narrative"]
    button(at,"Delete session history").click().run()
    assert at.session_state["history"]==[]


def test_browser_sessions_have_different_cache_identity(connect):
    first=connect()
    second=connect()
    assert first.session_state["session_token"]!=second.session_state["session_token"]
    assert first.session_state["cache_manager"] is not second.session_state["cache_manager"]
