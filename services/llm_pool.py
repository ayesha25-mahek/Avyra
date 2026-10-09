"""
services/llm_pool.py
---------------------
LLMPool — multi-key, sequential fallback LLM provider for BizzoraAI.

Strategy:
  1. Try GEMINI_API_KEY_1 → GEMINI_API_KEY_5 in order.
  2. On any error move to the next key.
  3. After all Gemini keys exhausted, try GROQ_API_KEY_1 → GROQ_API_KEY_5,
     each key tries multiple Groq models in order.
  4. After all Groq keys exhausted, try local Ollama (sovereign / on-premise).
  5. If every provider fails, raise RuntimeError.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Model names ─────────────────────────────────────────────────────────────
# Based on Google API recommendations for active models
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]

# Groq models currently available on the configured API key
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound",
]

# ─── Ollama (local / sovereign) ───────────────────────────────────────────────
# Override these in .env if your Ollama endpoint or model differs.
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

MAX_KEYS = 5


class LLMPool:
    """
    Sequential multi-key, multi-model LLM pool.

    Reads GEMINI_API_KEY_1..5 and GROQ_API_KEY_1..5 from the environment.
    .generate(prompt) works through every available key and model combination,
    falling through to the next on any exception.
    """

    def __init__(self, preferred_provider: str = "auto") -> None:
        self.preferred_provider = (preferred_provider or "auto").lower().strip()
        self.gemini_keys: list = []
        for i in range(1, MAX_KEYS + 1):
            key = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
            if key:
                self.gemini_keys.append(key)

        self.groq_keys: list = []
        for i in range(1, MAX_KEYS + 1):
            key = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
            if key:
                self.groq_keys.append(key)

        if not self.gemini_keys and not self.groq_keys and not OLLAMA_BASE_URL:
            raise RuntimeError(
                "LLMPool: No LLM API keys or Ollama endpoint found. "
                "Set GEMINI_API_KEY_1, GROQ_API_KEY_1, or OLLAMA_BASE_URL in .env"
            )

        logger.info(
            "LLMPool ready (preferred: %s) — Gemini keys: %d, Groq keys: %d, Ollama: %s (%s)",
            self.preferred_provider,
            len(self.gemini_keys),
            len(self.groq_keys),
            OLLAMA_BASE_URL,
            OLLAMA_MODEL,
        )

    # ─── Gemini ──────────────────────────────────────────────────────────────

    def _try_gemini(self, key: str, key_idx: int, model: str, prompt: str) -> str:
        from google import genai  # type: ignore

        logger.info("Gemini key %d | model %s", key_idx, model)
        client = genai.Client(api_key=key)
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text
        if not text:
            raise ValueError("Gemini returned empty response.")
        logger.info("[SUCCESS] Gemini key %d / %s succeeded", key_idx, model)
        return text

    # ─── Groq ────────────────────────────────────────────────────────────────

    def _try_groq(self, key: str, key_idx: int, model: str, prompt: str) -> str:
        from groq import Groq  # type: ignore

        logger.info("Groq key %d | model %s", key_idx, model)
        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = response.choices[0].message.content
        if not text:
            raise ValueError("Groq returned empty response.")
        logger.info("[SUCCESS] Groq key %d / %s succeeded", key_idx, model)
        return text

    # ─── Ollama (local / sovereign) ──────────────────────────────────────────

    def _try_ollama(self, prompt: str, model: str = None) -> str:
        """Call local Ollama via its /api/chat REST endpoint (no extra SDK needed)."""
        import requests  # already in requirements.txt

        target_model = model or OLLAMA_MODEL
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        logger.info("Ollama local | model %s | url %s", target_model, url)
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "").strip()
        if not text:
            raise ValueError(f"Ollama ({target_model}) returned empty response.")
        logger.info("[SUCCESS] Ollama (%s) succeeded.", target_model)
        return text

    def generate_with_ollama(self, prompt: str, model: str = None) -> str:
        """Directly generate with local Ollama sovereign model."""
        return self._try_ollama(prompt, model=model)

    # ─── Public API ──────────────────────────────────────────────────────────

    def generate(self, prompt: str, *args, **kwargs) -> str:
        """
        If preferred_provider is 'ollama' or 'sovereign', executes strictly via local Ollama
        (preventing any external/cloud leakage).
        Otherwise, tries every Gemini key x model combo, then every Groq key x model combo,
        then local Ollama.
        """
        errors: list = []
        target_model = kwargs.get("model")
        task_type = kwargs.get("task_type")

        # ── Preferred Local Ollama (Sovereign Mode) ──
        if self.preferred_provider in ("ollama", "local", "local_ollama", "sovereign"):
            logger.info("Directing generation to local Ollama (target model: %s)...", target_model or OLLAMA_MODEL)
            try:
                return self._try_ollama(prompt, model=target_model)
            except Exception as exc:
                msg = f"Local Ollama ({target_model or OLLAMA_MODEL}) failed: {exc}"
                logger.error(msg)
                # STRICT SOVEREIGNTY: In sovereign/ollama mode, never silently leak to external cloud APIs
                raise RuntimeError(
                    f"Sovereign execution failed locally: {exc}. External cloud fallback blocked to guarantee 0 external calls."
                )

        # ── Gemini ──
        for idx, key in enumerate(self.gemini_keys, start=1):
            for model in GEMINI_MODELS:
                try:
                    return self._try_gemini(key, idx, model, prompt)
                except Exception as exc:
                    msg = f"Gemini key {idx} / {model} failed: {exc}"
                    logger.warning(msg)
                    errors.append(msg)

        if self.gemini_keys:
            logger.warning("All Gemini keys exhausted — switching to Groq.")

        # ── Groq ──
        for idx, key in enumerate(self.groq_keys, start=1):
            for model in GROQ_MODELS:
                try:
                    return self._try_groq(key, idx, model, prompt)
                except Exception as exc:
                    msg = f"Groq key {idx} / {model} failed: {exc}"
                    logger.warning(msg)
                    errors.append(msg)

        # ── Ollama (Local Sovereign Fallback for auto mode, if not already attempted) ──
        if self.preferred_provider not in ("ollama", "local", "local_ollama", "sovereign") and OLLAMA_BASE_URL:
            logger.warning("All cloud LLM keys exhausted — switching to local Ollama (%s).", OLLAMA_MODEL)
            try:
                return self._try_ollama(prompt, model=target_model)
            except Exception as exc:
                msg = f"Ollama ({target_model or OLLAMA_MODEL}) failed: {exc}"
                logger.warning(msg)
                errors.append(msg)

        raise RuntimeError(
            "LLMPool: All providers and models failed.\n" + "\n".join(errors)
        )
