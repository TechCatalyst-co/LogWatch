#!/usr/bin/env python3
"""
syslog_relay.py - run this on the booth laptop.

Cloud hosts like Render only accept HTTPS, so routers and Raspberry Pis can't send
syslog to them directly. This relay listens for syslog on your local network and
forwards it securely to the TheLogWatch server.

  python3 syslog_relay.py --server https://logwatch-api.onrender.com --key YOUR_INGEST_KEY

Then point your router / Pi at THIS laptop's IP, UDP port 5514
(or run with --port 514 as admin/sudo if a device only sends to 514).

Name devices by IP in devices.json (same folder):  { "192.168.8.1": "Booth router" }
Standard library only.
"""
import argparse
import json
import os
import queue
import re
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request

PRI = re.compile(r"^<\d{1,3}>(\d\s)?")


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def sender(server, key, q):
    url = server.rstrip("/") + "/api/ingest"
    while True:
        batch = [q.get()]
        time.sleep(0.5)                              # gather a burst into one request
        while not q.empty() and len(batch) < 500:
            batch.append(q.get_nowait())
        body = json.dumps(batch).encode()
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, data=body, method="POST",
                                             headers={"Content-Type": "application/json", "X-Ingest-Key": key})
                with urllib.request.urlopen(req, timeout=60) as r:
                    res = json.loads(r.read())
                worst = max((v["level"] for v in res.get("verdicts", [])),
                            key=["Normal", "FYI", "Worth a look", "Act now"].index, default="-")
                print(f"{time.strftime('%H:%M:%S')}  sent {res.get('received')} lines  (worst: {worst})")
                break
            except Exception as ex:                  # server asleep / network blip: back off and retry
                wait = 2 ** attempt * 3
                print(f"  ! send failed ({ex}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
        else:
            print(f"  ! dropped {len(batch)} lines after 5 tries", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", required=True, help="TheLogWatch API, e.g. https://logwatch-api.onrender.com")
    ap.add_argument("--key", required=True, help="the server's INGEST_KEY")
    ap.add_argument("--port", type=int, default=5514)
    a = ap.parse_args()

    names = {}
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices.json")
    if os.path.exists(cfg):
        names = {k: v for k, v in json.load(open(cfg, encoding="utf-8")).items() if not k.startswith("_")}

    q = queue.Queue(maxsize=20000)
    threading.Thread(target=sender, args=(a.server, a.key, q), daemon=True).start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", a.port))
    print(f"Relay listening on udp://{lan_ip()}:{a.port}  ->  {a.server}\nPoint routers / Pis at that address. Ctrl+C to stop.")
    while True:
        data, (ip, _port) = sock.recvfrom(65535)
        for line in data.decode("utf-8", "replace").splitlines():
            line = PRI.sub("", line).strip()
            if not line:
                continue
            src = "linux" if re.search(r"\b(sshd|sudo|systemd)\b", line) else "router"
            try:
                q.put_nowait({"raw": line, "source": src, "device": names.get(ip, f"Router @ {ip}")})
            except queue.Full:
                pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nbye")
