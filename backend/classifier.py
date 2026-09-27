"""
classifier.py - turns raw device logs into plain-language verdicts.

Every event gets:
  level    0 = Normal, 1 = FYI, 2 = Worth a look, 3 = Act now
  category Network / Sign-in / Privacy / Web / System
  title    one-line plain-English headline
  plain    what it means, in words a non-expert understands
  advice   what to do next

Rules are deterministic on purpose: the dashboard's verdicts are the
"answer-key-style" baseline, and the optional AI digest (server.py) reads the
RAW logs independently so the two can be compared.
"""
import json
import re
import time
import ipaddress
from collections import defaultdict, deque
from datetime import datetime

LEVELS = ["Normal", "FYI", "Worth a look", "Act now"]

# --------------------------------------------------------------------- helpers

IP_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
MAC_RE = re.compile(r"\b([0-9a-f]{2}(?::[0-9a-f]{2}){5})\b", re.I)
TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2}):(\d{2})\b")
ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})")
EVENTID_RE = re.compile(r"\b(?:EventID|Event ID|event_id|Id)\s*[=:]\s*(\d{3,5})", re.I)
KV_RE = re.compile(r"(\w+)=(\"[^\"]*\"|[^\s]+(?:\s(?![\w]+=)[^\s=]+)*)")


def is_public_ip(ip):
    try:
        a = ipaddress.ip_address(ip)
        return not (a.is_private or a.is_loopback or a.is_link_local
                    or a.is_multicast or a.is_unspecified)
    except ValueError:
        return False


def first_public_ip(text):
    for ip in IP_RE.findall(text):
        if is_public_ip(ip):
            return ip
    return None


def parse_kv(text):
    """app=Bright Flashlight permission=MICROPHONE  ->  dict (values may contain spaces)."""
    out = {}
    for k, v in KV_RE.findall(text):
        out[k.lower()] = v.strip('"')
    return out


def log_time(ev, text):
    """Best-effort timestamp from the log itself; falls back to 'now'."""
    t = ev.get("time") or ev.get("timecreated") or ev.get("timestamp")
    now = datetime.now()
    if isinstance(t, (int, float)):
        return float(t) / (1000 if t > 1e12 else 1)
    if isinstance(t, str) and t:
        # PowerShell ConvertTo-Json date: /Date(1727413200000)/
        m = re.search(r"/Date\((\d+)", t)
        if m:
            return int(m.group(1)) / 1000
        m = ISO_RE.search(t)
        if m:
            return datetime(*map(int, m.groups())).timestamp()
        m = TIME_RE.search(t) or re.search(r"\b(\d{1,2}):(\d{2})\b", t)
        if m:
            g = list(map(int, m.groups())) + [0]
            return now.replace(hour=g[0], minute=g[1], second=g[2], microsecond=0).timestamp()
    m = ISO_RE.search(text)
    if m:
        return datetime(*map(int, m.groups())).timestamp()
    m = TIME_RE.search(text)
    if m:
        h, mi, s = map(int, m.groups())
        if h < 24:
            return now.replace(hour=h, minute=mi, second=s, microsecond=0).timestamp()
    return time.time()


def is_night(ts):
    return 0 <= datetime.fromtimestamp(ts).hour < 5


SOURCES = ("router", "windows", "phone", "browser", "linux")


def guess_source(text, hint=None):
    if hint in SOURCES:
        return hint
    t = text.lower()
    if EVENTID_RE.search(text) or "microsoft-windows" in t:
        return "windows"
    if "permission=" in t or "appops" in t:
        return "phone"
    if "url=" in t or re.search(r"https?://", t):
        return "browser"
    if "sshd" in t or "sudo" in t:
        return "linux"
    return "router"


# ------------------------------------------------------------- lookalike sites

BRANDS = ["paypal", "amazon", "google", "microsoft", "apple", "netflix", "chase",
          "bankofamerica", "wellsfargo", "facebook", "instagram", "outlook",
          "icloud", "venmo", "coinbase", "steam", "roblox", "discord", "usps", "fedex"]
