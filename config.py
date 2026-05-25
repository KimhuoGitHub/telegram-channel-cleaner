# config.py — Tweak your settings here

# ─── Inactivity Threshold ─────────────────────────────
# Leave channels with no activity beyond this many days
INACTIVE_DAYS = 30

# ─── Dry Run ──────────────────────────────────────────
# True  → preview only (safe, nothing gets left)
# False → actually leave the channels
DRY_RUN = True

# ─── Review Mode ──────────────────────────────────────
# True  → prompt yes/no for each channel individually
# False → leave all inactive channels at once (bulk)
REVIEW_MODE = True

# ─── Whitelist ────────────────────────────────────────
# Channel names containing these strings will be skipped
# Case-insensitive. Partial match is supported.
# Example: ["work", "family", "my team"]
WHITELIST = []

# ─── Session ──────────────────────────────────────────
# Local session file name (auto-created on first login)
SESSION_NAME = "session_cleaner"
