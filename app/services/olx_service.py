"""
OLX.uz Automated Advert Publishing Service.

Handles:
1. OLX session state validation and management.
2. Downloading Telegram media attachments to local temporary storage.
3. Automated form submission to OLX.uz using Playwright.
4. Extracting published advert URLs and status tracking in database.
"""

import os
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

try:
    from aiogram import Bot
except ImportError:
    Bot = Any  # type: ignore

from app.config.settings import settings
from app.utils.logger import logger
from app.database.database import AsyncSessionLocal
from app.database.models.advertising_request import AdvertisingRequest
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.database.repositories.audit_repo import AuditRepository
from app.services.olx_category_mapper import OlxCategoryMapper


class OlxService:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "app" / "data"
    TEMP_MEDIA_DIR = DATA_DIR / "temp_media"

    @classmethod
    def get_session_file_path(cls) -> Path:
        raw_path = getattr(settings, "OLX_SESSION_FILE", "app/data/olx_session.json")
        p = Path(raw_path)
        if not p.is_absolute():
            p = cls.BASE_DIR / p
        return p

    @classmethod
    def get_session_status(cls) -> Dict[str, Any]:
        """
        Inspects the OLX session file to verify if user has active authorization.
        Returns status dictionary.
        """
        session_file = cls.get_session_file_path()
        if not session_file.exists():
            return {
                "exists": False,
                "file_path": str(session_file),
                "is_valid": False,
                "account_name": None,
                "updated_at": None,
                "message": "Sessiya fayli topilmadi. Avtorizatsiyadan o‘tish zarur."
            }

        try:
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime, tz=timezone.utc)
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cookies = data.get("cookies", [])
            origins = data.get("origins", [])

            # Check for OLX cookies
            has_olx_cookie = any("olx.uz" in c.get("domain", "") for c in cookies)
            has_local_storage = len(origins) > 0

            # Find user info if present in cookies or localStorage
            account_name = None
            for cookie in cookies:
                if cookie.get("name") in ("user_name", "user_email", "phone"):
                    account_name = cookie.get("value")
                    break

            is_valid = has_olx_cookie or has_local_storage

            return {
                "exists": True,
                "file_path": str(session_file),
                "is_valid": is_valid,
                "cookies_count": len(cookies),
                "account_name": account_name or "Ulangan OLX foydalanuvchisi",
                "updated_at": mtime.strftime("%d.%m.%Y %H:%M UTC"),
                "message": "OLX sessiyasi faol va yuklangan." if is_valid else "Sessiya fayli bo‘sh yoki yaroqsiz."
            }
        except Exception as e:
            logger.error(f"Error inspecting OLX session: {e}")
            return {
                "exists": True,
                "file_path": str(session_file),
                "is_valid": False,
                "account_name": None,
                "updated_at": None,
                "message": f"Sessiya faylini o‘qishda xatolik: {e}"
            }

    @classmethod
    def save_session_json(cls, json_str: str) -> Tuple[bool, str]:
        """Saves session state JSON uploaded from Web Admin."""
        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, dict) or "cookies" not in parsed:
                return False, "Noto‘g‘ri format: 'cookies' kaliti mavjud emas."

            session_file = cls.get_session_file_path()
            session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)

            return True, "OLX sessiyasi muvaffaqiyatli saqlandi."
        except json.JSONDecodeError as jde:
            return False, f"JSON sintaksis xatosi: {jde}"
        except Exception as e:
            return False, f"Faylni saqlashda xatolik: {e}"

    @classmethod
    async def download_request_media(
        cls,
        bot: Optional[Bot],
        req: AdvertisingRequest
    ) -> List[str]:
        """
        Downloads photos from Telegram via Bot API into temporary folder.
        Returns list of local file paths.
        """
        if not bot or not req.media_items:
            return []

        req_temp_dir = cls.TEMP_MEDIA_DIR / f"req_{req.id}"
        req_temp_dir.mkdir(parents=True, exist_ok=True)
        local_paths = []

        for idx, media in enumerate(req.media_items):
            if media.media_type != "PHOTO" and not media.media_type.startswith("PHOTO"):
                continue
            try:
                file_info = await bot.get_file(media.file_id)
                ext = ".jpg"
                if file_info.file_path and "." in file_info.file_path:
                    ext = "." + file_info.file_path.split(".")[-1]

                dest_file = req_temp_dir / f"photo_{idx + 1}{ext}"
                await bot.download_file(file_info.file_path, destination=dest_file)
                if dest_file.exists() and dest_file.stat().st_size > 0:
                    local_paths.append(str(dest_file))
            except Exception as e:
                logger.warning(f"Failed to download media {media.file_id} for req {req.id}: {e}")

        return local_paths

    @classmethod
    def cleanup_temp_media(cls, req_id: int):
        """Cleans up temporary media files for a request."""
        req_temp_dir = cls.TEMP_MEDIA_DIR / f"req_{req_id}"
        if req_temp_dir.exists():
            try:
                shutil.rmtree(req_temp_dir, ignore_errors=True)
            except Exception:
                pass

    @classmethod
    async def publish_request_to_olx(
        cls,
        bot: Optional[Bot],
        session_db: Any,
        req: AdvertisingRequest
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Main entry point for publishing an AdvertisingRequest to OLX.
        Returns (success: bool, olx_url: Optional[str], error_message: Optional[str]).
        """
        req_id = req.id
        logger.info(f"🚀 OLX ga e’lon joylashtirish boshlandi: req_id={req_id} ({req.request_number})")

        # 1. Check if OLX enabled
        if not getattr(settings, "OLX_ENABLED", True):
            msg = "OLX integratsiyasi sozlamalarda o‘chirilgan."
            await AdvertisingRequestRepository.update_olx_status(session_db, req_id, "NONE", olx_error=msg)
            return False, None, msg

        # 2. Check session file
        session_status = cls.get_session_status()
        if not session_status["exists"] or not session_status["is_valid"]:
            error_msg = "OLX avtorizatsiya sessiyasi mavjud emas yoki eskirgan. Admin panel orqali kiring."
            logger.error(f"❌ {error_msg} | req_id={req_id}")
            await AdvertisingRequestRepository.update_olx_status(
                session_db, req_id, "FAILED", olx_error=error_msg
            )
            return False, None, error_msg

        # Set status to PUBLISHING
        await AdvertisingRequestRepository.update_olx_status(session_db, req_id, "PUBLISHING")

        # 3. Extract answers dictionary
        answers_dict: Dict[str, Any] = {}
        if req.answers:
            for ans in req.answers:
                answers_dict[ans.field_id] = ans.value

        advert_data = OlxCategoryMapper.prepare_advert_data(
            category_id=req.category_id,
            subcategory_id=req.subcategory_id,
            answers=answers_dict,
            preview_text=req.preview_text
        )
        if req.user:
            advert_data["person"] = req.user.first_name or req.user.username or "Foydalanuvchi"

        # 4. Download media attachments
        local_photos = []
        try:
            local_photos = await cls.download_request_media(bot, req)
        except Exception as e:
            logger.warning(f"Media yuklashda ogohlantirish: {e}")

        # 5. Execute browser automation via Playwright
        success, ad_url, ad_id, err_text = await cls._execute_playwright_post(advert_data, local_photos)

        # Clean up temporary downloaded photos
        cls.cleanup_temp_media(req_id)

        # 6. Save results
        if success and ad_url:
            await AdvertisingRequestRepository.update_olx_status(
                session_db,
                request_id=req_id,
                olx_status="PUBLISHED",
                olx_ad_id=ad_id or f"olx_{req_id}",
                olx_ad_url=ad_url,
                olx_error=None
            )
            await AuditRepository.create(
                session_db,
                event_type="olx_advert_published",
                details=f"Req {req.request_number} published to OLX: {ad_url}"
            )
            logger.info(f"✅ E’lon OLX.uz ga muvaffaqiyatli joylandi: {ad_url}")
            return True, ad_url, None
        else:
            err = err_text or "OLX.uz e’lon joylashda noma’lum xatolik yuz berdi."
            await AdvertisingRequestRepository.update_olx_status(
                session_db,
                request_id=req_id,
                olx_status="FAILED",
                olx_error=err
            )
            await AuditRepository.create(
                session_db,
                event_type="olx_advert_failed",
                details=f"Req {req.request_number} failed to post to OLX: {err}"
            )
            logger.error(f"❌ OLX e’lon joylashda xatolik | req={req.request_number}: {err}")
            return False, None, err

    @classmethod
    async def _execute_playwright_post(
        cls,
        advert_data: Dict[str, Any],
        photo_paths: List[str]
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Uses Playwright to navigate to OLX.uz, fill the form, upload photos, and submit.
        """
        session_file = cls.get_session_file_path()
        headless = getattr(settings, "OLX_HEADLESS", True)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            msg = "Playwright moduli o‘rnatilmagan. 'pip install playwright' va 'playwright install chromium' zarur."
            return False, None, None, msg

        try:
            async with async_playwright() as p:
                browser = None
                for channel in ["chrome", "msedge", None]:
                    try:
                        kwargs = {
                            "headless": headless,
                            "ignore_default_args": ["--enable-automation"],
                            "args": [
                                "--disable-blink-features=AutomationControlled",
                                "--no-sandbox",
                                "--disable-setuid-sandbox",
                                "--disable-infobars",
                            ]
                        }
                        if channel:
                            kwargs["channel"] = channel
                        browser = await p.chromium.launch(**kwargs)
                        if browser:
                            break
                    except Exception:
                        continue

                if not browser:
                    return False, None, None, "Brauzerni ishga tushirib bo'lmadi (Chrome, Edge yoki Playwright Chromium topilmadi)."

                context = await browser.new_context(
                    storage_state=str(session_file),
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                    locale="uz-UZ"
                )

                # Anti-detection stealth script
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.navigator.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['uz-UZ', 'uz', 'ru-RU', 'ru', 'en-US', 'en']});
                """)

                page = await context.new_page()

                # Step A: Navigate to add new advert page
                post_url = "https://www.olx.uz/adding/"
                logger.info(f"🌐 Sahifa ochilmoqda: {post_url}")
                try:
                    await page.goto(post_url, wait_until="domcontentloaded", timeout=45000)
                except Exception as nav_err:
                    await browser.close()
                    return False, None, None, f"OLX sahifasiga ulanib bo‘lmadi: {nav_err}"

                # Step B: Check if redirected to login page (Session expired)
                current_url = page.url
                if "login" in current_url or "account" in current_url:
                    await browser.close()
                    return False, None, None, "OLX sessiyasi muddati o‘tgan. Iltimos, admin paneldan qayta tizimga kiring."

                await asyncio.sleep(2)

                # Step B.1: Dismiss cookies banner if present
                try:
                    cookie_btn = await page.query_selector('[data-testid="dismiss-cookies-banner"], button#onetrust-accept-btn-handler')
                    if cookie_btn and await cookie_btn.is_visible():
                        await cookie_btn.click()
                        await asyncio.sleep(1)
                        logger.debug("OLX cookies banner dismissed.")
                except Exception:
                    pass

                # Step C: Fill Title
                title = advert_data["title"]
                title_selector = 'input[data-testid="posting-title"], input[name="title"], input[data-cy="ad-title"]'
                try:
                    await page.wait_for_selector(title_selector, timeout=10000)
                    await page.fill(title_selector, title)
                    logger.info(f"OLX Title kiritildi: {title}")
                except Exception as t_err:
                    logger.warning(f"Title maydoni topilmadi: {t_err}")
                    inputs = await page.query_selector_all('input[type="text"]')
                    if inputs:
                        await inputs[0].fill(title)

                await asyncio.sleep(2)

                # Step D: Category Selection
                # Check if OLX already suggested and applied the category based on title
                has_suggested = False
                try:
                    sug_card = await page.query_selector('div:has-text("Наше предложение:"), div:has-text("Bizning taklifimiz:"), [data-testid="suggested-category"]')
                    if sug_card and await sug_card.is_visible():
                        has_suggested = True
                        logger.info("OLX sarlavha asosida toifani avtomatik taklif qildi va tanladi.")
                except Exception:
                    pass

                if not has_suggested:
                    mapping = advert_data.get("category_mapping")
                    cat_picker = await page.query_selector('[data-testid="posting-select-category"]')
                    if cat_picker and await cat_picker.is_visible():
                        try:
                            await cat_picker.click()
                            await asyncio.sleep(1.5)
                            rec = await page.query_selector('div:has-text("Рекомендованная") + div, div:has-text("Tavsiya etilgan") + div')
                            if rec and await rec.is_visible():
                                await rec.click()
                                await asyncio.sleep(1)
                            elif mapping and mapping.search_terms:
                                for term in mapping.search_terms:
                                    cat_elem = await page.query_selector(f'text="{term}"')
                                    if cat_elem and await cat_elem.is_visible():
                                        await cat_elem.click()
                                        await asyncio.sleep(1.2)
                        except Exception as cp_err:
                            logger.debug(f"Category picker click error: {cp_err}")

                # Wait for category-dependent inputs (Price, Attributes, Location) to mount
                await asyncio.sleep(2)

                # Step E: Fill Description
                description = advert_data["description"]
                desc_selector = 'textarea[data-testid="posting-description-text-area"], textarea[name="description"], textarea[data-cy="ad-description"]'
                try:
                    await page.wait_for_selector(desc_selector, timeout=10000)
                    await page.fill(desc_selector, description)
                    logger.info("OLX Description to‘ldirildi.")
                except Exception as d_err:
                    logger.warning(f"Description maydonini to‘ldirishda xatolik: {d_err}")

                # Step F: Upload photos if any
                if photo_paths:
                    valid_paths = [p for p in photo_paths if os.path.exists(p)]
                    if valid_paths:
                        file_input = await page.query_selector('input[data-testid="attach-photos-input"], input[type="file"]')
                        if file_input:
                            try:
                                await file_input.set_input_files(valid_paths[:8])
                                logger.info(f"📸 {len(valid_paths[:8])} ta rasm OLX ga biriktirildi.")
                                await asyncio.sleep(3)
                            except Exception as p_err:
                                logger.warning(f"Rasmlarni yuklashda ogohlantirish: {p_err}")

                # Step G: Set Item Selling Price (User's real product price)
                price = advert_data.get("price", 0)
                if price and price > 0:
                    price_selector = 'input[data-testid="price-input"], input[name="parameters.price.price"], input[name*="price"], input[data-testid="price"]'
                    price_input = await page.query_selector(price_selector)
                    if price_input and await price_input.is_visible():
                        try:
                            await price_input.fill(str(price))
                            logger.info(f"OLX Mahsulot Narxi kiritildi: {price}")
                        except Exception as p_err:
                            logger.warning(f"Narx kiritishda ogohlantirish: {p_err}")

                # Step H: Private / Business type (Частное лицо / Бизнес)
                try:
                    priv_btn = await page.query_selector('[data-testid="private_business_private_unactive"], [data-cy="private_business_private"], button:has-text("Частное лицо"), button:has-text("Jismoniy shaxs")')
                    if priv_btn and await priv_btn.is_visible():
                        await priv_btn.click()
                        await asyncio.sleep(0.5)
                        logger.info("OLX 'Частное лицо' (Jismoniy shaxs) tanlandi.")
                except Exception as priv_err:
                    logger.debug(f"Private toggle error: {priv_err}")

                # Step I: Brand Selection (Марка телефона / parameters.mobile_phone_manufacturer)
                brand = advert_data.get("brand")
                if brand:
                    try:
                        brand_box = await page.query_selector('[data-cy="parameters.mobile_phone_manufacturer"], [data-testid="dropdown"]:has-text("Марка"), div:has-text("Марка телефона")')
                        if brand_box and await brand_box.is_visible():
                            await brand_box.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            btn = await brand_box.query_selector('input, button, .n-referenceinput-button')
                            if btn:
                                await btn.click()
                                await asyncio.sleep(1)
                                brand_opt = await page.query_selector(f'text="{brand}"')
                                if brand_opt and await brand_opt.is_visible():
                                    await brand_opt.click()
                                    logger.info(f"OLX Brend tanlandi: {brand}")
                                    await asyncio.sleep(0.5)
                                else:
                                    # Fallback: pick Apple or first option
                                    fb = await page.query_selector('text="Apple"')
                                    if fb and await fb.is_visible():
                                        await fb.click()
                                        logger.info("OLX Brend (fallback Apple) tanlandi.")
                    except Exception as b_err:
                        logger.debug(f"Brand selection error: {b_err}")

                # Step J: Condition toggle (Yangi / Ishlatilgan, Новый / Б/у)
                condition = advert_data.get("condition", "yangi")
                try:
                    if condition == "ishlatilgan":
                        cond_btn = await page.query_selector('[data-testid="parameters.state_used_unactive"], [data-cy="parameters.state_used"], button:has-text("Б/у"), button:has-text("Ishlatilgan")')
                    else:
                        cond_btn = await page.query_selector('[data-testid="parameters.state_new_unactive"], [data-cy="parameters.state_new"], button:has-text("Новый"), button:has-text("Yangi")')
                    if cond_btn and await cond_btn.is_visible():
                        await cond_btn.click()
                        await asyncio.sleep(0.5)
                        logger.info(f"OLX Holati tanlandi: {condition}")
                except Exception as c_err:
                    logger.debug(f"Condition toggle error: {c_err}")

                # Step K: Set Location if not already pre-filled
                loc_selector = 'input[data-testid="autosuggest-location-search-input"], input[name="city_id"]'
                loc_input = await page.query_selector(loc_selector)
                if loc_input and await loc_input.is_visible():
                    try:
                        val = await loc_input.input_value()
                        if not val:
                            city = advert_data.get("city_district") or getattr(settings, "OLX_DEFAULT_CITY", "Toshkent") or "Toshkent"
                            await loc_input.fill(city)
                            await asyncio.sleep(1.5)
                            sug = await page.query_selector('[data-testid="autosuggest-location-search-item"], li[role="option"]')
                            if sug:
                                await sug.click()
                                await asyncio.sleep(1)
                                logger.info(f"OLX Joylashuv tanlandi: {city}")
                    except Exception as l_err:
                        logger.warning(f"Joylashuv kiritishda ogohlantirish: {l_err}")

                # Step L: Set Contact Phone
                phone = advert_data.get("phone", "")
                if phone:
                    phone_selector = 'input[data-testid="phone"], input[name="phone"]'
                    phone_input = await page.query_selector(phone_selector)
                    if phone_input and await phone_input.is_visible():
                        try:
                            curr_phone = await phone_input.input_value()
                            if not curr_phone:
                                await phone_input.fill(str(phone))
                                logger.info(f"OLX Aloqa telefoni kiritildi: {phone}")
                        except Exception as ph_err:
                            logger.warning(f"Telefon kiritishda ogohlantirish: {ph_err}")

                # Step M: Set Contact Person
                person_name = advert_data.get("person", "")
                if person_name:
                    person_selector = 'input[data-testid="person"], input[name="person"]'
                    person_input = await page.query_selector(person_selector)
                    if person_input and await person_input.is_visible():
                        try:
                            curr_person = await person_input.input_value()
                            if not curr_person:
                                await person_input.fill(str(person_name))
                        except Exception:
                            pass

                await asyncio.sleep(2)

                # Step N: Click Submit Button
                submit_selector = 'button[data-testid="submit-btn"], button[type="submit"]:has-text("Опубликовать"), button:has-text("E’lonni joylashtirish")'
                submit_btn = await page.query_selector(submit_selector)
                if submit_btn and await submit_btn.is_visible():
                    logger.info("👉 E’lonni tasdiqlash (Submit) tugmasi bosilmoqda...")
                    await submit_btn.scroll_into_view_if_needed()
                    await submit_btn.click()
                    await asyncio.sleep(8)
                else:
                    logger.warning("Submit tugmasi topilmadi yoki ko‘rinmayapti.")

                # Step O: Validate Redirection and Extract Published URL
                final_url = page.url
                logger.info(f"Submitdan keyingi URL: {final_url}")
                published_url = None
                ad_id = None

                # CRITICAL: If still on /dobavit/ or /adding/, submission was rejected!
                if "/dobavit" in final_url or "/adding" in final_url:
                    err_msgs = []
                    try:
                        err_els = await page.query_selector_all('[data-has-error="true"], [data-error="true"], [role="alert"], p:has-text("Сделайте выбор"), p:has-text("Заполните")')
                        for e in err_els:
                            txt = (await e.text_content() or "").strip()
                            if txt and txt not in err_msgs and len(txt) < 100:
                                err_msgs.append(txt)
                    except Exception:
                        pass
                    err_detail = "; ".join(err_msgs) if err_msgs else "Majburiy maydonlar to‘liq to‘ldirilmadi"
                    await browser.close()
                    return False, None, None, f"E’lon qabul qilinmadi (forma sahifasida qoldi): {err_detail}"

                # Extract ad_id if present in URL
                import re
                ad_id_match = re.search(r"ad-id=(\d+)", final_url) or re.search(r"-ID([a-zA-Z0-9]+)", final_url)
                if ad_id_match:
                    ad_id = ad_id_match.group(1)

                # Case 1: Redirected to promotion / upsell page (standard OLX post-ad step)
                if "purchase" in final_url or "promote" in final_url or "activate" in final_url:
                    try:
                        no_ad_btn = await page.query_selector('button:has-text("Не рекламировать"), a:has-text("Не рекламировать"), button:has-text("Reklama qilmaslik")')
                        if no_ad_btn and await no_ad_btn.is_visible():
                            await no_ad_btn.click()
                            await asyncio.sleep(2)
                    except Exception:
                        pass

                    if ad_id:
                        published_url = f"https://www.olx.uz/d/obyavlenie/-ID{ad_id}.html"
                    else:
                        published_url = "https://www.olx.uz/myaccount/"

                # Case 2: Direct public ad page
                elif "/d/obyavlenie/" in final_url or "/obyavlenie/" in final_url:
                    published_url = final_url

                # Case 3: MyAccount or success confirmation
                elif "myaccount" in final_url or "success" in final_url:
                    published_url = final_url if "http" in final_url else "https://www.olx.uz/myaccount/"
                    if not ad_id:
                        ad_id = f"olx_{int(datetime.now().timestamp())}"

                await browser.close()

                if published_url:
                    return True, published_url, ad_id, None
                else:
                    return False, None, None, f"E’lon chop etildi deb hisoblanmadi. Oxirgi sahifa: {final_url}"

        except Exception as e:
            logger.error(f"Playwright OLX execution error: {e}", exc_info=True)
            return False, None, None, f"Brauzer xatosi: {str(e)}"

    @classmethod
    async def trigger_manual_push(cls, request_id: int, bot: Optional[Bot] = None) -> Tuple[bool, str]:
        """Triggers manual publishing from Web Admin or Telegram command."""
        async with AsyncSessionLocal() as session:
            req = await AdvertisingRequestRepository.get_by_id(session, request_id)
            if not req:
                return False, f"ID={request_id} li so‘rov topilmadi."

            success, url, err = await cls.publish_request_to_olx(bot, session, req)
            if success:
                return True, f"E’lon OLX.uz ga muvaffaqiyatli joylashtirildi: {url}"
            else:
                return False, f"Joylashtirishda xatolik: {err}"