HOMOGLYPH = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("3", "e"),
             ("5", "s"), ("4", "a"), ("7", "t"), ("@", "a")]


def _norm(label):
    s = label.lower()
    for a, b in HOMOGLYPH:
        s = s.replace(a, b)
    return s


def _lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_domain(host):
    """Return (level, brand, reason) or None."""
    host = host.lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) < 2:
        return None
    reg = labels[-2]                        # registrable label e.g. paypal in paypal.com
    for brand in BRANDS:
        if reg == brand:
            return None                     # the real thing
        if _norm(reg) == brand or (len(brand) >= 5 and _lev(reg, brand) == 1):
            return (3, brand, f"'{host}' is spelled to look like {brand}, but it is a different website")
        if any(brand in _norm(l) for l in labels[:-2]):
            return (3, brand, f"'{host}' puts '{brand}' at the front, but the site really belongs to '{'.'.join(labels[-2:])}'")
        if brand in _norm(reg) and reg != brand:
            return (2, brand, f"'{host}' uses the {brand} name but is not {brand}'s official site")
    return None


# ------------------------------------------------------------------ the engine

SIMPLE_APPS = ["flashlight", "torch", "calculator", "qr", "wallpaper", "solitaire",
               "sudoku", "ringtone", "battery saver", "cleaner", "compass", "level"]
EXPECTED = {
    "location": ["map", "weather", "uber", "lyft", "ride", "find my", "strava", "fitness", "doordash", "waze"],
    "camera": ["camera", "instagram", "snapchat", "zoom", "teams", "facetime", "whatsapp", "bank", "scanner", "tiktok"],
    "microphone": ["zoom", "teams", "phone", "whatsapp", "facetime", "voice", "recorder", "discord", "snapchat", "tiktok", "instagram"],
    "contacts": ["phone", "messages", "whatsapp", "signal", "mail", "gmail", "outlook", "contacts"],
    "sms": ["messages", "signal", "whatsapp"],
    "call_log": ["phone", "dialer"],
}
PERM_WORDS = {"mic": "microphone", "microphone": "microphone", "record_audio": "microphone",
              "camera": "camera", "location": "location", "fine_location": "location",
              "coarse_location": "location", "contacts": "contacts", "read_contacts": "contacts",
              "sms": "sms", "read_sms": "sms", "call_log": "call_log"}


