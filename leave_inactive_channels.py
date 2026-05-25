"""
leave_inactive_channels.py
Auto-leave inactive Telegram channels based on last activity date.
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.types import Channel
from dotenv import load_dotenv
import os

from config import INACTIVE_DAYS, DRY_RUN, REVIEW_MODE, WHITELIST, SESSION_NAME

load_dotenv()

_raw_api_id = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not _raw_api_id or not API_HASH:
    sys.exit(
        "❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH.\n"
        "   Copy .env.example to .env and fill in your credentials from my.telegram.org."
    )

try:
    API_ID = int(_raw_api_id)
except ValueError:
    sys.exit("❌ TELEGRAM_API_ID must be a number. Check your .env file.")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def get_inactive_channels():
    """Return list of channels with no activity for over INACTIVE_DAYS."""
    inactive = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVE_DAYS)

    async for dialog in client.iter_dialogs():
        if not isinstance(dialog.entity, Channel):
            continue

        name = dialog.name
        last_active = dialog.date

        # Skip whitelisted channels
        if any(w.lower() in name.lower() for w in WHITELIST):
            print(f"  ⏭️  Skipped (whitelisted): {name}")
            continue

        if last_active is None or last_active < cutoff:
            inactive.append(
                {
                    "name": name,
                    "id": dialog.id,
                    "last_active": last_active.strftime("%Y-%m-%d") if last_active else "never",
                    "entity": dialog.entity,
                }
            )

    return inactive


async def main():
    await client.start()
    print("✅ Logged in successfully\n")

    print(f"🔍 Scanning for channels inactive over {INACTIVE_DAYS} days...\n")
    inactive_channels = await get_inactive_channels()

    if not inactive_channels:
        print("🎉 No inactive channels found. You're all clean!")
        return

    print(f"\n📋 Found {len(inactive_channels)} inactive channel(s):\n")
    for ch in inactive_channels:
        print(f"  • [{ch['last_active']}] {ch['name']}")

    if DRY_RUN:
        print(f"\n⚠️  DRY RUN — no channels were left.")
        print("    Set DRY_RUN = False in config.py to actually leave them.")
        return

    if REVIEW_MODE:
        await leave_one_by_one(inactive_channels)
    else:
        await leave_all(inactive_channels)


async def leave_channel(ch, prefix="  "):
    """Leave a single channel, printing success/failure.

    Args:
        ch: Channel dict with 'entity' and 'name'.
        prefix: Line prefix for status output.

    Returns:
        True if the channel was left successfully, False otherwise.
    """
    try:
        await client(LeaveChannelRequest(ch["entity"]))
        print(f"{prefix}✅ Left: {ch['name']}")
        await asyncio.sleep(2)  # Avoid Telegram rate limit
        return True
    except FloodWaitError as e:
        print(f"{prefix}⏳ Rate limited. Waiting {e.seconds}s before continuing...")
        await asyncio.sleep(e.seconds)
        return await leave_channel(ch, prefix)
    except Exception as e:
        print(f"{prefix}❌ Failed to leave '{ch['name']}': {e}")
        return False


async def leave_one_by_one(channels):
    """Prompt yes/no/quit for each channel individually."""
    print("\n📝 Review mode — decide for each channel (yes / no / quit):\n")

    left, skipped = 0, 0

    for i, ch in enumerate(channels, 1):
        print(
            f"  [{i}/{len(channels)}] {ch['name']}  (last active: {ch['last_active']})"
        )

        answer = input("    Leave this channel? (yes/no/quit): ").strip().lower()

        if answer in ("q", "quit"):
            print("\n🛑 Quit early.")
            break
        elif answer in ("y", "yes"):
            if await leave_channel(ch, prefix="    "):
                left += 1
            print()
        else:
            print(f"    ⏭️  Skipped.\n")
            skipped += 1

    print(f"✅ Done! Left: {left} | Skipped: {skipped}")


async def leave_all(channels):
    """Leave all inactive channels at once after a single confirmation."""
    confirm = (
        input(f"\n🚨 Leave all {len(channels)} channel(s)? (yes/no): ").strip().lower()
    )
    if confirm not in ("y", "yes"):
        print("❌ Aborted.")
        return

    print()
    for ch in channels:
        await leave_channel(ch)

    print("\n✅ Done! All inactive channels have been left.")


if __name__ == "__main__":
    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Exiting.")
