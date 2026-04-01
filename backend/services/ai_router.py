import os
from typing import Tuple

import httpx
import google.generativeai as genai

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Keywords that mark a query as complex
COMPLEX_KEYWORDS = [
    "emotion", "story", "explain", "why", "how does", "what is happening",
    "describe", "analyze", "summarize", "feeling", "narrative",
]


def _is_complex(query: str) -> bool:
    lower = query.lower()
    if len(query) > 80:
        return True
    return any(kw in lower for kw in COMPLEX_KEYWORDS)


def _build_prompt(query: str, context: str) -> str:
    return (
        "You are analyzing a video using multi-modal AI. You have:\n"
        "- Object detection: what objects appear in each frame\n"
        "- Facial emotion recognition: what emotions people are showing\n"
        "- Scene captions: natural language descriptions of each frame\n"
        "- Audio transcription: what people are saying, with [LOUD] markers for shouting\n\n"
        "Here is the analysis data:\n\n"
        f"{context}\n\n"
        f"User question: {query}\n"
        "Answer based on ALL the available data. Reference specific timestamps when relevant. "
        "If the question is about emotions, prioritize the emotion data. "
        "If about speech or sounds, prioritize the audio data."
    )


def _call_ollama(prompt: str) -> str:
    """Call Ollama's /api/generate endpoint (local Docker development)."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "No response from local model.")
    except Exception as e:
        print(f"Ollama error: {e}")
        return f"Local model unavailable: {e}"


def _call_groq(prompt: str) -> str:
    """Call Groq API — OpenAI-compatible, replaces Ollama in production."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.2-3b-preview",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return ""


def _call_gemini(prompt: str) -> str:
    """Call Gemini 1.5 Flash for complex queries."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return ""


def route_query(query: str, context: str) -> Tuple[str, str]:
    """
    Route a user query to the appropriate AI backend.

    Priority:
    1. Complex query + GEMINI_API_KEY → Gemini 1.5 Flash (cloud)
    2. GROQ_API_KEY set → Groq (production replacement for Ollama)
    3. Ollama (local Docker development)

    Returns:
        (response_text, model_used)
        model_used is "cloud" or "local"
    """
    prompt = _build_prompt(query, context)

    # ── Complex + Gemini available → cloud ────────────────────
    if _is_complex(query) and GEMINI_API_KEY:
        response = _call_gemini(prompt)
        if response:
            return response, "cloud"
        # Fall through if Gemini fails

    # ── Groq available (production) → local via Groq ──────────
    if GROQ_API_KEY:
        response = _call_groq(prompt)
        if response:
            return response, "local"
        # Fall through if Groq fails

    # ── Ollama (local Docker dev) ─────────────────────────────
    response = _call_ollama(prompt)
    return response, "local"
