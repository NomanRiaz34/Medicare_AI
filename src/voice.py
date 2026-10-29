"""Record -> transcribe -> human review -> explicit assessment submission."""
from openai import OpenAI
from .config import TRANSCRIPTION_MODEL
from .auth import OPENAI_BASE_URL

def transcribe_audio(audio: bytes, api_key: str) -> str:
    if not api_key:
        raise ValueError("Configure an API key before transcribing audio.")
    if not audio or len(audio) > 10 * 1024 * 1024:
        raise ValueError("Use a nonempty recording smaller than 10 MB.")
    with OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL, timeout=45, max_retries=1) as client:
        result = client.audio.transcriptions.create(
            model=TRANSCRIPTION_MODEL, file=("symptoms.wav", audio, "audio/wav"))
    return result.text.strip()[:2000]
