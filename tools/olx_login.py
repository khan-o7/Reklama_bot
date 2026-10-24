"""
OLX.uz bir martalik avtorizatsiya va sessiyani saqlash skripti (Stealth Anti-Detection).

Ushbu skript brauzerni oddiy inson ochganidek (bot belgilari butunlay yashirilgan) rejimda ochadi.
Siz o'z OLX akkauntingizga kirasiz, so'ngra skript tizimga kirish sessiyasini (cookies va localStorage)
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
    print("=" * 65)
    print("🛡️  OLX.uz AVTORIZATSIYA VA SESSIYANI SAQLASH (STEALTH REJIM)")
    print("=" * 65)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\n🌐 Haqiqiy brauzer profili ishga tushirilmoqda...")

    async with async_playwright() as p:
        context = None
        # Chrome, Edge yoki Chromium orqali doimiy profil bilan ochamiz
        for channel in ["chrome", "msedge", None]:
            try:
                kwargs = {
                    "user_data_dir": str(USER_DATA_DIR),
                    "headless": False,
                    "ignore_default_args": ["--enable-automation"],
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                        "--no-sandbox",
                        "--disable-infobars",
                        "--disable-dev-shm-usage",
                    ],
                    "viewport": None,  # Brauzer ekran o'lchamida ochiladi
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                    "locale": "uz-UZ"
                }
                if channel:
                    kwargs["channel"] = channel
                context = await p.chromium.launch_persistent_context(**kwargs)
                if context:
                    print(f"✅ Brauzer ishga tushdi ({channel or 'Chromium'}).")
                    break
            except Exception:
                continue

        if not context:
            raise RuntimeError("Brauzerni ishga tushirib bo'lmadi.")

        # Bot indikatorlarini butunlay yashirish
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['uz-UZ', 'uz', 'ru-RU', 'ru', 'en-US', 'en']});
        """)

        pages = context.pages
        page = pages[0] if pages else await context.new_page()

        print("👉 OLX.uz bosh sahifasi ochilmoqda...")
        try:
            await page.goto("https://www.olx.uz/", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"⚠️ Sahifa yuklanishida ogohlantirish: {e}")

        await asyncio.sleep(2)

        print("\n" + "*" * 65)
        print("📌 YO'RIQNOMA:")
        print("1. Ochilgan brauzer oynasida:")
        print("   - Agar robot tekshiruvi (Cloudflare) chiqsa, galochkani bosing.")
        print("   - Yuqori o'ng burchakdagi 'Hisobingiz' tugmasini bosib OLX ga kiring.")
        print("2. Tizimga muvaffaqiyatli kirganingizdan so'ng:")
        print("   👉 SHU YERDA 'ENTER' TUGMASINI BOSING!")
        print("*" * 65 + "\n")

        # Konsolda Enter bosilishini kutish
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input, "Kirishni yakunlagach, ENTER bosing... ")

        print("\n💾 Sessiya ma'lumotlari saqlanmoqda...")
        await context.storage_state(path=str(SESSION_FILE))

        print(f"✅ MUVAFFAQITYATLI: OLX sessiyasi saqlandi!")
        print(f"📁 Fayl manzili: {SESSION_FILE}")

        await context.close()
        print("\nBrauzer yopildi. Endi bot ushbu sessiyadan avtomatik foydalana oladi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAmaliyot to'xtatildi.")
        sys.exit(0)
