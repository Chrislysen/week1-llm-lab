"""xray_server.py: open the Zombie Constraint X-ray on localhost, with a live
decider you can run against the local model and a replay that plays a
dialogue line by line while the memory store updates beside it.

    python xray_server.py                # builds from results/, opens the browser
    python xray_server.py --port 8765 --no-browser

Standard library only. The page is rebuilt from the repository's result files
on every start, so what you see is what the files say. Live and replay calls
send the exact prompt the experiment used to Ollama at temperature 0; they
are demo calls and are not written to results/.

API (all JSON):
    GET  /api/health                    {"ollama": bool, "models": [...]}
    GET  /api/timeline?i=<n>&arm=<arm>  lines + per-line stores for all designs
    POST /api/run     {i, arm, design, model}   one decider call, whole reply
    POST /api/stream  {i, arm, design, model}   same, as server-sent events
"""
import argparse
import json
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e29_memory_semantics import build_user
from lineage_e29 import ARMS, DESIGNS, all_e29_dialogues, store_timeline
from lineage_eval import parse_plan
from structured import MAX_ATTEMPTS, ask_structured
from xray_build import build_data, render_page

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

    def messages_for(self, i, arm, design):
        d = self.dialogues[i]
        inst = d["instance"]
        return [{"role": "system", "content": SYSTEM.format(setting=inst.setting)},
                {"role": "user", "content": build_user(design, inst, d["arms"][arm])}]

    def timeline(self, i, arm):
        d = self.dialogues[i]
        dia = d["arms"][arm]
        return {"instance": d["instance"].id, "rotation": d["rotation"], "arm": arm,
                "lines": [{"speaker": s, "text": t, "tag": tag[0], "cid": tag[1]} for s, t, tag in dia],
                "stores": {X: store_timeline(X, d["instance"], dia) for X in DESIGNS}}

    def run_live(self, i, arm, design, model):
        from robust_client import RetryingOllamaClient
        with self.lock:
            if self.client is None:
                self.client = RetryingOllamaClient()
            t0 = time.time()
            res = ask_structured(client=self.client, model=model, temperature=TEMPERATURE,
                                 messages=self.messages_for(i, arm, design),
                                 validate=make_validator("default"),
                                 budget=Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600),
                                 speaker="Operator", expected=schema_hint("default"))
            seconds = round(time.time() - t0, 2)
        text = res.accepted_text or res.last_text or ""
        plan, err = parse_plan(text)
        return {"text": text, "plan": plan, "error": err, "seconds": seconds,
                "attempts": len(res.attempts),
                "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None}

    def stream_live(self, i, arm, design, model):
        """Yield token events from Ollama's streaming chat, then a final event
        with the parsed plan. Same messages and options as the recorded runs."""
        body = json.dumps({"model": model, "messages": self.messages_for(i, arm, design),
                           "stream": True, "options": {"temperature": TEMPERATURE}}).encode("utf-8")
        req = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with self.lock:
            t0 = time.time()
            parts, ptok, ctok = [], None, None
            with urllib.request.urlopen(req, timeout=300) as r:
                for raw in r:
                    raw = raw.strip()
                    if not raw:
                        continue
                    obj = json.loads(raw)
                    tok = (obj.get("message") or {}).get("content", "")
                    if tok:
                        parts.append(tok)
                        yield {"t": tok}
                    if obj.get("done"):
                        ptok, ctok = obj.get("prompt_eval_count"), obj.get("eval_count")
            seconds = round(time.time() - t0, 2)
        text = "".join(parts).strip()
        plan, err = parse_plan(text)
        yield {"done": True, "text": text, "plan": plan, "error": err, "seconds": seconds,
               "prompt_tokens": ptok, "completion_tokens": ctok}


STATE = None


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return  # the browser closed a stream or a page load; not an error
        super().handle_error(request, client_address)


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

    def _read_json(self):
        n = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(n) or b"{}")

    def _validate(self, req):
        i = int(req["i"]); arm = req["arm"]; design = req["design"]; model = req["model"]
        if not (0 <= i < len(STATE.dialogues)) or arm not in ARMS or design not in DESIGNS:
            return None, "bad dialogue, arm or design"
        if model not in ollama_models():
            return None, f"model {model!r} is not installed in Ollama"
        return (i, arm, design, model), None

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._send(200, STATE.page, "text/html; charset=utf-8")
        if url.path == "/api/health":
            m = ollama_models()
            return self._send(200, {"ollama": bool(m), "models": m})
        if url.path == "/api/e29":
            q = urllib.parse.parse_qs(url.query)
            try:
                i = int(q.get("i", ["-1"])[0])
                recs = STATE.data["e29_dialogues"]
                if not (0 <= i < len(recs)):
                    return self._send(400, {"error": "bad dialogue"})
                d = recs[i]
                return self._send(200, {"instance": d["instance"], "rotation": d["rotation"],
                                        "blocks": d["blocks"], "recorded": d["recorded"]})
            except Exception as e:
                return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        if url.path == "/api/timeline":
            q = urllib.parse.parse_qs(url.query)
            try:
                i = int(q.get("i", ["-1"])[0]); arm = q.get("arm", [""])[0]
                if not (0 <= i < len(STATE.dialogues)) or arm not in ARMS:
                    return self._send(400, {"error": "bad dialogue or arm"})
                return self._send(200, STATE.timeline(i, arm))
            except Exception as e:
                return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/run":
            try:
                args, err = self._validate(self._read_json())
                if err:
                    return self._send(400, {"error": err})
                return self._send(200, STATE.run_live(*args))
            except Exception as e:  # surfaced to the page, never hidden
                return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        if self.path == "/api/stream":
            try:
                args, err = self._validate(self._read_json())
            except Exception as e:
                return self._send(400, {"error": f"{type(e).__name__}: {e}"})
            if err:
                return self._send(400, {"error": err})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                for ev in STATE.stream_live(*args):
                    self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except Exception as e:
                try:
                    self.wfile.write(f"data: {json.dumps({'done': True, 'error': f'{type(e).__name__}: {e}'})}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass
            return
        return self._send(404, {"error": "not found"})

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
    srv = QuietServer(("127.0.0.1", a.port), Handler)
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
