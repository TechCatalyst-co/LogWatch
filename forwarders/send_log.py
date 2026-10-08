#!/usr/bin/env python3
"""
send_log.py - push logs from any machine into TheLogWatch over HTTP.

Examples
  # send a file once
  python3 send_log.py --server https://logwatch-api.onrender.com --key KEY --source router --device "Home router" router.log

  # follow a growing file (like tail -f)
  python3 send_log.py --server https://logwatch-api.onrender.com --key KEY --source linux --device "Raspberry Pi" -f /var/log/auth.log

  # pipe anything in
  adb logcat -v time | python3 send_log.py --server https://logwatch-api.onrender.com --key KEY --source phone --device "Pixel 8" -
  journalctl -f -o short | python3 send_log.py --server ... --source linux --device "Pi" -

Standard library only.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request


def post(server, lines, source, device, key):
    q = []
    if source:
        q.append("source=" + urllib.parse.quote(source))
    if device:
        q.append("device=" + urllib.parse.quote(device))
    req = urllib.request.Request(f"{server.rstrip('/')}/api/ingest?{'&'.join(q)}",
                                 data="\n".join(lines).encode(), method="POST",
                                 headers={"Content-Type": "text/plain", "X-Ingest-Key": key or ""})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="log file, or - for stdin")
    ap.add_argument("--server", required=True, help="e.g. https://logwatch-api.onrender.com")
    ap.add_argument("--source", choices=["router", "windows", "phone", "browser", "linux"])
    ap.add_argument("--device")
    ap.add_argument("--key", default="", help="the server's INGEST_KEY")
    ap.add_argument("-f", "--follow", action="store_true", help="keep reading new lines as they are written")
    ap.add_argument("--delay", type=float, default=0, help="seconds between lines (for a watchable replay)")
    a = ap.parse_args()

    f = sys.stdin if a.file == "-" else open(a.file, encoding="utf-8", errors="replace")
    if a.follow and f is not sys.stdin:
        f.seek(0, 2)
    batch, last = [], time.time()
    while True:
        line = f.readline()
        if line:
            line = line.rstrip("\n")
            if line.strip() and not line.startswith("#"):
                batch.append(line)
            if a.delay:
                post(a.server, batch, a.source, a.device, a.key)
                batch = []
                time.sleep(a.delay)
            elif len(batch) >= 200 or time.time() - last > 1:
                post(a.server, batch, a.source, a.device, a.key)
                batch, last = [], time.time()
            continue
        if batch:
            r = post(a.server, batch, a.source, a.device, a.key)
            print(f"sent {r.get('received')} lines", file=sys.stderr)
            batch, last = [], time.time()
        if not (a.follow or f is sys.stdin):
            break
        if f is sys.stdin and not line:
            break
        time.sleep(0.5)


if __name__ == "__main__":
    main()
