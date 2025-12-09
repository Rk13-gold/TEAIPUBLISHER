#!/usr/bin/env python3
"""
Small script to validate Telegram bot token and channel configuration using the project's `Config`.
Usage: python scripts/check_bot_chat.py
"""
from core.config import Config

if __name__ == '__main__':
    cfg = Config()
    ok, msg = cfg.check_telegram_bot_and_chat()
    if ok:
        print("✅ Bot and channel validated:", msg)
    else:
        print("❌ Validation failed:", msg)
