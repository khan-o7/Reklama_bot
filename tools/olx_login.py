"""
OLX.uz bir martalik avtorizatsiya va sessiyani saqlash skripti.

Ushbu skript brauzerni ko'rinadigan (headful) rejimda ochadi.
Siz o'z OLX akkauntingizga qo'lda kirasiz (SMS/parol orqali),
so'ngra skript tizimga kirish sessiyasini (cookies va localStorage)
'app/data/olx_session.json' fayliga saqlab oladi.
"""

import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
SESSION_FILE = DATA_DIR / "olx_session.json"
USER_DATA_DIR = DATA_DIR / "olx_profile"


async def main():
    print("=" * 60)
    print("🛡️  OLX.uz AVTORIZATSIYA VA SESSIYANI SAQLASH SKRIPTI")
    print("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\n🌐 Brauzer ochilmoqda...")

    async with async_playwright() as p:
        # Chromium brauzerini xuddi oddiy foydalanuvchidek ishga tushiramiz
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="uz-UZ"
        )

        page = await context.new_page()

        print("👉 OLX.uz ochilmoqda...")
        try:
            await page.goto("https://www.olx.uz/account/", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️ Sahifa yuklanishida ogohlantirish: {e}")

        print("\n" + "*" * 60)
        print("📌 DIQQAT:")
        print("1. Ochilgan brauzerda OLX akkauntingizga kiring (Telefon va parol/SMS orqali).")
        print("2. Tizimga muvaffaqiyatli kirib, shaxsiy kabinetingiz ko'ringandan so'ng:")
        print("   👉 SHU YERDA 'ENTER' TUGMASINI BOSING!")
        print("*" * 60 + "\n")

        # Konsolda Enter bosilishini kutish
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input, "Kirishni yakunlagach, ENTER bosing... ")

        print("\n💾 Sessiya ma'lumotlari saqlanmoqda...")
        await context.storage_state(path=str(SESSION_FILE))

        print(f"✅ MUVAFFAQITYATLI: OLX sessiyasi saqlandi!")
        print(f"📁 Fayl manzili: {SESSION_FILE}")

        await browser.close()
        print("\nBrauzer yopildi. Endi bot ushbu sessiyadan avtomatik foydalana oladi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAmaliyot to'xtatildi.")
        sys.exit(0)
