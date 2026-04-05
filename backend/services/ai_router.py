import os
import time
from typing import Tuple, Optional

import httpx
import google.generativeai as genai

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

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


def _build_prompt(query: str, context: str, has_video: bool = False) -> str:
    prompt = (
        "You are an expert multi-modal UI assistant analyzing a video.\n"
        "You have access to:\n"
        "- Object detection (YOLO)\n"
        "- Facial emotions (DeepFace)\n"
        "- Scene captions (BLIP)\n"
        "- Audio transcriptions (Whisper)\n"
    )
    if has_video:
        prompt += "- Raw Video File (Uploaded to API). Please utilize the raw video directly to estimate spatial metrics (speed, altitude, distance) estimating via parallax, object sizes, and motion.\n"
    
    prompt += (
        "\nHere is the data:\n\n"
        f"{context}\n\n"
        f"User question: {query}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Be extremely direct, concise, and straight to the point.\n"
        "2. DO NOT mention 'inconsistencies' between different models (e.g., if YOLO sees a bear but BLIP sees a monkey). Synthesize the most logical conclusion confidently without complaining to the user.\n"
        "3. Never narrate your own chain of thought. Just answer the question.\n"
        "4. Always prioritize human element and action. If estimating speed or altitude, provide your best reasoned guess based on visual cues."
    )
    return prompt


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
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return ""


def _call_gemini(prompt: str, video_path: Optional[str] = None) -> str:
    """Call Gemini 1.5 Flash for complex queries, with optional Raw Video upload."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        contents = [prompt]
        uploaded_file = None
        
        if video_path and os.path.exists(video_path):
            uploaded_file = genai.upload_file(video_path)
            # Wait for processing
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                print("Gemini video processing failed.")
            else:
                contents.insert(0, uploaded_file)

        response = model.generate_content(contents)
        
        # Cleanup file after generation so we don't leak quotas
        if uploaded_file:
            genai.delete_file(uploaded_file.name)
            
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return ""


def route_query(query: str, context: str, video_path: Optional[str] = None) -> Tuple[str, str]:
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
    prompt = _build_prompt(query, context, has_video=bool(video_path and GEMINI_API_KEY))

    # ── Complex + Gemini available → cloud ────────────────────
    if _is_complex(query) and GEMINI_API_KEY:
        response = _call_gemini(prompt, video_path)
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
