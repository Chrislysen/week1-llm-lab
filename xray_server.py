"""xray_server.py: open the Zombie Constraint X-ray on localhost, with a live
decider you can run against the local model.

    python xray_server.py                # builds from results/, opens the browser
    python xray_server.py --port 8765 --no-browser

Standard library only. The page is rebuilt from the repository's result files
on every start, so what you see is what the files say. "Run live" sends the
exact prompt the experiment used to Ollama at temperature 0; those calls are
demo calls and are not written to results/.
"""
import argparse
import json
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e29_memory_semantics import build_user
from lineage_e29 import ARMS, DESIGNS, all_e29_dialogues
from lineage_eval import parse_plan
from structured import MAX_ATTEMPTS, ask_structured
from xray_build import E29_MODELS, build_data, render_page

OLLAMA = "http://localhost:11434"


def ollama_models():
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=2) as r:
            tags = json.load(r)
        return sorted(m["name"] for m in tags.get("models", []))
    except Exception:
        return []


class State:
    def __init__(self):
        self.models = ollama_models()
        self.data = build_data(live=True, live_models=self.models)
        self.page = render_page(self.data).encode("utf-8")
        self.dialogues = all_e29_dialogues()
        self.lock = threading.Lock()
        self.client = None

    def run_live(self, i, arm, design, model):
        from robust_client import RetryingOllamaClient
        assert arm in ARMS and design in DESIGNS
        d = self.dialogues[i]
        inst = d["instance"]
        user = build_user(design, inst, d["arms"][arm])
        with self.lock:
            if self.client is None:
                self.client = RetryingOllamaClient()
            t0 = time.time()
            res = ask_structured(client=self.client, model=model, temperature=TEMPERATURE,
                                 messages=[{"role": "system", "content": SYSTEM.format(setting=inst.setting)},
                                           {"role": "user", "content": user}],
                                 validate=make_validator("default"),
                                 budget=Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600),
                                 speaker="Operator", expected=schema_hint("default"))
            seconds = round(time.time() - t0, 2)
        text = res.accepted_text or res.last_text or ""
        plan, err = parse_plan(text)
        return {"text": text, "plan": plan, "error": err, "seconds": seconds,
                "attempts": len(res.attempts),
                "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None}


STATE = None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, STATE.page, "text/html; charset=utf-8")
        if self.path == "/api/health":
            return self._send(200, {"ollama": bool(ollama_models()), "models": ollama_models()})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/run":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
            i = int(req["i"]); arm = req["arm"]; design = req["design"]; model = req["model"]
            if not (0 <= i < len(STATE.dialogues)) or arm not in ARMS or design not in DESIGNS:
                return self._send(400, {"error": "bad dialogue, arm or design"})
            if model not in ollama_models():
                return self._send(400, {"error": f"model {model!r} is not installed in Ollama"})
            return self._send(200, STATE.run_live(i, arm, design, model))
        except Exception as e:  # surfaced to the page, never hidden
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, fmt, *args):
        print("  " + (fmt % args))


def main():
    global STATE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    print("building the X-ray from results/ ...")
    STATE = State()
    d = STATE.data
    print(f"  corpus {d['corpus_hash']} · E29 corpus {d['e29_hash']} · {len(d['e29_dialogues'])} E29 dialogues · "
          f"{len(d['e29b'])} real-extractor records")
    print(f"  ollama: {'up, ' + str(len(STATE.models)) + ' models' if STATE.models else 'not reachable (recorded plans still shown)'}")
    url = f"http://localhost:{a.port}/"
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"  serving {url}   (Ctrl+C to stop)")
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
