# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Booth visitors** (general public, all ages, mostly non-experts) at the CSF 2026 booth. They read a big-screen dashboard from a few metres away, play "You vs. the Machine" rounds, and send logs from their own phones via a QR link.
- **Booth operators** (students) who drive the dashboard from a laptop: sign in, play cases, toggle Challenge mode, reveal answers, ask the AI, reset between visitors, and connect devices.

## Product Purpose

TheLogWatch turns the raw logs that home devices quietly write (routers, Windows PCs, phones, browsers) into plain-English verdicts with a next step. At the booth it powers a competition: a visitor reads raw logs and a case card, guesses what is going on, then compares their answer with the rule-based verdicts and an AI's independent read. Success: a visitor walks away understanding that their devices keep a diary, and that a human with context catches things a machine cannot (and vice versa).

## Positioning

Not a SOC tool: a translator. Every line becomes one of four plain verdicts (Normal, FYI, Worth a look, Act now) plus advice, and the booth game pits human context against machine pattern-matching on the same evidence.

## Operating Context

- Big-screen dashboard (`frontend/index.html`) shown on a booth display, operated by keyboard/mouse; `C` toggles Challenge mode.
- Visitor phone page (`frontend/phone.html`) opened via QR code; visitors choose what to send.
- Paper case cards accompany each of the four cases; the answer key lives in README.md.
- Backend on Render (FastAPI + MongoDB Atlas), frontend on Netlify; static HTML/CSS/JS with no build step.

## Capabilities and Constraints

- Operator login with `ADMIN_PASSWORD` (12-hour token); devices/phones send with `INGEST_KEY`; optional read-only public view.
- Live stream via SSE with 3 s polling fallback; Ask AI uses Claude when a key is set, otherwise falls back to the rule-based digest.
- Four cases: router slow Wi-Fi, Windows "someone on my PC", phone battery drain, browser phishing. Plus background noise and looping attract mode.
- Must stay dependency-light static files; log text is always HTML-escaped.

## Brand Commitments

- Name: **TheLogWatch** (one word, capital T, L, W).
- Game name: **You vs. the Machine**. Event theme: **Connected lives, Protected futures** (CSF 2026). Both stay.
- Verdict vocabulary is fixed: Normal, FYI, Worth a look, Act now.

## Evidence on Hand

- Four real case log packets in `backend/sample_logs/`, case cards served by `/api/scenarios`.
- No logo existed before this rebrand; no testimonials, metrics, or press. Do not fabricate any.

## Product Principles

1. Plain English first; raw logs are available, never the headline.
2. Readable from across a room by a non-expert.
3. The human's edge is part of the story: never make the machine look omniscient.
4. Privacy by default: visitors choose exactly what to send.

## Accessibility & Inclusion

Public, all-ages audience: verdicts must never rely on colour alone (glyph + word), and text must hold contrast on a bright booth display.
