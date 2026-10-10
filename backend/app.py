"""
TheLogWatch cloud backend - FastAPI + MongoDB. Deploy on Render (see render.yaml).

Environment
  MONGODB_URI        MongoDB Atlas connection string (mongodb+srv://...). "mongomock://" = in-memory test mode
  MONGODB_DB         database name (default: logwatch)
  ADMIN_PASSWORD     password for the booth operator (dashboard controls, viewing logs)
  SECRET_KEY         signs login tokens (Render generates one)
  INGEST_KEY         devices / phones must send this to push logs
  ALLOWED_ORIGINS    comma-separated front-end origins, e.g. https://logwatch.netlify.app (default *)
  PUBLIC_VIEW        "true" lets anyone with the link watch the dashboard read-only (default false)
  EVENT_TTL_DAYS     logs are deleted automatically after this many days (default 14; 0 = keep)
  ANTHROPIC_API_KEY  optional - enables "Ask AI"
  CLAUDE_MODEL       default claude-sonnet-5

Run locally:  uvicorn app:app --reload   (from the backend folder)
"""
import asyncio
import base64
import hashlib
import hmac
import json
import math
import os
import secrets
import time
from contextlib import asynccontextmanager
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

import scenarios
from classifier import LEVELS, Engine
from store import Store

# ------------------------------------------------------------------- config

def env(name, default=""):
    return os.environ.get(name, default).strip()


