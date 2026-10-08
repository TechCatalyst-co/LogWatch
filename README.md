# LogWatch Cloud — "You vs. the Machine"

A hosted version of the LogWatch booth demo for CSF 2026 · *Connected lives, Protected futures*.

- **Frontend** (the big-screen dashboard + visitor phone page) → **Netlify**
- **Backend API** (log classifier, live stream, scenario player, AI digest) → **Render**
- **Database** → **MongoDB Atlas** (free M0 cluster is plenty)

> **Running the booth?** Students operating the demo should read the [TheLogWatch Operator's Guide](docs/USER_GUIDE.md).

```
 phones (QR code) ─────────────┐
 Windows PC (PowerShell) ──────┤  HTTPS + ingest key
 router / Pi ─UDP─► laptop relay ┤ ─────────────────►  Render: FastAPI  ◄──►  MongoDB Atlas
                                                         ▲   live stream (SSE)
                                   Netlify dashboard ────┘   operator login
```

---

## 1 · MongoDB Atlas (5 min)
1. Create a free account at mongodb.com/atlas → **Create cluster → M0 (free)**.
2. **Database Access** → add a user with a strong password (role: *Read and write to any database*).
3. **Network Access** → *Add IP address* → `0.0.0.0/0`. Render's free plan has no fixed outbound IP, so
   this is required; the strong DB password is what protects it.
4. **Connect → Drivers** → copy the `mongodb+srv://...` string and put your password in it.

LogWatch creates its collections and indexes on first start, including a TTL index that
**auto-deletes logs after 14 days** (`EVENT_TTL_DAYS`).

## 2 · Put the code on GitHub
Unzip, then create a new GitHub repo and push the whole `logwatch-cloud` folder. Both Render and
Netlify deploy from it.

## 3 · Render (backend)
1. render.com → **New + → Blueprint** → pick the repo. It reads `render.yaml`.
2. Fill in when asked:
   - `MONGODB_URI` → the Atlas string
   - `ADMIN_PASSWORD` → the booth operator password
   - `ALLOWED_ORIGINS` → leave `*` for now; you'll set it to the Netlify URL in step 5
   - `ANTHROPIC_API_KEY` → optional; enables **Ask AI**
   `SECRET_KEY` and `INGEST_KEY` are generated for you.
3. Deploy. Check `https://<your-service>.onrender.com/api/health` shows `"db":"ok"`.

> **Free plan sleeps after 15 minutes idle** and takes ~1 minute to wake. For event day, switch the
> service to **Starter** (a few dollars for the month) so the dashboard never stalls mid-round.

## 4 · Netlify (frontend)
1. app.netlify.com → **Add new site → Import from Git** → same repo. `netlify.toml` sets everything.
2. **Site configuration → Environment variables** → add `LOGWATCH_API` = your Render URL
   (e.g. `https://logwatch-api.onrender.com`, no trailing slash). Redeploy.
3. Optional: rename the site (e.g. `logwatch-csf.netlify.app`).

## 5 · Lock it down
In Render → Environment, set `ALLOWED_ORIGINS` to your Netlify URL (comma-separate several).
Open the Netlify site, sign in with `ADMIN_PASSWORD`, and you're live.

**One-service option:** the Render service also serves the dashboard itself at its own URL, so you can
skip Netlify entirely. Netlify is still nicer (fast CDN, custom domain, deploy previews).

---

## At the booth
- **Cases → Card / Play**, **Challenge mode** (`C`), **Ask AI**, **Reveal**, **Reset** work as in the
  offline version.
- **Connect devices & phones** (bottom-left) shows a **QR code** for visitors' phones and the exact
  commands for the relay and the Windows forwarder, pre-filled with your server and key.
- Routers and Raspberry Pis: run `forwarders/syslog_relay.py` on the booth laptop and point them at it.
  Details in `forwarders/README.md`.
- If a network blocks live streaming, the dashboard quietly falls back to refreshing every 3 seconds.

## Security model
| Who | Can do | How |
|---|---|---|
| Booth operator | everything (view, play, reset, AI, export) | `ADMIN_PASSWORD` → 12-hour signed token |
| Devices & phones | send logs only | `INGEST_KEY` (in the QR link / forwarder commands) |
| Anyone else | nothing, unless `PUBLIC_VIEW=true` (read-only dashboard) | — |

- Ingest is rate-limited per IP (1,500 lines/min) and capped at 1 MB per request; logins at 10/min.
- Log text is stored as a string and always HTML-escaped on screen; device-supplied JSON can't create
  database fields or operators.
- The phone page sends `no-referrer`, so the key in its link isn't leaked to other sites.
- **After the event:** rotate `INGEST_KEY` and `ADMIN_PASSWORD`, and **Reset** (or let the 14-day TTL clear it).

## Environment variables (Render)
| Variable | Required | Default | |
|---|---|---|---|
| `MONGODB_URI` | yes | — | Atlas connection string |
| `ADMIN_PASSWORD` | yes | — | operator login |
| `SECRET_KEY` | yes | generated | signs login tokens |
| `INGEST_KEY` | yes | generated | devices/phones send this |
| `ALLOWED_ORIGINS` | recommended | `*` | Netlify URL(s) |
| `ANTHROPIC_API_KEY` | no | — | enables Ask AI |
| `CLAUDE_MODEL` | no | `claude-sonnet-5` | |
| `EVENT_TTL_DAYS` | no | `14` | `0` keeps logs forever |
| `PUBLIC_VIEW` | no | `false` | read-only dashboard without login |
| `MONGODB_DB` | no | `logwatch` | |

## Run it locally
```bash
cd backend
pip install -r requirements-dev.txt
MONGODB_URI=mongomock:// ADMIN_PASSWORD=test INGEST_KEY=test uvicorn app:app --reload
```
Open http://localhost:8000 (the backend serves the frontend). `mongomock://` is an in-memory database
for testing; use your Atlas string to test against the real thing.

## Project layout
```
backend/            FastAPI app (Render)
  app.py            API, auth, live stream, AI digest
  classifier.py     rules that turn log lines into plain-English verdicts
  scenarios.py      case library player + background noise
  store.py          MongoDB collections, indexes, TTL
  sample_logs/      the four competition cases
frontend/           static site (Netlify)
  index.html        big-screen dashboard
  phone.html        visitor phone page
  config.js         API address (written by Netlify at build time)
forwarders/         syslog_relay.py, send_log.py, windows_forwarder.ps1, device setup
render.yaml         Render Blueprint
netlify.toml        Netlify build + security headers
```

---

## Answer key

The dashboard's own verdicts are rule-based and match this key. The point of the round is what the
**visitor** and the **AI** each catch. Each case has one thing only a human can get (it's on the card,
not in the logs) and one thing a machine is better at.

### Case 1 — "My Wi-Fi feels slow" (router)
- **What's happening:** an unknown Android device (`android-8f2c1d9e`, 192.168.1.57) joined at **2:03 AM** —
  not one of the family's five devices — and immediately opened port 51413 via UPnP for *Transmission*,
  a BitTorrent client, then contacted a torrent tracker. Someone has the Wi-Fi password and is
  downloading on it overnight → that's the slowness.
- **Separately:** an internet address (185.220.101.47) tried to log into the router admin page 6 times
  in 40 seconds → remote management is exposed.
- **Normal:** Dad's iPhone, the Samsung TV (`UN55TU7000-Living`) and the Xbox are known devices;
  the "DoS attack / port scan" lines are the firewall blocking internet background noise.
- **Do next:** change the Wi-Fi password (WPA2/WPA3), turn off remote management and UPnP,
  change the admin password, install the firmware update (current firmware is from 2019).
- **Human edge:** the card says nobody's up after midnight and lists the 5 devices — that's what makes
  the 2 AM Android an intruder. **Machine edge:** knowing 51413 = BitTorrent and that WAN-side admin logins mean exposed remote management.
- **Watch for:** the AI flagging the Samsung TV (odd hostname) or the "DoS Attack" lines as a real attack.

### Case 2 — "Is someone using my PC?" (Windows)
- **Normal:** the 3:03 AM sign-in and 7:14 AM sign-out. Maria works nights (card).
- **The attack (1:41–1:49 PM, while she's asleep):** 6 failed Remote Desktop logins from 185.220.101.47
  (4625, LogonType 10), then a **successful** RDP login as `maria` (4624) — the password was guessed.
  Then: a scheduled task disguised as `\Microsoft\Windows\UpdateCheck` running hidden, encoded PowerShell
  from AppData (4698, persistence) → a new account `support_admin` (4720) added to Administrators (4732,
  back door) → the security log cleared (1102, covering tracks).
- **Do next:** disconnect from the internet, turn off Remote Desktop, change Maria's password from another
  device, delete `support_admin` and the task, get the PC checked/reinstalled; change passwords used on it.
- **Human edge:** the 3 AM login looks alarming but is her shift. **Machine edge:** decoding event IDs
  and linking the chain in order.
- **Watch for:** the AI calling the 3 AM login suspicious (it can't know her schedule), or inventing what
  the encoded PowerShell does (the log doesn't show it).

### Case 3 — "Why is my battery dying overnight?" (phone)
- **The problem:** *Bright Flashlight Pro* turns on the **microphone every hour** (1:12, 2:12, 3:12, 4:12 AM,
  ~40 s each) and also grabbed location and **contacts**. A flashlight needs none of those. That's
  spyware-like behaviour and the battery drain.
- **Normal:** the flashlight using the **camera** at 10:48 PM (the LED *is* part of the camera);
  Weather Now checking location hourly; Snapchat/Maps during the evening.
- **Ambiguous (Worth a look):** Spotify touching the mic for 1 second at 3:33 AM — probably a voice
  feature/wake check, not proven either way.
- **Do next:** uninstall the flashlight app (the phone has one built in), review permissions in the Privacy
  Dashboard, set Weather to "only while using the app".
- **Human edge:** the card says it's a free flashlight app installed last week. **Machine edge:** spotting
  the exact hourly pattern.
- **Watch for:** the AI flagging the flashlight's camera use as malicious.

### Case 4 — "Did I get phished?" (browser)
- **What happened:** from Gmail, a `bit.ly` short link led to **paypa1.com** (digit 1, not letter l).
  Sam submitted email + password there, then was sent to `secure-paypal.com.account-verify.xyz` (the site
  really belongs to *account-verify.xyz*) and submitted **card number, expiry and CVV**, then downloaded
  `PayPal_Security_Update.exe` from the fake site. The real paypal.com visit afterwards is Sam checking.
- **Why saved passwords stopped working:** the .exe is most likely an info-stealer that took the browser's
  saved passwords/session cookies. (Likely, not proven by these logs alone.)
- **Do next:** don't run/delete the .exe, scan or reinstall the laptop, call the card issuer to cancel the card,
  change the PayPal password and every password saved in the browser *from a clean device*,
  turn on 2-step verification, sign out of all sessions.
- **Human edge:** the card explains the email and the "page just refreshed" trick. **Machine edge:**
  spotting `paypa1` vs `paypal` at a glance.
- **Normal:** YouTube, Amazon, accounts.google.com.
