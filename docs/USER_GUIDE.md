# TheLogWatch: Student Operator's Guide

**"You vs. the Machine"** · CSF 2026 · *Connected lives, Protected futures*

This guide is for students running the booth. You don't need to know how the platform is deployed
(that's in the main [README](../README.md)). Read sections 1–6 before your shift. Sections 7–9 are
for when something unusual happens. **Section 11 is the answer key, so don't show it to visitors.**

---

## Contents
1. [What is TheLogWatch?](#1--what-is-thelogwatch)
2. [Key ideas in 2 minutes](#2--key-ideas-in-2-minutes)
3. [Before your shift: checklist](#3--before-your-shift-checklist)
4. [Tour of the dashboard](#4--tour-of-the-dashboard)
5. [Button reference](#5--button-reference)
6. [Running a competition round](#6--running-a-competition-round)
7. [Letting visitors send from their phones](#7--letting-visitors-send-from-their-phones)
8. [Connecting live devices (optional)](#8--connecting-live-devices-optional)
9. [Troubleshooting](#9--troubleshooting)
10. [Privacy and conduct](#10--privacy-and-conduct)
11. [Answer key (operators only)](#11--answer-key-operators-only)

---

## 1 · What is TheLogWatch?

Every router, PC, phone and browser keeps a diary of what it does. These diaries are called **logs**.
They are full of useful clues, but they're written in a language almost nobody reads.

TheLogWatch reads those logs as they arrive and translates each line into plain English. It gives every
line a verdict ("Normal", "Act now" and so on) and shows everything live on a big-screen dashboard.

At the booth, we turn this into a game. A visitor gets a short story about a person with a tech worry
(the **case card**) plus that person's logs. The visitor tries to work out what's going on.
Then we ask an **AI** to read the same logs, and compare. The lesson: **humans and machines each catch
things the other misses.**

```
 visitors' phones (QR code) ──────────┐
 Windows PC (forwarder script) ───────┤   internet (HTTPS)
 router / Raspberry Pi ─► booth laptop ┤ ───────────────────►  TheLogWatch server  ──►  database
                                       │                              │
 built-in case library ────────────────┘                              ▼
                                                           big-screen dashboard (you)
```

Most rounds use the **built-in case library**, which has four prepared stories. Live devices and phones are
extras that make the booth feel real.

---

## 2 · Key ideas in 2 minutes

### The four verdict levels
Every log line gets one of these. The colours and icons match the dashboard.

| Level | Means | Example |
|---|---|---|
| **Normal** | Everyday housekeeping. Ignore it. | A known phone gets an IP address |
| **FYI** | Worth knowing, not a problem by itself | A new app used your location once |
| **Worth a look** | Odd, but may have an innocent reason | A login at 3 AM |
| **Act now** | Do something about this today | Someone created a new admin account |

### PATTERN
When the system links several lines into one story, the line gets a **PATTERN** tag. For example:
"6 failed logins, then a successful one" means the password was guessed. Single lines can look harmless.
Patterns are where the real attacks show up.

### Human edge vs. machine edge
This is the whole point of the demo, so say it out loud to visitors:
- **Humans know the context.** Only you know that Maria works nights, or that nobody in the house is
  up after midnight. That information is on the case card, *not* in the logs.
- **Machines know the details.** They know that port 51413 means BitTorrent, they can decode Windows
  event numbers, and they spot `paypa1.com` vs `paypal.com` instantly.
- **The AI is sometimes confidently wrong.** It only sees the logs, so it can't know the person's
  schedule. When it gets something wrong, that's a teaching moment, not a bug.

---

## 3 · Before your shift: checklist

- [ ] Get the **dashboard address** and the **operator password** from your team lead.
- [ ] Open the dashboard **about a minute before** you need it. If the server has been idle, it can take
      up to a minute to wake up. You may see *"Offline · can't reach the server, retrying…"* until then.
- [ ] Sign in at **Booth operator sign-in** with the operator password. Your sign-in lasts 12 hours on that browser.
- [ ] Check that the **clock in the top-right is ticking** and the dot next to it is lit. This means the live feed is connected.
- [ ] Press **Reset** for a clean screen. You'll be asked to confirm, because Reset deletes *all* logs.
- [ ] Put the browser in full screen (F11 on Windows, Ctrl+Cmd+F on Mac).
- [ ] Have paper scorecards and pens ready for visitors.
- [ ] Optional: turn on **Background** or **Play all** so the screen looks alive while people walk past.

---

## 4 · Tour of the dashboard

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ LogWatch · You vs. the Machine   [status]   Cases Background Challenge Digest AI ...  ●│ ← top bar
├───────────────────────────────────────────────────────────────────────────────────────┤
│ Logs read │ Devices reporting │ Normal │ Worth a look │ Act now                        │ ← KPI tiles
├──────────────┬───────────────────────────────────────┬────────────────────────────────┤
│ Devices      │ Live log feed   [filters]             │ What to do next                │
│              │                                       │                                │
│              │                                       ├────────────────────────────────┤
│ [Connect     │                                       │ Activity · last 10 min         │
│  devices &   │                                       │ By category                    │
│  phones]     │                                       │                                │
└──────────────┴───────────────────────────────────────┴────────────────────────────────┘
```

> The on-screen title currently says **LogWatch**. It's the same platform.

**Status (top bar).** Shows what's feeding the dashboard right now. *Idle · waiting for logs* means
nothing is playing. While a case plays, its name appears here.

**KPI tiles.** Running totals: how many lines have been read, how many devices are reporting, and how many
lines fall into each verdict level. The **Act now** tile lights up when there's at least one.

**Devices (left).** Every router, PC, phone or browser that has sent logs, with an icon for its worst
verdict so far. **Click a device** to show only its logs. Click it again (or the ✕ chip in the feed
filters) to show everything.

**Live log feed (centre).** The newest lines are at the top. Each row shows the time, a verdict chip, a
short title, the device, and the plain-English explanation.
- **Click a row** to expand it. You'll see the **raw log line** and the advice (→).
- **Filters:** *All*, *Worth a look +* (hides Normal/FYI, which is great for spotting trouble fast), or one source
  (Router, Windows, Phone, Browser…).

**What to do next (right).** The important findings rolled up into actions, e.g. "Change the Wi-Fi
password". In a round, this is the "answer" the visitor's scorecard is compared to.

**Activity · last 10 min / By category.** A timeline of log volume coloured by verdict, plus a breakdown
by category. Hover over them for details.

---

## 5 · Button reference

| Button | What it does | When to use it |
|---|---|---|
| **Cases** | Opens the case library: each case has **Card** (read the story) and **Play** (stream its logs). Also **Play all**, which loops all cases. | Start of every round |
| **Background** | Toggles harmless fake traffic (web visits, DNS lookups, routine logins) | Between visitors, so the screen isn't empty |
| **Challenge mode** (or press **C**) | Hides the verdicts. Rows show **raw logs only** and the right-hand panels are covered. A yellow banner appears. | Before playing a case for a visitor |
| **Reveal answers** (in the yellow banner) | Turns Challenge mode off and shows all verdicts | After the visitor finishes their scorecard |
| **Digest** | Summary written by the platform's own rules | Quick recap of what was found |
| **Ask AI** | Sends the **raw logs only** to an AI. The AI never sees the case card or the dashboard's verdicts. Its answer appears in a pop-up. | The "vs. the Machine" moment |
| **Stop** | Stops whatever is playing (a case, Play all, or Background) | Pause or end a round |
| **Reset** | **Deletes all logs** from the database, after you confirm | Between visitor groups |
| **Connect devices & phones** | Shows the QR code for phones, plus commands for live devices. Also contains **Sign out** and **Download all logs (JSON)**. | See sections 7 and 8 |
| **Esc** key | Closes any pop-up | |

---

## 6 · Running a competition round

A round takes about 5–8 minutes per visitor or small group.

1. **Reset.** Press **Reset** and confirm, so only this round's logs are on screen.
   Turn off **Background** if it's on.
2. **Pick a case.** Press **Cases**. Choose one of the four (or let the visitor pick a worry that sounds
   familiar).
3. **Read the card.** Press **Card**. Read the story aloud or let the visitor read it. This is the
   context that only a human gets. Don't press "Play these logs" yet.
4. **Hide the answers.** Close the pop-up and press **Challenge mode** (or **C**). You'll see the yellow
   banner: *"Challenge mode: verdicts are hidden."*
5. **Play the logs.** Go back to **Cases → Play** for that case. Lines appear one by one, as raw logs.
6. **Visitor investigates.** They fill in the scorecard: *What's happening? What's normal? What should
   this person do?* Help them read the lines, but don't give away the answer. Good hints:
   - "What time did that happen? Who was awake then?"
   - "Is that a device you recognise from the card?"
   - "Look very carefully at that web address."
7. **Ask the machine.** Press **Ask AI**. Read the AI's answer together. Did it catch the same things?
   Did it flag something that the card explains as normal?
8. **Reveal.** Press **Reveal answers**. Walk through the **What to do next** panel and the feed.
   Use the [answer key](#11--answer-key-operators-only) to score.
9. **Close the loop.** Ask: *"What did you catch that the AI couldn't, and what did the AI catch
   that you missed?"* Then give one practical takeaway, like "turn on 2-step verification" or "check your
   phone's privacy dashboard".
10. **Between visitors:** press **Stop**, then **Cases → Play all** (loops every case) or **Background**,
    so the screen stays alive.

**Tips**
- The **Worth a look +** filter is handy during the reveal, because it hides the noise.
- Click any row to show its raw log line next to the translation.
- Short on time? Skip Ask AI and just Reveal. Busy queue? Run the same case for a group of 3–4.

---

## 7 · Letting visitors send from their phones

This works well as a hook while someone is waiting in line.

1. Press **Connect devices & phones**. A **QR code** appears.
2. The visitor scans it and opens the page **"Send a log to the big screen"**.
3. **Option 1: check your phone's privacy log.** The page explains where to find it:
   - *Android 12+:* Settings → Security & privacy → Privacy → **Privacy dashboard**
   - *iPhone:* Settings → Privacy & Security → **App Privacy Report** (it must be turned on, and it fills in over several days)

   They then pick **which app**, **which permission** (Location, Microphone, Camera, Contacts,
   Messages, Call log) and **when** (Recently / Overnight 2 AM), and tap **Send to the dashboard**.
   Their entry appears in the live feed with a verdict. A flashlight app using the microphone overnight will
   light up red.
4. **Option 2: paste any log (advanced).** Visitors can paste lines copied from a router page,
   Windows Event Viewer or a Raspberry Pi.

**Reassure visitors:** nothing is read from their phone automatically. They choose exactly what to
send, and their first name is optional.

---

## 8 · Connecting live devices (optional)

Only do this if your team lead has set it up and you're comfortable. Full instructions are in
[`forwarders/README.md`](../forwarders/README.md). The **Connect devices & phones** pop-up shows the exact
commands with the server address and key already filled in.

| Device | How it connects |
|---|---|
| **Router / Raspberry Pi** | They send logs on the local network, so run the relay on the booth laptop: `python3 syslog_relay.py --server … --key …`, then point the router's "remote syslog server" at the laptop's IP |
| **Windows PC** | Admin PowerShell: `.\windows_forwarder.ps1 -Server … -Key …` |
| **Anything else** | The `curl` command shown in the pop-up uploads a log file |

**"Live moments" that make great demos:**
- Join a new phone to the booth router's Wi-Fi, so a new device appears.
- Type the router admin password wrong 5 times, or the Windows lock-screen password a few times.
- On the Windows PC: `net user demo_intruder P@ssw0rd123! /add` creates a new account and triggers an alert.
  **Always clean up afterwards:** `net user demo_intruder /delete`.

---

## 9 · Troubleshooting

| What you see | What it means / what to do |
|---|---|
| *"Offline · can't reach the server, retrying…"* | The server is waking up (up to ~1 min) or the Wi-Fi dropped. Wait. The page retries by itself. |
| Sign-in says *"too many attempts, wait a minute"* | Too many wrong passwords. Wait 60 seconds and check the password with your lead. |
| Sign-in says the server has no ADMIN_PASSWORD | Setup problem. Tell your team lead. |
| Feed updates in jumps instead of smoothly | The venue network is blocking live streaming. The dashboard switches to refreshing every 3 seconds on its own. This is fine. |
| QR box says *"QR code needs internet"* | The laptop is offline. Reconnect, then reopen the pop-up. |
| Pop-up says *"No INGEST_KEY is set on the server"* | Phones and devices can't send yet. Tell your team lead. |
| **Ask AI** shows *"No ANTHROPIC_API_KEY set… showing the rule-based digest"* | The AI isn't configured. Use the rule-based Digest and the answer key instead, and tell your lead. |
| Phone page says to slow down | Too many lines were sent too quickly from one network. Wait a minute. |
| Nothing happens when I press Play | Check the status in the top bar. Press **Stop**, then **Play** again. If the clock isn't ticking, reload the page. |
| Screen is full of old logs | Press **Reset** (and confirm). |
| The AI said something wrong | This is expected. Use it in the discussion: *"Why couldn't it know that?"* |

If you're stuck, reload the page. You'll stay signed in for 12 hours.

---

## 10 · Privacy and conduct

- **Don't share** the operator password, the QR link or the key shown in the Connect pop-up with anyone
  away from the booth. The QR link contains a key that lets people send logs.
- Visitors only send what they choose. Even so, **press Reset** if someone sent something personal, and
  between groups.
- Logs delete themselves after 14 days, and the team lead changes all keys and passwords after the event.
- Never connect a visitor's device with a forwarder or relay. Visitors only use the phone page.
- Keep it friendly. The goal is for visitors to leave knowing **one thing they can check on their own
  devices tonight**.

---

## 11 · Answer key (operators only)

> **⚠ Spoilers. Don't show this section to visitors.** The dashboard's verdicts match this key.
> Each case has one thing only a human can get (it's on the card, not in the logs) and one thing a machine
> is better at.

### Case 1: "My Wi-Fi feels slow" (router)
- **What's happening:** an unknown Android device (`android-8f2c1d9e`, 192.168.1.57) joined at
  **2:03 AM**. It's not one of the family's five devices. It immediately opened port **51413** via UPnP for
  *Transmission*, a BitTorrent client, and contacted a torrent tracker. Someone has the Wi-Fi password and
  is downloading overnight, which is why the Wi-Fi is slow.
- **Separately:** an internet address (185.220.101.47) tried to log into the router admin page 6 times in
  40 seconds, which means remote management is exposed.
- **Normal:** Dad's iPhone, the Samsung TV (`UN55TU7000-Living`) and the Xbox are known devices. The
  "DoS attack / port scan" lines are the firewall blocking everyday internet noise.
- **Do next:** change the Wi-Fi password (WPA2/WPA3), turn off remote management and UPnP, change the
  admin password, and install the firmware update (the current firmware is from 2019).
- **Human edge:** the card says nobody is up after midnight and lists the 5 devices.
  **Machine edge:** knowing that 51413 means BitTorrent and that admin logins from the internet mean exposed remote management.
- **Watch for:** the AI flagging the Samsung TV (odd name) or the "DoS Attack" lines as a real attack.

### Case 2: "Is someone using my PC?" (Windows)
- **Normal:** the 3:03 AM sign-in and 7:14 AM sign-out. Maria works nights (see the card).
- **The attack (1:41–1:49 PM, while she's asleep):** 6 failed Remote Desktop logins from
  185.220.101.47, then a **successful** login as `maria`, meaning her password was guessed. Next comes a hidden
  scheduled task disguised as `\Microsoft\Windows\UpdateCheck` (persistence). Then a new account `support_admin`
  is created and added to Administrators (a back door). Finally the security log is cleared (covering tracks).
- **Do next:** disconnect from the internet, turn off Remote Desktop, change Maria's password from
  another device, delete `support_admin` and the task, get the PC checked or reinstalled, and change passwords
  used on it.
- **Human edge:** the 3 AM login looks alarming but is just her shift. **Machine edge:** decoding
  event IDs and linking the chain in order.
- **Watch for:** the AI calling the 3 AM login suspicious (it can't know her schedule), or inventing what
  the encoded PowerShell does (the log doesn't show it).

### Case 3: "Why is my battery dying overnight?" (phone)
- **The problem:** *Bright Flashlight Pro* turns on the **microphone every hour** (1:12, 2:12, 3:12,
  4:12 AM, about 40 s each) and also grabbed location and **contacts**. A flashlight needs none of these. That's
  spyware-like behaviour, and it's also what drains the battery.
- **Normal:** the flashlight using the **camera** at 10:48 PM (the flashlight LED is part of the camera), Weather
  Now checking location hourly, and Snapchat/Maps in the evening.
- **Ambiguous ("Worth a look"):** Spotify using the mic for 1 second at 3:33 AM. This is probably a voice
  feature, but it isn't proven either way.
- **Do next:** uninstall the flashlight app (the phone has one built in), review permissions in the
  Privacy Dashboard, and set Weather to "only while using the app".
- **Human edge:** the card says it's a free flashlight app installed last week. **Machine edge:**
  spotting the exact hourly pattern.
- **Watch for:** the AI flagging the flashlight's camera use as malicious.

### Case 4: "Did I get phished?" (browser)
- **What happened:** from Gmail, a `bit.ly` short link led to **paypa1.com** (the digit 1, not the letter l).
  Sam entered an email and password there. The next page was `secure-paypal.com.account-verify.xyz`, which
  really belongs to *account-verify.xyz*. There Sam entered **card number, expiry and CVV**, then
  downloaded `PayPal_Security_Update.exe`. The real paypal.com visit afterwards is Sam checking.
- **Why saved passwords stopped working:** the .exe is most likely an info-stealer that took the
  browser's saved passwords and session cookies. This is likely, but not proven by these logs alone.
- **Do next:** don't run the .exe (delete it), scan or reinstall the laptop, call the card issuer to cancel
  the card, change the PayPal password and every password saved in the browser *from a clean device*, turn on
  2-step verification, and sign out of all sessions.
- **Human edge:** the card explains the email and the "page just refreshed" trick. **Machine edge:**
  spotting `paypa1` vs `paypal` at a glance.
- **Normal:** YouTube, Amazon, accounts.google.com.
