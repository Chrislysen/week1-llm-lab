"""robust_client.py: bounded HTTP retry around Ollama. Infrastructure, not method.

WHY THIS EXISTS. Two long runs (E11 on aya-expanse, E12 on llama) died mid-chunk
on a transient `500 Server Error` from Ollama's /api/chat -- memory pressure
after cycling several models through VRAM. Chunking limited the loss to one
chunk each time, but a 432-call experiment losing 144 calls to a server hiccup is
wasted compute, not a finding.

WHAT THIS IS NOT. It is not a retry on bad model OUTPUT. Output that fails to
parse still goes through structured.py's bounded parse/retry and is recorded as
a failed attempt, exactly as before. This retries only TRANSPORT failures --
HTTP 5xx and connection errors -- where no reply was produced at all. A retried
call sends a byte-identical request, so nothing about the experiment changes.

Retries are counted and printed at the end of a run, so a corpus scored during a
flaky period cannot look identical to one scored cleanly.
"""
import time

import requests

from llm_client import ChatResponse, OllamaClient

MAX_TRANSPORT_RETRIES = 4
BACKOFF_SECONDS = (2, 5, 15, 30)


class RetryingOllamaClient(OllamaClient):
    """OllamaClient that survives a transient 5xx instead of losing the run."""

    def __init__(self, host="http://localhost:11434"):
        super().__init__(host)
        self.transport_retries = 0
        self.seed = None

    def chat(self, model, messages, temperature=0.7, num_predict=None):
        options = {"temperature": temperature}
        if num_predict is not None:          # runaway guard, opt-in only
            options["num_predict"] = num_predict
        if self.seed is not None:
            options["seed"] = self.seed
        last = None
        for attempt in range(MAX_TRANSPORT_RETRIES + 1):
            t0 = time.monotonic()
            try:
                resp = requests.post(
                    f"{self.host}/api/chat",
                    json={"model": model, "messages": messages,
                          "stream": False, "options": options},
                    timeout=300)
                resp.raise_for_status()
                data = resp.json()
                return ChatResponse(
                    text=data["message"]["content"].strip(),
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    seconds=time.monotonic() - t0)
            except (requests.HTTPError, requests.ConnectionError,
                    requests.Timeout) as exc:
                last = exc
                if attempt == MAX_TRANSPORT_RETRIES:
                    break
                self.transport_retries += 1
                time.sleep(BACKOFF_SECONDS[attempt])
        raise RuntimeError(
            f"Ollama transport failed after {MAX_TRANSPORT_RETRIES} retries: "
            f"{last}") from last
