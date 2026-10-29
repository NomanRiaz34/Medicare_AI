"""Bring-your-own-key connection gate. No credentials are written or globally cached."""
from dataclasses import dataclass
from openai import (OpenAI, AuthenticationError, PermissionDeniedError, NotFoundError,
                    RateLimitError, APIConnectionError, APITimeoutError, APIStatusError)

OPENAI_BASE_URL = "https://api.openai.com/v1"

class KeyValidationError(ValueError):
    """Only safe, authored text from this exception may be shown in the UI."""

@dataclass(frozen=True)
class VerifiedConnection:
    model: str


def validate_api_key(api_key: str, model: str) -> VerifiedConnection:
    """Make a real authenticated model lookup, not a prefix-only or fake login.

    No text generation is requested. This checks credentials + metadata access to
    this model, not generation quota, JSON compatibility, or transcription access.
    """
    key = api_key.strip()
    if not key or len(key) < 20 or len(key) > 512 or any(c.isspace() for c in key):
        raise KeyValidationError("Enter your complete OpenAI API key without spaces.")
    if not model or len(model) > 120:
        raise KeyValidationError("The configured model is invalid. Contact the app owner.")
    try:
        # Pin the destination: never send visitor keys to an environment-supplied proxy API endpoint.
        with OpenAI(api_key=key, base_url=OPENAI_BASE_URL, timeout=15, max_retries=0) as client:
            result = client.models.retrieve(model)
        if not getattr(result, "id", None):
            raise KeyValidationError("OpenAI returned an unexpected response. Please try again.")
        return VerifiedConnection(model=model)
    except AuthenticationError:
        raise KeyValidationError("OpenAI rejected this key. Check that it is correct and has not been revoked.") from None
    except PermissionDeniedError:
        raise KeyValidationError("This key cannot access the configured model. Check its project permissions.") from None
    except NotFoundError:
        raise KeyValidationError("The configured model is unavailable to this key. Ask the app owner to check the model setting.") from None
    except RateLimitError:
        raise KeyValidationError("OpenAI could not complete the check because of a rate or account limit. Try again later.") from None
    except (APIConnectionError, APITimeoutError):
        raise KeyValidationError("Could not reach OpenAI. Check your connection and try again.") from None
    except APIStatusError:
        raise KeyValidationError("OpenAI could not verify the key right now. Please try again later.") from None


def disconnect_session(state):
    """Clear patient/form/key state and best-effort remove the session-owned cache."""
    manager = state.get("cache_manager")
    if manager is not None:
        try:
            manager.destroy()
        except Exception:
            # Cleanup must never prevent key removal. Hosting disk erasure is not guaranteed.
            pass
    for key in list(state):
        del state[key]
