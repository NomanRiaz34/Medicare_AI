"""LLMChain meets the assignment; imports live in langchain-classic on LangChain v1."""
import json
from time import perf_counter
from langchain_classic.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from .models import PatientInput, Assessment
from .prompts import PATIENT_TEMPLATE, ASSESSMENT_CHAT_TEMPLATE, NARRATIVE_CHAT_TEMPLATE
from .safety import minimum_urgency, emergency_assessment, enforce_floor
from .utils import parse_assessment
from .config import DISCLAIMER
from .auth import OPENAI_BASE_URL

class CallTracker(BaseCallbackHandler):
    def __init__(self):
        self.called = False
    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.called = True

def build_llm(api_key, model, cache=False, structured=False):
    kwargs = {"response_format": {"type": "json_object"}} if structured else {}
    return ChatOpenAI(api_key=api_key, base_url=OPENAI_BASE_URL, model=model, temperature=0,
                      timeout=45, max_retries=1, max_tokens=1800,
                      cache=cache, model_kwargs=kwargs)

def build_assessment_chain(api_key, model, cache=False):
    return LLMChain(llm=build_llm(api_key, model, cache, structured=True),
                    prompt=ASSESSMENT_CHAT_TEMPLATE, output_key="assessment", verbose=False)

def assess(patient: PatientInput, api_key, model, cache=False, chain=None):
    started = perf_counter()
    floor = minimum_urgency(patient)
    if floor == "EMERGENCY":
        return emergency_assessment(patient), {"source": "Local emergency safeguard", "seconds": 0.0}
    if not api_key and chain is None:
        raise ValueError("Connect your OpenAI API key before requesting AI guidance.")
    chain = chain or build_assessment_chain(api_key, model, cache)
    values = patient.model_dump()
    args = {"patient_json": json.dumps(values, ensure_ascii=False),
            "patient_text": PATIENT_TEMPLATE.format(**values),
            "language": patient.language, "safety_floor": floor}
    tracker = CallTracker()
    output = chain.invoke(args, config={"callbacks": [tracker]})
    result = enforce_floor(parse_assessment(output["assessment"]), patient)
    # Read the cache lookup outcome, not elapsed time or model-start callbacks.
    source = "Cache" if getattr(cache, "last_lookup_hit", False) else "Model"
    return result, {"source": source, "seconds": round(perf_counter() - started, 2)}

def stream_narrative(api_key, model, result: Assessment, language: str):
    # Narrative calls are deliberately uncached: streaming is a separate paid call.
    llm = build_llm(api_key, model, cache=False)
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(
        language=language, assessment_json=result.model_dump_json())
    for chunk in llm.stream(messages):
        if isinstance(chunk.content, str) and chunk.content:
            yield chunk.content

def message_demo(patient: PatientInput, result: Assessment):
    # Explicit role objects for the course; no unbounded cross-patient chat context.
    return [SystemMessage(content=DISCLAIMER),
            HumanMessage(content=patient.model_dump_json()),
            AIMessage(content=result.model_dump_json())]
