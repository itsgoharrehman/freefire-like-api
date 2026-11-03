# -*- coding: utf-8 -*-
"""
refresh_tokens.py - Standalone High-Speed Token Generator & Refresher
Authored for Gohar Rehman | Free Fire Like Engine
"""
import sys
import asyncio
import time

sys.stdout.reconfigure(encoding="utf-8")
from core.tokens import token_manager
from core.telegram import send_telegram_report, format_token_refresh_report

async def run():
    print("=" * 60)
    print("  GOHAR REHMAN | FREE FIRE TOKEN REFRESH ENGINE (OB55)")
    print("=" * 60)
    print(f"[*] Loaded {len(token_manager.accounts)} accounts from data/accounts.json")
    print("[*] Authenticating accounts in parallel (concurrency: 50)...")
    res = await token_manager.refresh_all_accounts(concurrency=50)
    print(f"\n[+] Refresh Complete!")
    print(f"    Total Accounts : {res['total']}")
    print(f"    Active Tokens  : {res['active']}")
    print(f"    Failed/Banned  : {res['failed']}")
    print(f"    Duration       : {res['duration']}s")

    report = format_token_refresh_report(
        total=res["total"],
        active=res["active"],
        failed=res["failed"],
        duration=res["duration"]
    )
    sent = await send_telegram_report(report)
    if sent:
        print("[+] Telegram report dispatched successfully!")

if __name__ == "__main__":
    asyncio.run(run())