class Engine:
    def __init__(self):
        self.on_new_device = None        # callback(device, mac) so the cloud app can persist it
        self.reset()

    def reset(self):
        self.known_macs = defaultdict(set)          # device -> macs seen
        self.fails = defaultdict(deque)             # (device, who) -> timestamps
        self.burst_alerted = {}                     # (device, who) -> ts of last alert

    # ---- public -------------------------------------------------------------
    def classify(self, ev):
        """ev: dict with at least 'raw'. Returns list of classified events
        (the event itself, plus any correlated alert it triggered)."""
        ev = {str(k).lower(): v for k, v in ev.items()}
        meta = ("source", "device", "scenario", "raw")
        if ev.get("raw"):
            raw = str(ev["raw"]).strip()
        elif set(ev) - {"message", "time", *meta}:
            raw = json.dumps({k: v for k, v in ev.items() if k not in meta})
        else:
            raw = str(ev.get("message") or "").strip()
        src = guess_source(raw, ev.get("source"))
        dev = ev.get("device") or {"router": "Home router", "windows": "Windows PC",
                                     "phone": "Phone", "browser": "Browser",
                                     "linux": "Linux box"}.get(src, "Device")
        ts = log_time(ev, raw)
        base = dict(source=src, device=dev, raw=raw[:2000], ts=ts, rx=time.time(),
                    scenario=ev.get("scenario"))
        fn = getattr(self, "_" + src, self._generic)
        extra = []
        verdict = fn(ev, raw, ts, dev, extra)
        base.update(verdict)
        base["level_name"] = LEVELS[base["level"]]
        out = [base]
        for x in extra:
            a = dict(base)
            a.update(x)
            a["level_name"] = LEVELS[a["level"]]
            a["correlated"] = True
            out.append(a)
        return out

    # ---- helpers --------------------------------------------------------------
    @staticmethod
    def v(level, category, title, plain, advice=""):
        return dict(level=level, category=category, title=title, plain=plain, advice=advice)

    def _track_fail(self, dev, who, ts, extra, what):
        q = self.fails[(dev, who)]
        q.append(ts)
        while q and ts - q[0] > 600:
            q.popleft()
        recent = sum(1 for t in q if ts - t <= 180)
        last = self.burst_alerted.get((dev, who), 0)
        if recent >= 5 and ts - last > 600:
            self.burst_alerted[(dev, who)] = ts
            extra.append(self.v(
                3, "Sign-in", f"Password-guessing attack on {what}",
                f"{recent} wrong passwords for '{who}' in under 3 minutes. People don't mistype that fast. "
                "This pattern is an automated tool trying passwords one after another.",
                "Use a long, unique password, turn on 2-step verification, and block remote sign-in if you don't need it."))

    def _fail_count(self, dev, who, ts):
        return sum(1 for t in self.fails.get((dev, who), ()) if ts - t <= 600)

    # ---- router -------------------------------------------------------------
    def _router(self, ev, raw, ts, dev, extra):
        t = raw.lower()
        pub = first_public_ip(raw)
        if "dhcpack" in t or "dhcp ack" in t or "assigned" in t and "dhcp" in t:
            mm = MAC_RE.search(raw)
            mac = mm.group(1) if mm else None
            tail = raw[mm.end():].split() if mm else []
            host = tail[0] if tail else "unknown"
            if mac and host.lower() == mac.lower():
                host = "no name"
            key = (mac or raw).lower()
            if key in self.known_macs[dev]:
                return self.v(0, "Network", f"{host} renewed its connection",
                              "A device that's already on your network checked in again. Routine.")
            self.known_macs[dev].add(key)
            if self.on_new_device:
                self.on_new_device(dev, key)
            if is_night(ts):
                return self.v(2, "Network", f"New device joined overnight: {host}",
                              f"A device you haven't seen before ({host}, hardware ID {mac}) joined your Wi-Fi in the middle of the night.",
                              "Check your router's device list. If you don't recognise it, change your Wi-Fi password and kick it off.")
            return self.v(1, "Network", f"New device joined: {host}",
                          f"A device named '{host}' connected to your Wi-Fi for the first time.",
                          "Usually a guest's phone or a new gadget. Worth a glance if you don't recognise the name.")
        if re.search(r"(bad password|login fail|failed login|authentication fail|admin login failure|invalid password)", t):
            who = (re.search(r"for '?(\w+)'?", raw) or [None, "admin"])[1]
            if pub:
                self._track_fail(dev, "router-admin", ts, extra, "your router")
                return self.v(3, "Sign-in", "Someone on the internet tried to log into your router",
                              f"A computer at {pub}, outside your home, tried to sign into your router's settings page as '{who}' and got the password wrong.",
                              "Turn OFF 'remote management' in your router settings and change the admin password from the default.")
            self._track_fail(dev, "router-admin", ts, extra, "your router")
            return self.v(1, "Sign-in", "Wrong router password typed at home",
                          "Someone on your own network typed the router's admin password wrong. Often just a typo.")
        if re.search(r"(admin login success|login successful|accepted password|luci: accepted login)", t):
            if pub:
                return self.v(3, "Sign-in", "Router settings opened from the internet",
                              f"Someone at {pub}, outside your home, successfully logged into your router.",
                              "If this wasn't you: change the admin password now, turn off remote management, and update the firmware.")
            return self.v(0, "Sign-in", "Router settings opened from inside the home",
                          "Someone at home logged into the router's settings page.")
        if re.search(r"(dos attack|syn.?flood|port ?scan|scan\]|ping of death)", t):
            return self.v(1, "Network", "Internet background noise blocked",
                          f"An outside computer{(' at ' + pub) if pub else ''} poked at your connection and your router's firewall blocked it. "
                          "Every internet connection gets thousands of these a day.",
                          "Nothing to do; this is your firewall doing its job.")
        if "upnp" in t or "addentry" in t or "add_nat_rule" in t:
            inside = [ip for ip in IP_RE.findall(raw) if not is_public_ip(ip)]
            return self.v(2, "Network", "A device opened a door to the internet",
                          f"A device{(' at ' + inside[0]) if inside else ''} asked the router (via UPnP) to let outside traffic straight in. "
                          "Game consoles do this legitimately; malware does it too.",
                          "Find which device it is. If it's not a console or something you set up, turn off UPnP.")
        if re.search(r"(firmware|upgrade|update available)", t):
            return self.v(1, "System", "Router firmware notice",
                          "The router is talking about a software update.",
                          "Install router updates; old router software is one of the most common ways homes get hacked.")
        if re.search(r"(dns|dnsmasq).*(query|forwarded|reply)", t):
            return self.v(0, "Network", "Website address lookup",
                          "A device asked 'where is this website?'. Totally routine; happens constantly.")
        if re.search(r"(wan|pppoe|link).*(up|connected)", t):
            return self.v(0, "Network", "Internet connection up", "The router connected to your internet provider.")
        if re.search(r"(disassoc|deauth|disconnected)", t):
            return self.v(0, "Network", "A device left the Wi-Fi", "A device disconnected. Normal when people leave or phones sleep.")
        return self.v(0, "Network", "Routine router activity", "Everyday housekeeping from your router.")

    # ---- windows ------------------------------------------------------------
    def _windows(self, ev, raw, ts, dev, extra):
        eid = ev.get("eventid") or ev.get("EventID") or ev.get("id")
        if not eid:
            m = EVENTID_RE.search(raw)
            eid = m.group(1) if m else None
        try:
            eid = int(eid)
        except (TypeError, ValueError):
            eid = None
        kv = parse_kv(raw)
        user = ev.get("targetusername") or ev.get("TargetUserName") or kv.get("user") or kv.get("targetusername") or "someone"
        ip = ev.get("ipaddress") or ev.get("IpAddress") or kv.get("ip") or kv.get("sourceip") or ""
        ltype = str(ev.get("logontype") or ev.get("LogonType") or kv.get("logontype") or "")
        where = "over the network" if ltype in ("3", "10") else "at the keyboard" if ltype == "2" else ""
        remote = ip and is_public_ip(ip)

        if eid == 4625:
            self._track_fail(dev, user, ts, extra, f"'{user}' on {dev}")
            lvl = 2 if remote or ltype == "10" else 1
            return self.v(lvl, "Sign-in", f"Wrong password for '{user}'",
                          f"A sign-in to '{user}' failed{(' from ' + ip) if ip else ''}{(' ' + where) if where else ''}. "
                          "One or two is a typo. Lots in a row is not.",
                          "Watch for repeats. If it keeps happening, change the password.")
        if eid == 4624:
            n = self._fail_count(dev, user, ts)
            if n >= 3:
                extra.append(self.v(
                    3, "Sign-in", f"'{user}' signed in right after {n} failed tries",
                    "Several wrong passwords, then a correct one. Either someone finally remembered it... or someone finally guessed it.",
                    "If this wasn't you: disconnect from the internet, change the password from a different device, and check for new accounts or programs."))
                self.fails[(dev, user)].clear()
            if ltype == "10" and remote:
                return self.v(3, "Sign-in", f"Remote Desktop login from the internet as '{user}'",
                              f"Someone connected to this PC over Remote Desktop from {ip}, outside your home.",
                              "If you didn't set this up, turn off Remote Desktop and change the password.")
            if user.endswith("$") or user.upper() in ("SYSTEM", "LOCAL SERVICE", "NETWORK SERVICE", "DWM-1", "UMFD-0"):
                return self.v(0, "Sign-in", "Windows signed in its own services", "Windows' own background accounts logging in. Normal.")
            return self.v(0, "Sign-in", f"'{user}' signed in", f"A successful sign-in to '{user}'{(' ' + where) if where else ''}.")
        if eid == 4698:
            task = ev.get("taskname") or kv.get("taskname") or kv.get("task") or "a task"
            odd = bool(re.search(r"(appdata|temp|\\users\\public|powershell|-enc|\.vbs|\.js\b|http)", raw, re.I))
            return self.v(3 if odd else 2, "System", f"New scheduled task: {task}",
                          "Something set up a program to run automatically on a schedule. " +
                          ("It points at a hidden or temporary folder / encoded script, a classic trick malware uses to survive a reboot." if odd
                           else "Software updaters do this legitimately."),
                          "Open Task Scheduler and look it up. If you don't recognise it, disable it and run a malware scan.")
        if eid == 4720:
            new = ev.get("targetusername") or kv.get("newaccount") or kv.get("targetusername") or user
            return self.v(3, "Sign-in", f"New user account created: '{new}'",
                          "Someone added a brand-new account to this PC. Attackers do this to keep a back door.",
                          "If nobody in your home created it, delete the account and change your passwords.")
        if eid in (4732, 4728):
            return self.v(3, "Sign-in", "An account was made an administrator",
                          "An account was given full control of this PC.",
                          "Make sure you know who did this and why.")
        if eid == 1102:
            return self.v(3, "System", "The security log was wiped",
                          "Someone erased this PC's security history. Legit users almost never do this; intruders do it to cover their tracks.",
                          "Treat the PC as compromised: disconnect it and get help.")
        if eid == 7045:
            return self.v(2, "System", "New background service installed",
                          "A program installed itself to run silently in the background every time the PC starts.",
                          "Fine if you just installed software. If not, look it up.")
        if eid in (1116, 1117):
            return self.v(3, "System", "Windows Security found malware",
                          "Microsoft Defender detected something malicious" + (" and removed it." if eid == 1117 else "."),
                          "Run a full scan and change passwords you've typed on this PC recently.")
        if eid == 4740:
            return self.v(2, "Sign-in", f"Account '{user}' locked out", "Too many wrong passwords locked the account.",
                          "If you didn't cause it, someone may be guessing the password.")
        if eid in (4634, 4647):
            return self.v(0, "Sign-in", f"'{user}' signed out", "Someone signed out. Normal.")
        if eid in (6005, 6006, 1074, 12, 13):
            return self.v(0, "System", "PC started or shut down", "Normal power on/off record.")
        return self.v(0, "System", f"Windows event {eid or ''}".strip(), "Routine Windows record.")

    # ---- phone --------------------------------------------------------------
    def _phone(self, ev, raw, ts, dev, extra):
        kv = parse_kv(raw)
        app = ev.get("app") or kv.get("app") or kv.get("package") or "An app"
        perm_raw = (ev.get("permission") or kv.get("permission") or kv.get("op") or "").lower()
        perm = PERM_WORDS.get(perm_raw.split(".")[-1].replace("android.permission.", ""), perm_raw)
        a = app.lower()
        if not perm:
            return self.v(0, "Privacy", f"{app} activity", "Routine app activity.")
        night = is_night(ts)
        if perm == "camera" and any(s in a for s in ("flashlight", "torch")):
            return self.v(0, "Privacy", f"{app} used the camera",
                          "Expected: the flashlight LED is part of the camera, so flashlight apps need camera access to switch it on.")
        if any(s in a for s in SIMPLE_APPS) and perm in ("microphone", "camera", "contacts", "sms", "call_log", "location"):
            return self.v(3, "Privacy", f"{app} used your {perm}",
                          f"A {app} has no reason to need your {perm}." +
                          (" And it did it overnight while the phone was idle." if night else ""),
                          f"Revoke the {perm} permission (Settings > Privacy > Permission manager) or uninstall the app.")
        if any(s in a for s in EXPECTED.get(perm, [])):
            return self.v(0, "Privacy", f"{app} used {perm}", f"Expected: {app} needs {perm} to work.",
                          "Consider 'Only while using the app' instead of 'Always'." if perm == "location" else "")
        if night and perm in ("microphone", "camera"):
            return self.v(2, "Privacy", f"{app} used your {perm} overnight",
                          f"{app} accessed the {perm} between midnight and 5 AM.",
                          "Check whether that makes sense for this app. If not, revoke the permission.")
        return self.v(1, "Privacy", f"{app} used {perm}", f"{app} accessed your {perm}.",
                      "Ask: does this app need that to do its job?")

    # ---- browser ------------------------------------------------------------
    def _browser(self, ev, raw, ts, dev, extra):
        m = re.search(r"https?://([^/\s:\"']+)", raw) or re.search(r"(?:url|host|domain)=([^\s/]+)", raw)
        host = (ev.get("host") or (m.group(1) if m else "")).lower()
        t = raw.lower()
        hit = check_domain(host) if host else None
        if re.search(r"\.(exe|scr|msi|bat|vbs|js|apk|iso)\b", t) and ("download" in t or "saved" in t):
            f = re.search(r"([\w\-.]+\.(?:exe|scr|msi|bat|vbs|js|apk|iso))\b", raw, re.I)
            name = f.group(1) if f else "a file"
            if hit:
                return self.v(3, "Web", f"Program downloaded from a fake site: {name}",
                              f"A runnable file came from {host}, which is pretending to be {hit[1]}. This is how info-stealing malware gets installed.",
                              "Do NOT open it. Delete it, run a malware scan, and change passwords saved in this browser.")
            return self.v(2, "Web", f"Program downloaded: {name}",
                          "A file that can run code was downloaded.",
                          "Only open it if you trust exactly where it came from.")
        if hit:
            lvl, brand, why = hit
            sub = "form_submit" in t or "post" in t.split()
            return self.v(lvl, "Web", ("Typed into a lookalike site: " if sub else "Lookalike website: ") + host,
                          f"{why}. " + ("Something was typed and submitted on that page, likely a password. " if sub else "") +
                          "This is how phishing works: a copy of a real login page on a fake address.",
                          f"If you typed a password there, change your {brand} password now and turn on 2-step verification.")
        if re.search(r"(bit\.ly|tinyurl|t\.co|is\.gd|rb\.gy)", t):
            return self.v(1, "Web", "Shortened link opened", "A short link hides the real destination until you click it.")
        if host.endswith((".zip", ".mov", ".xyz", ".top", ".click", ".cam")):
            return self.v(1, "Web", f"Unusual web address: {host}", "Domains on this ending are often used for throwaway scam sites.")
        return self.v(0, "Web", f"Visited {host or 'a website'}", "Ordinary browsing.")

    # ---- linux / raspberry pi ----------------------------------------------
    def _linux(self, ev, raw, ts, dev, extra):
        t = raw.lower()
        m = re.search(r"(?:failed password|invalid user)(?: for)?(?: invalid user)? (\S+)", t)
        if m:
            who = m.group(1)
            self._track_fail(dev, who, ts, extra, f"'{who}' on {dev}")
            pub = first_public_ip(raw)
            return self.v(2 if pub else 1, "Sign-in", f"Failed SSH login for '{who}'",
                          f"A remote login attempt failed{(' from ' + pub + ' on the internet') if pub else ''}.",
                          "Use SSH keys instead of passwords and don't expose SSH to the internet.")
        if "accepted" in t and "ssh" in t:
            who = (re.search(r"for (\S+)", raw) or [None, "someone"])[1]
            n = self._fail_count(dev, who, ts)
            if n >= 3:
                extra.append(self.v(3, "Sign-in", f"SSH login succeeded after {n} failures",
                                    "Several wrong passwords, then a correct one.",
                                    "If this wasn't you, change the password and check for new users or cron jobs."))
            return self.v(0, "Sign-in", f"SSH login: {who}", "A successful remote login.")
        if "sudo" in t:
            return self.v(0, "System", "Admin command run", "Someone ran a command with admin rights (sudo).")
        return self.v(0, "System", "Routine system activity", "Everyday housekeeping.")

    def _generic(self, ev, raw, ts, dev, extra):
        return self.v(0, "System", "Log received", "A log line we don't have a rule for yet.")