MONGODB_URI = env("MONGODB_URI") or "mongomock://"
ADMIN_PASSWORD = env("ADMIN_PASSWORD")
SECRET_KEY = env("SECRET_KEY") or hashlib.sha256(("logwatch|" + ADMIN_PASSWORD).encode()).hexdigest()
INGEST_KEY = env("INGEST_KEY")
ORIGINS = [o.strip().rstrip("/") for o in env("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
PUBLIC_VIEW = env("PUBLIC_VIEW", "false").lower() in ("1", "true", "yes")
API_KEY = env("ANTHROPIC_API_KEY")
MODEL = env("CLAUDE_MODEL", "claude-sonnet-5")
TOKEN_HOURS = 12

store = Store(MONGODB_URI, env("MONGODB_DB", "logwatch"), float(env("EVENT_TTL_DAYS", "14") or 0))
engine = Engine()
engine_lock = asyncio.Lock()
subscribers: set[asyncio.Queue] = set()

@asynccontextmanager
async def lifespan(_app):
    await asyncio.to_thread(store.init)
    for dev, mac in await asyncio.to_thread(store.known_all):
        engine.known_macs[dev].add(mac)
    if store.memory:
        print("WARNING: MONGODB_URI not set - using an in-memory database. Nothing will be saved.")
    if not ADMIN_PASSWORD:
        print("WARNING: ADMIN_PASSWORD not set - dashboard login is disabled.")
    yield
    await player.stop()


app = FastAPI(title="TheLogWatch", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "X-Ingest-Key"])


# ------------------------------------------------------------------- auth

def make_token():
    exp = int(time.time()) + TOKEN_HOURS * 3600
    payload = f"admin|{exp}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def check_token(tok):
    try:
        role, exp, sig = base64.urlsafe_b64decode(tok.encode()).decode().split("|")
    except Exception:
        return False
    good = hmac.new(SECRET_KEY.encode(), f"{role}|{exp}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, good) and int(exp) > time.time()


def bearer(req: Request):
    h = req.headers.get("authorization", "")
    tok = h[7:] if h.lower().startswith("bearer ") else req.query_params.get("token", "")
    return tok and check_token(tok)


def require_admin(req: Request):
    if not ADMIN_PASSWORD:
        raise HTTPException(503, "ADMIN_PASSWORD is not set on the server")
    if not bearer(req):
        raise HTTPException(401, "login required")


def require_viewer(req: Request):
    if PUBLIC_VIEW:
        return
    require_admin(req)


def client_ip(req: Request):
    fwd = req.headers.get("x-forwarded-for", "")
    return (req.headers.get("true-client-ip") or (fwd.split(",")[0].strip() if fwd else "")
            or (req.client.host if req.client else "?"))


# ------------------------------------------------------------------- rate limits

class Limiter:
    def __init__(self, per_minute):
        self.per_minute = per_minute
        self.hits = defaultdict(deque)

    def allow(self, key, n=1):
        now = time.time()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) + n > self.per_minute:
            return False
        q.extend([now] * n)
        if len(self.hits) > 5000:            # don't grow forever
            for k in list(self.hits)[:1000]:
                if not self.hits[k]:
                    del self.hits[k]
        return True


ingest_limit = Limiter(1500)   # log lines per IP per minute
login_limit = Limiter(10)      # login attempts per IP per minute


# ------------------------------------------------------------------- ingest

def broadcast(msg):
    data = json.dumps(msg)
    for q in list(subscribers):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


async def ingest(raw_events):
    new_known = []
    out = []
    async with engine_lock:
        engine.on_new_device = lambda d, m: new_known.append((d, m))
        for ev in raw_events:
            if not isinstance(ev, dict):
                ev = {"raw": str(ev)}
            ev = {k: v for k, v in ev.items() if isinstance(k, str) and not k.startswith("$")}
            for c in engine.classify(ev):
                c["id"] = secrets.token_hex(8)
                c["device"] = str(c["device"])[:80]
                c["scenario"] = str(c["scenario"])[:60] if c.get("scenario") else None
                out.append(c)
    await asyncio.to_thread(store.insert_events, [dict(c) for c in out])
    for d, m in new_known:
        await asyncio.to_thread(store.add_known, d, m)
    for c in out:
        broadcast({"type": "event", "event": c})
    return out


player = scenarios.Player(ingest, engine)


# ------------------------------------------------------------------- routes

@app.get("/api/health")
async def health():
    try:
        await asyncio.to_thread(store.ping)
        db = "memory" if store.memory else "ok"
    except Exception as ex:
        db = f"error: {type(ex).__name__}"
    return {"ok": True, "db": db, "ai": bool(API_KEY), "public_view": PUBLIC_VIEW,
            "login": bool(ADMIN_PASSWORD), "ingest_key": bool(INGEST_KEY)}


@app.post("/api/login")
async def login(req: Request):
    if not login_limit.allow(client_ip(req)):
        raise HTTPException(429, "too many attempts, wait a minute")
    try:
        body = await req.json()
    except Exception:
        body = {}
    pw = str(body.get("password", ""))
    if not ADMIN_PASSWORD or not hmac.compare_digest(pw.encode(), ADMIN_PASSWORD.encode()):
        await asyncio.sleep(0.8)
        raise HTTPException(401, "wrong password")
    return {"token": make_token(), "hours": TOKEN_HOURS}


@app.get("/api/state", dependencies=[Depends(require_viewer)])
async def state():
    evs, devs, counts = await asyncio.gather(
        asyncio.to_thread(store.recent, 400),
        asyncio.to_thread(store.device_list),
        asyncio.to_thread(store.counts))
    return {"events": evs, "devices": devs, "counts": counts, "total": sum(counts.values()),
            "levels": LEVELS, "now_playing": player.now_playing, "ai": bool(API_KEY),
            "public_view": PUBLIC_VIEW}


@app.get("/api/events", dependencies=[Depends(require_viewer)])
async def event_history(device: Optional[str] = None, source: Optional[str] = None,
                        alerts: bool = False, before: Optional[str] = None,
                        limit: int = Query(250, ge=1, le=400)):
    cursor = None
    if before is not None:
        try:
            cursor = json.loads(before)
            if (not isinstance(cursor, list) or len(cursor) != 2
                    or type(cursor[0]) not in (int, float) or not math.isfinite(cursor[0])
                    or not isinstance(cursor[1], str)):
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(400, "invalid history cursor")
    return await asyncio.to_thread(store.history, limit, device, source, alerts, cursor)


@app.get("/api/stream", dependencies=[Depends(require_viewer)])
async def stream(req: Request):
    q: asyncio.Queue = asyncio.Queue(maxsize=2000)
    subscribers.add(q)

    async def gen():
        try:
            yield "retry: 3000\n\n"
            while True:
                if await req.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    data = json.dumps({"type": "ping", "now_playing": player.now_playing})
                yield f"data: {data}\n\n"
        finally:
            subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/scenarios", dependencies=[Depends(require_viewer)])
async def list_scenarios():
    lib = scenarios.load_library()
    return [{"id": k, "title": v["title"], "card": v["card"], "device": v["device"], "lines": len(v["lines"])}
            for k, v in lib.items()]


@app.get("/api/join", dependencies=[Depends(require_admin)])
async def join_info():
    return {"ingest_key": INGEST_KEY}


@app.post("/api/ingest")
async def api_ingest(req: Request):
    key = req.headers.get("x-ingest-key") or req.query_params.get("key", "")
    if not (bearer(req) or (INGEST_KEY and hmac.compare_digest(key.encode(), INGEST_KEY.encode()))):
        raise HTTPException(401, "missing or wrong ingest key")
    body = await req.body()
    if len(body) > 1_000_000:
        raise HTTPException(413, "too large (1 MB max per request)")
    txt = body.decode("utf-8", "replace").strip()
    evs = None
    if txt[:1] in "[{":
        try:
            parsed = json.loads(txt)
            evs = parsed if isinstance(parsed, list) else [parsed]
        except ValueError:
            evs = None
    if evs is None:
        evs = [{"raw": line} for line in txt.splitlines() if line.strip()]
    evs = evs[:2000]
    if not ingest_limit.allow(client_ip(req), max(1, len(evs))):
        raise HTTPException(429, "slow down: too many log lines this minute")
    src, dev = req.query_params.get("source"), req.query_params.get("device")
    for e in evs:
        if isinstance(e, dict):
            if src:
                e.setdefault("source", src)
            if dev:
                e.setdefault("device", dev)
    out = await ingest(evs)
    return {"ok": True, "received": len(out),
            "verdicts": [{"level": e["level_name"], "title": e["title"]} for e in out[-20:]]}


@app.post("/api/play", dependencies=[Depends(require_admin)])
async def play(scenario: str = "", speed: float = 1.0, loop: int = 0, noise: int = 0):
    sids = list(scenarios.load_library()) if scenario == "all" else [s for s in scenario.split(",") if s]
    await player.play(sids, speed=speed, loop=bool(loop), noise=bool(noise))
    return {"ok": True}


@app.post("/api/stop", dependencies=[Depends(require_admin)])
async def stop():
    await player.stop()
    return {"ok": True}


@app.post("/api/reset", dependencies=[Depends(require_admin)])
async def reset():
    await player.stop()
    async with engine_lock:
        engine.reset()
    await asyncio.to_thread(store.reset)
    broadcast({"type": "reset"})
    return {"ok": True}


@app.get("/api/export", dependencies=[Depends(require_admin)])
async def export():
    rows = await asyncio.to_thread(store.all_events)
    return Response(json.dumps(rows, indent=1), media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=logwatch-export.json"})


# ------------------------------------------------------------------- digest

def rules_digest(evs, title):
    if not evs:
        return f"### {title}\n\nNo logs yet."
    c = Counter(e["level"] for e in evs)
    worst = sorted([e for e in evs if e["level"] >= 2], key=lambda e: (-e["level"], e["ts"]))
    lines = [f"### {title}",
             f"**{len(evs)} log lines** read: {c[0]} normal, {c[1]} FYI, {c[2]} worth a look, {c[3]} act now.", ""]
    if not worst:
        lines.append("**Verdict:** nothing here looks worrying. This is ordinary day-to-day activity.")
        return "\n".join(lines)
    lines.append("**What stands out:**")
    seen = set()
    for e in worst:
        if e["title"] in seen:
            continue
        seen.add(e["title"])
        t = datetime.fromtimestamp(e["ts"]).strftime("%H:%M")
        lines.append(f"- **{e['level_name']}** ({t}, {e['device']}): {e['title']}. {e['plain']}")
        if len(seen) >= 7:
            break
    adv = []
    for e in worst:
        if e.get("advice") and e["advice"] not in adv:
            adv.append(e["advice"])
    lines += ["", "**What to do next:**"] + [f"{i}. {a}" for i, a in enumerate(adv[:5], 1)]
    return "\n".join(lines)


AI_PROMPT = """You are helping an ordinary, non-technical person understand logs pulled from their own device(s).
Read the raw logs below and answer in plain language (no jargon without a short explanation), under 250 words, using exactly these four headings:

**What's happening?**
**Is anything unusual?**
**Should I worry?** (start with one of: Normal / Worth a look / Act now)
**What should I do next?** (numbered, most important first)

Only claim what the logs actually show. If something is ambiguous, say so rather than guessing.

RAW LOGS:
{logs}"""


async def ai_digest(evs):
    logs = "\n".join(f"[{e['device']}] {e['raw']}" for e in evs[-150:])
    async with httpx.AsyncClient(timeout=90) as cx:
        r = await cx.post("https://api.anthropic.com/v1/messages",
                          headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json={"model": MODEL, "max_tokens": 1200,
                                "messages": [{"role": "user", "content": AI_PROMPT.format(logs=logs)}]})
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json().get("content", []))


@app.post("/api/digest", dependencies=[Depends(require_admin)])
async def digest(device: str = "", scenario: str = "", mode: str = "rules"):
    allv = await asyncio.to_thread(store.recent, 300, device or None, scenario or None)
    evs = [e for e in allv if not e.get("correlated")]
    title = device or (scenario and scenarios.load_library().get(scenario, {}).get("title")) or "All devices"
    if mode != "ai":
        return {"mode": "rules", "text": rules_digest(allv, title)}
    if not API_KEY:
        return {"mode": "rules", "note": "No ANTHROPIC_API_KEY set on the server - showing the rule-based digest.",
                "text": rules_digest(allv, title)}
    key = hashlib.sha1("\n".join(e["raw"] for e in evs[-150:]).encode()).hexdigest()
    cached = await asyncio.to_thread(store.ai_get, key)
    if cached:
        return {"mode": "ai", "note": "Saved answer (same logs as before).", "text": cached}
    try:
        text = await ai_digest(evs)
        await asyncio.to_thread(store.ai_put, key, text)
        return {"mode": "ai", "text": text}
    except Exception as ex:
        return {"mode": "rules", "note": f"AI unreachable ({type(ex).__name__}) - showing the rule-based digest.",
                "text": rules_digest(allv, title)}


@app.exception_handler(HTTPException)
async def http_err(_req, ex: HTTPException):
    return JSONResponse({"error": ex.detail}, status_code=ex.status_code)


# ------------------------------------------------------------------- optional: serve the front end too
# If the frontend folder sits next to backend/ (it does in this repo), Render serves it as well,
# so the whole app can run as one service. Netlify hosting is still the recommended setup.
FRONT = Path(__file__).resolve().parent.parent / "frontend"
if FRONT.is_dir():
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="frontend")
