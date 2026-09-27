"""
scenarios.py - the log library: loads sample_logs/*, plays them into the
dashboard at a watchable pace, and generates harmless background noise so the
screen looks alive between visitors.
"""
import json
import os
import random
import asyncio
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "sample_logs")


def _fill(line):
    now = datetime.now()
    return (line.replace("{DATE}", now.strftime("%Y-%m-%d"))
                .replace("{SYSLOGDATE}", now.strftime("%b %d").replace(" 0", "  ")))


def load_library():
    """Returns {id: {title, source, device, card, known, pace, lines, file}}."""
    out = {}
    if not os.path.isdir(LIB):
        return out
    for fn in sorted(os.listdir(LIB)):
        if fn.startswith(".") or not fn.endswith((".log", ".jsonl", ".txt")):
            continue
        meta = {"title": fn, "source": None, "device": None, "card": "", "known": [],
                "pace": 1.0, "lines": [], "file": fn}
        with open(os.path.join(LIB, fn), encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("#"):
                    if ":" in line:
                        k, v = line[1:].split(":", 1)
                        k, v = k.strip().lower(), v.strip()
                        if k == "known":
                            meta["known"] = v.lower().split()
                        elif k == "pace":
                            meta["pace"] = float(v)
                        elif k in meta:
                            meta[k] = v
                    continue
                if line.strip():
                    meta["lines"].append(line)
        out[os.path.splitext(fn)[0]] = meta
    return out


def to_event(line, meta, sid):
    line = _fill(line)
    ev = None
    if line.lstrip().startswith("{"):
        try:
            ev = json.loads(line)
        except ValueError:
            ev = None
    if ev is None:
        ev = {"raw": line}
    ev.setdefault("source", meta["source"])
    ev.setdefault("device", meta["device"])
    ev["scenario"] = sid
    return ev


class Player:
    """Plays scenarios / noise into an async ingest(list_of_events) coroutine."""

    def __init__(self, ingest, engine):
        self.ingest = ingest
        self.engine = engine
        self.task = None
        self.now_playing = None

    def busy(self):
        return self.task is not None and not self.task.done()

    async def stop(self):
        if self.busy():
            self.task.cancel()
            try:
                await self.task
            except (asyncio.CancelledError, Exception):
                pass
        self.task = None
        self.now_playing = None

    async def play(self, sids, speed=1.0, loop=False, noise=False):
        await self.stop()
        self.task = asyncio.create_task(self._run(sids, max(0.1, min(speed, 50)), loop, noise))

    async def _run(self, sids, speed, loop, noise):
        lib = load_library()
        try:
            while True:
                if noise and not sids:
                    self.now_playing = "Background activity"
                    await self.ingest([random_noise()])
                    await asyncio.sleep(random.uniform(1.5, 4.0) / speed)
                    continue
                for sid in sids:
                    meta = lib.get(sid)
                    if not meta:
                        continue
                    self.now_playing = meta["title"]
                    for mac in meta["known"]:
                        self.engine.known_macs[meta["device"]].add(mac)
                    for line in meta["lines"]:
                        await self.ingest([to_event(line, meta, sid)])
                        await asyncio.sleep(meta["pace"] / speed)
                        if noise and random.random() < 0.35:
                            await self.ingest([random_noise()])
                    await asyncio.sleep(3 / speed)
                if not loop:
                    break
        finally:
            self.now_playing = None


# ------------------------------------------------------------ background noise

def _t():
    return datetime.now().strftime("%H:%M:%S")


NOISE = [
    lambda: {"source": "router", "device": "Booth router (demo)",
             "raw": f"{datetime.now():%b %d} {_t()} router dnsmasq[812]: query[A] {random.choice(['www.google.com','api.spotify.com','netflix.com','weather.com','outlook.office365.com','i.instagram.com'])} from 192.168.8.{random.randint(20,60)}"},
    lambda: {"source": "router", "device": "Booth router (demo)",
             "raw": f"{datetime.now():%b %d} {_t()} router kernel: [DoS Attack: TCP Port Scan] from source: {random.choice(['162.142.125.10','45.33.32.156','198.51.100.77'])}, port {random.choice([22,23,80,443,8080])}"},
    lambda: {"source": "windows", "device": "Booth laptop (Windows)",
             "EventID": 4624, "TargetUserName": random.choice(["SYSTEM", "DWM-1", "UMFD-0"]), "LogonType": 5, "TimeCreated": datetime.now().isoformat(timespec="seconds")},
    lambda: {"source": "phone", "device": "Demo phone",
             "raw": f"{datetime.now():%Y-%m-%d} {_t()} app={random.choice(['Weather Now','Google Maps','Spotify','Instagram'])} permission={random.choice(['LOCATION','LOCATION','CAMERA'])} duration=2s"},
    lambda: {"source": "browser", "device": "Booth laptop (Chrome)",
             "raw": f"{datetime.now():%Y-%m-%d} {_t()} visit url=https://{random.choice(['www.wikipedia.org','news.ycombinator.com','www.youtube.com','docs.google.com','www.amazon.com','github.com'])}/"},
]


def random_noise():
    ev = random.choice(NOISE)()
    ev["scenario"] = "noise"
    return ev
