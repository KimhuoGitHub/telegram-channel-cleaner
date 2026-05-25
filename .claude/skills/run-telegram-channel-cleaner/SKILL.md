---
name: run-telegram-channel-cleaner
description: Run, dry-run, and screenshot-verify the Telegram inactive-channel cleaner CLI (leave_inactive_channels.py). Use when asked to "run the cleaner", "test the channel cleaner", "dry-run this", or "verify leave_inactive_channels.py works".
---

# Run: telegram-channel-cleaner

A CLI tool (Telethon) that logs into a real Telegram account and lists
channels with no activity beyond `INACTIVE_DAYS`. Paths below are
relative to the repo root (`telegram-channel-cleaner/`).

**This tool authenticates against a real, personal Telegram account**
using credentials in `.env` and an already-authorized session file
(`session_cleaner.session`). There is no test/sandbox mode. Its core
action (`LeaveChannelRequest`) is irreversible — it actually removes
the account from a channel. **Never flip `DRY_RUN` to `False` or drive
`REVIEW_MODE`/`leave_all` prompts unless the user has explicitly
authorized a real leave in the current conversation.** Default to the
dry-run path below, which is safe to re-run freely.

## Prerequisites

- `.env` exists with real `TELEGRAM_API_ID` / `TELEGRAM_API_HASH`
  (get from https://my.telegram.org). Copy `.env.example` if missing —
  but note a fresh `.env` still requires an interactive phone/code
  login on first run, which this skill does not automate.
- `session_cleaner.session` exists (created by a prior interactive
  login). Its presence means `client.start()` will NOT prompt for a
  phone number / code — it reuses the saved session.
- Python venv with deps installed:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

## Run (agent path — dry run, safe)

1. Confirm `config.py` has `DRY_RUN = True` (this is the committed
   default). Do not change it.
2. Run:
   ```bash
   source venv/bin/activate && python leave_inactive_channels.py
   ```
3. Expected output: a login confirmation, a scan line, a numbered list
   of inactive channels (`[YYYY-MM-DD] Channel Name`, or `[never]` for
   channels with zero messages), then:
   ```
   ⚠️  DRY RUN — no channels were left.
       Set DRY_RUN = False in config.py to actually leave them.
   ```
   The process exits on its own — no interactive input required in
   dry-run mode.

This is the full verification loop: it proves auth, the scan/dialog
iteration, whitelist filtering, and the inactivity cutoff logic, all
without any destructive call. Re-run it any time; it's idempotent.

## Run (human path — real leave, destructive)

Only with explicit user authorization in the conversation:
1. Set `DRY_RUN = False` in `config.py`.
2. Run the same command. With `REVIEW_MODE = True` (default) it will
   prompt `yes/no/quit` per channel via `input()` — drive this with a
   real terminal or `expect`-style stdin piping, not headlessly, since
   each answer triggers a real `LeaveChannelRequest`.
3. Revert `DRY_RUN` to `True` afterward so the repo default stays safe.

## Gotchas

- `int(os.getenv("TELEGRAM_API_ID"))` fails fast with a clear message
  now if `.env` is missing/malformed (see `leave_inactive_channels.py`
  top-level guard) — if you see a raw `TypeError` instead, the code
  predates that fix.
- `dialog.date` is `None` for channels with zero messages ever (not a
  join-date fallback) — the scan treats `None` as inactive and labels
  it `"never"` in the printed list. If you see channels missing that
  you expected to be flagged, check this isn't regressed.
- No `timeout` binary on macOS by default (`gtimeout` via coreutils,
  or just rely on the script's own dry-run exit — it doesn't block).

## Troubleshooting

- `TypeError: int() argument must be a string...` on startup → `.env`
  missing or `TELEGRAM_API_ID`/`TELEGRAM_API_HASH` blank. Copy
  `.env.example` to `.env` and fill in real values.
- Hangs after "Scanning for channels..." → likely a `FloodWaitError`
  loop from a prior leave run; the current code catches it and sleeps
  `e.seconds` (can be long) rather than failing — this is expected
  behavior, not a hang, if the wait is large.
