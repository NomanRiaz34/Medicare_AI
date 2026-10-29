from types import SimpleNamespace
from unittest.mock import MagicMock
import httpx
import pytest
from openai import (AuthenticationError, PermissionDeniedError, NotFoundError,
                    RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
from src import auth

FAKE_KEY = "sk-fictional-key-for-tests-only-123456789"

@pytest.fixture
def fake_client(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    factory = MagicMock(return_value=client)
    monkeypatch.setattr(auth, "OpenAI", factory)
    return factory, client

@pytest.mark.parametrize("key", ["", " ", "bad", "sk-"+"x"*600, "sk-"+"x"*25+" x"])
def test_invalid_key_is_rejected_without_request(fake_client, key):
    factory, _ = fake_client
    with pytest.raises(auth.KeyValidationError):
        auth.validate_api_key(key, "gpt-4o-mini")
    factory.assert_not_called()


def test_auth_uses_real_lookup_contract(fake_client):
    factory, client = fake_client
    client.models.retrieve.return_value = SimpleNamespace(id="gpt-4o-mini")
    result = auth.validate_api_key(" "+FAKE_KEY+" ", "gpt-4o-mini")
    assert result.model == "gpt-4o-mini"
    client.models.retrieve.assert_called_once_with("gpt-4o-mini")
    assert factory.call_args.kwargs["api_key"] == FAKE_KEY
    assert factory.call_args.kwargs["base_url"] == "https://api.openai.com/v1"
    assert factory.call_args.kwargs["max_retries"] == 0
    client.__exit__.assert_called_once()
    assert FAKE_KEY not in repr(result)

@pytest.mark.parametrize("cls,status,expected", [
    (AuthenticationError, 401, "rejected"),
    (PermissionDeniedError, 403, "permissions"),
    (NotFoundError, 404, "unavailable"),
    (RateLimitError, 429, "limit"),
    (InternalServerError, 500, "right now"),
])
def test_provider_errors_never_leak_credentials(fake_client, cls, status, expected):
    _, client = fake_client
    response = httpx.Response(status, request=httpx.Request("GET","https://api.openai.com/v1/models/test"))
    client.models.retrieve.side_effect = cls("sensitive "+FAKE_KEY, response=response, body=None)
    with pytest.raises(auth.KeyValidationError) as error:
        auth.validate_api_key(FAKE_KEY,"gpt-4o-mini")
    assert expected in str(error.value)
    assert FAKE_KEY not in str(error.value)

@pytest.mark.parametrize("cls", [APIConnectionError, APITimeoutError])
def test_connection_error(fake_client, cls):
    _, client = fake_client
    client.models.retrieve.side_effect = cls(request=httpx.Request("GET", "https://api.openai.com"))
    with pytest.raises(auth.KeyValidationError, match="reach OpenAI"):
        auth.validate_api_key(FAKE_KEY,"gpt-4o-mini")


def test_disconnect_removes_all_data_even_when_cleanup_fails():
    manager=MagicMock()
    manager.destroy.side_effect=RuntimeError("disk unavailable")
    state={"session_api_key":FAKE_KEY,"history":["fictional patient"],"connected":True,"cache_manager":manager,"key_entry":FAKE_KEY}
    auth.disconnect_session(state)
    assert state == {}
    manager.destroy.assert_called_once()


def test_destroy_only_own_sqlite_namespace(tmp_path):
    from src.cache_manager import CacheManager
    from langchain_core.outputs import Generation
    a,b=CacheManager(tmp_path,"one"),CacheManager(tmp_path,"two")
    for manager in (a,b):
        manager.get("SQLite").update("test","model",[Generation(text="fictional")])
    a.destroy()
    assert not (tmp_path/(a.namespace+".db")).exists()
    assert (tmp_path/(b.namespace+".db")).exists()
    assert b.get("SQLite").lookup("test","model")[0].text == "fictional"
