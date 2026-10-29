"""Tolerant JSON extraction followed by strict schema validation."""
import json
from .models import Assessment

class InvalidAssessment(ValueError):
    def __init__(self, raw):
        super().__init__("The AI response could not be validated. Please try again or contact a healthcare professional.")
        self.raw = raw

def parse_assessment(raw: str) -> Assessment:
    if not isinstance(raw, str) or len(raw) > 60000:
        raise InvalidAssessment("Response missing or too large.")
    # raw_decode handles fences/prose without incorrectly slicing braces inside strings.
    decoder = json.JSONDecoder()
    candidates = [raw.strip()]
    candidates += [raw[i:] for i, char in enumerate(raw) if char == "{"]
    for candidate in candidates:
        try:
            data, _ = decoder.raw_decode(candidate)
            return Assessment.model_validate(data)
        except (ValueError, TypeError):
            pass
    raise InvalidAssessment(raw)

def fallback_narrative(result: Assessment) -> str:
    return result.summary + "\n\n" + "\n".join("• " + s for s in result.recommended_next_steps)
