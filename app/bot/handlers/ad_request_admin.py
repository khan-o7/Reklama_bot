import hashlib
import html
from typing import Optional, List
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models.payment import Payment
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.database.repositories.user_repo import UserRepository
from app.services.publication_service import PublicationService
from app.utils.logger import logger

router = Router(name="ad_request_admin_router")


class AdminReqPricingStates(StatesGroup):
    entering_price = State()
    confirming_price = State()
    entering_reject_reason = State()
    entering_payment_reject_reason = State()


class UserReceiptStates(StatesGroup):
    submitting_receipt = State()


# =========================================================================
# 1. ADMIN PRICING WORKFLOW (Section 14)
# =========================================================================

@router.callback_query(F.data.startswith("adm_price:"))
async def handle_admin_set_price_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    admin_id = callback.from_user.id
    if admin_id not in settings.all_admin_ids:
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    await state.set_state(AdminReqPricingStates.entering_price)
    await state.update_data(target_req_id=req_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_price_cancel")]
    ])
    await callback.message.reply(
        f"💰 <b>REKLAMA NARXINI BELGILASH</b>\n\n"
        f"So‘rov raqami: <code>{req.request_number}</code>\n"
        f"Kategoriya: <b>{req.category_id}</b>\n\n"
        f"Iltimos, ushbu e’lon uchun reklama narxini <b>so‘mda</b> kiriting (masalan: <code>50000</code> yoki <code>100000</code>):",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()


@router.message(AdminReqPricingStates.entering_price, F.text)
async def handle_admin_price_input(message: Message, state: FSMContext, session: AsyncSession) -> None:
    admin_id = message.from_user.id
    if admin_id not in settings.all_admin_ids:
        return

    clean_digits = "".join(filter(str.isdigit, message.text))
    if not clean_digits:
        await message.reply("⚠️ Iltimos, narxni faqat raqamlar bilan kiriting (masalan: <code>50000</code>):", parse_mode="HTML")
        return

    price = int(clean_digits)
    if price < 1000:
        await message.reply("⚠️ Narx kamida 1 000 so‘m bo‘lishi kerak.", parse_mode="HTML")
        return

    data = await state.get_data()
    req_id = data.get("target_req_id")
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await message.reply("So‘rov topilmadi.")
        await state.clear()
        return

    await state.update_data(entered_price=price)
    await state.set_state(AdminReqPricingStates.confirming_price)

    cardholder = settings.AD_CARDHOLDER_NAME
    card_number = settings.AD_PAYMENT_CARD

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Narxni tasdiqlash va foydalanuvchiga yuborish", callback_data=f"adm_price_confirm:{req_id}")],
        [InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data=f"adm_price:{req_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_price_cancel")]
    ])

    summary_text = (
        f"📋 <b>NARX VA TO‘LOVNI TASDIQLASH:</b>\n\n"
        f"So‘rov: <code>{req.request_number}</code>\n"
        f"Belgilangan narx: <b>{price:,} so‘m</b>\n".replace(",", " ") +
        f"Karta egasi: <b>{cardholder}</b>\n"
        f"Karta raqami: <code>{card_number}</code>\n\n"
        f"Tasdiqlasangiz, to‘lov ma’lumotlari darhol e’lon egasiga yuboriladi."
    )
    await message.reply(summary_text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm_price_confirm:"), AdminReqPricingStates.confirming_price)
async def handle_admin_price_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    admin_id = callback.from_user.id
    if admin_id not in settings.all_admin_ids:
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    data = await state.get_data()
    req_id = int(callback.data.split(":")[1])
    price = data.get("entered_price")

    cardholder = settings.AD_CARDHOLDER_NAME
    card_number = settings.AD_PAYMENT_CARD

    req = await AdvertisingRequestRepository.set_price(
        session=session,
        request_id=req_id,
        price=price,
        card_number=card_number,
        cardholder=cardholder,
        admin_id=admin_id
    )
    await state.clear()

    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    # Notify admin of success
    await callback.message.edit_text(
        f"✅ <b>Narx muvaffaqiyatli belgilandi!</b>\n\n"
        f"So‘rov: <code>{req.request_number}</code>\n"
        f"Narx: <b>{price:,} so‘m</b>\n"
        f"Holati: <b>To‘lov kutilmoqda (AWAITING_PAYMENT)</b>".replace(",", " "),
        parse_mode="HTML"
    )

    # Send exact payment message to user (Section 14)
    user_db = await UserRepository.get_by_id(session, req.user_id)
    if user_db:
        payment_text = (
            "Reklama e’loningiz ko‘rib chiqildi.\n\n"
            f"So‘rov raqami: {req.request_number}\n"
            f"Reklama narxi: {price:,} so‘m\n\n".replace(",", " ") +
            "To‘lov ma’lumotlari:\n"
            f"Karta egasi: {cardholder}\n"
            f"Karta raqami: {card_number}\n\n"
            "To‘lovni amalga oshirgach, chekni ushbu botga yuboring.\n\n"
            "Reklama faqat to‘lov administrator tomonidan tasdiqlangandan so‘ng joylashtiriladi."
        )
        user_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧾 To‘lov chekini yuborish", callback_data=f"user_send_receipt:{req.id}")],
        ])
        try:
            await callback.bot.send_message(
                chat_id=user_db.telegram_id,
                text=payment_text,
                reply_markup=user_kb
            )
        except Exception as e:
            logger.error(f"Failed to deliver payment instructions to user {user_db.telegram_id}: {e}")

    await callback.answer("To‘lov ko‘rsatmalari foydalanuvchiga yuborildi.")


@router.callback_query(F.data == "adm_price_cancel")
async def handle_admin_price_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Narx belgilash bekor qilindi.")
    await callback.answer()


# =========================================================================
# 2. USER RECEIPT SUBMISSION WORKFLOW (Section 15)
# =========================================================================

@router.callback_query(F.data.startswith("user_send_receipt:"))
async def handle_user_start_receipt(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    await state.set_state(UserReceiptStates.submitting_receipt)
    await state.update_data(receipt_req_id=req_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="user_receipt_cancel")]
    ])
    await callback.message.reply(
        f"🧾 <b>TO‘LOV CHEKINI YUBORISH</b>\n\n"
        f"So‘rov raqami: <code>{req.request_number}</code>\n"
        f"To‘lov summasi: <b>{req.price:,} so‘m</b>\n\n".replace(",", " ") +
        f"Iltimos, amalga oshirilgan to‘lov chekining fotosuratini yoki PDF faylini yuboring:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("user_pay:"))
async def handle_user_pay_shortcut(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    cardholder = req.cardholder or settings.AD_CARDHOLDER_NAME
    card_number = req.card_number or settings.AD_PAYMENT_CARD

    payment_text = (
        "Reklama e’loningiz ko‘rib chiqildi.\n\n"
        f"So‘rov raqami: {req.request_number}\n"
        f"Reklama narxi: {req.price:,} so‘m\n\n".replace(",", " ") +
        "To‘lov ma’lumotlari:\n"
        f"Karta egasi: {cardholder}\n"
        f"Karta raqami: {card_number}\n\n"
        "To‘lovni amalga oshirgach, chekni ushbu botga yuboring.\n\n"
        "Reklama faqat to‘lov administrator tomonidan tasdiqlangandan so‘ng joylashtiriladi."
    )
    user_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧾 To‘lov chekini yuborish", callback_data=f"user_send_receipt:{req.id}")],
        [InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="menu:back_to_start")]
    ])
    await callback.message.edit_text(payment_text, reply_markup=user_kb)
    await callback.answer()


@router.message(UserReceiptStates.submitting_receipt, F.photo | F.document)
async def handle_receipt_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    req_id = data.get("receipt_req_id")
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await message.reply("So‘rov topilmadi.")
        await state.clear()
        return

    user = message.from_user
    user_db = await UserRepository.get_by_telegram_id(session, user.id)

    # Extract file details
    file_id = None
    file_unique_id = None
    file_type = "PHOTO"
    file_bytes = None

    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        file_type = "PHOTO"
    elif message.document:
        doc = message.document
        file_id = doc.file_id
        file_unique_id = doc.file_unique_id
        file_type = "DOCUMENT"

    # Compute receipt hash for duplicate prevention
    try:
        f_info = await message.bot.get_file(file_id)
        buf = io.BytesIO()
        await message.bot.download_file(f_info.file_path, buf)
        file_bytes = buf.getvalue()
        receipt_hash = hashlib.sha256(file_bytes).hexdigest()
    except Exception as hash_err:
        logger.debug(f"Could not download receipt for hashing: {hash_err}")
        receipt_hash = hashlib.sha256(f"{file_unique_id}_{user.id}".encode()).hexdigest()

    # Record Payment in DB
    payment = Payment(
        request_id=req.id,
        user_id=user_db.id if user_db else 1,
        amount=req.price,
        receipt_file_id=file_id,
        receipt_file_unique_id=file_unique_id or "",
        receipt_hash=receipt_hash,
        receipt_type=file_type,
        status="PENDING"
    )
    session.add(payment)

    # Update request status to RECEIPT_SUBMITTED
    await AdvertisingRequestRepository.update_status(session, req.id, "RECEIPT_SUBMITTED")
    await state.clear()

    # Notify User
    await message.reply(
        "✅ <b>To‘lov chekingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"So‘rov raqami: <code>{req.request_number}</code>\n\n"
        "Administrator to‘lovni tekshirib tasdiqlagach, e’loningiz guruhga avtomatik chop etiladi.",
        parse_mode="HTML"
    )

    # Notify Administrators (Section 15)
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To‘lovni tasdiqlash", callback_data=f"adm_pay_ok:{req.id}"),
            InlineKeyboardButton(text="❌ To‘lovni rad etish", callback_data=f"adm_pay_rej:{req.id}"),
        ],
        [
            InlineKeyboardButton(text="👁 E’lonni ko‘rish", callback_data=f"adm_view:{req.id}")
        ]
    ])

    admin_notice = (
        f"🧾 <b>YANGI TO‘LOV CHEKI KELIB TUSHDI!</b>\n\n"
        f"So‘rov raqami: <code>{req.request_number}</code>\n"
        f"Foydalanuvchi: {html.escape(user.full_name or '')} (@{user.username or 'yoq'})\n"
        f"Kutilayotgan summa: <b>{req.price:,} so‘m</b>\n\n".replace(",", " ") +
        f"Iltimos, chekni tekshirib to‘lovni tasdiqlang yoki rad eting:"
    )

    for a_id in settings.all_admin_ids:
        try:
            if file_type == "PHOTO":
                await message.bot.send_photo(chat_id=a_id, photo=file_id, caption=admin_notice, parse_mode="HTML", reply_markup=admin_kb)
            else:
                await message.bot.send_document(chat_id=a_id, document=file_id, caption=admin_notice, parse_mode="HTML", reply_markup=admin_kb)
        except Exception as e:
            logger.error(f"Failed to alert admin {a_id} about receipt: {e}")


@router.callback_query(F.data == "user_receipt_cancel")
async def handle_user_receipt_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Chek yuborish bekor qilindi.")
    await callback.answer()


# =========================================================================
# 3. ADMIN PAYMENT APPROVAL & AUTOMATIC PUBLICATION (Section 16)
# =========================================================================

@router.callback_query(F.data.startswith("adm_pay_ok:"))
async def handle_admin_approve_payment(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_id = callback.from_user.id
    if admin_id not in settings.all_admin_ids:
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    # Idempotency check: prevent duplicate approvals
    if req.status in ("PAYMENT_APPROVED", "PUBLISHED", "READY_TO_PUBLISH"):
        await callback.answer("Ushbu to‘lov allaqachon tasdiqlangan!", show_alert=True)
        return

    # Update status to PAYMENT_APPROVED
    await AdvertisingRequestRepository.update_status(session, req.id, "PAYMENT_APPROVED")

    # 1. Deliver user confirmation (Section 16 exact text)
    user_db = await UserRepository.get_by_id(session, req.user_id)
    if user_db:
        user_msg = (
            "To‘lovingiz tasdiqlandi.\n\n"
            f"So‘rov raqami: {req.request_number}\n\n"
            "Reklamangiz tasdiqlandi va tez orada guruhga joylashtiriladi."
        )
        try:
            await callback.bot.send_message(chat_id=user_db.telegram_id, text=user_msg)
        except Exception as e:
            logger.error(f"Failed to send confirmation to user: {e}")

    # 2. Publish advertisement to configured group
    await AdvertisingRequestRepository.update_status(session, req.id, "READY_TO_PUBLISH")
    pub_ok, msg_id, pub_text = await PublicationService.publish_advertising_request(
        bot=callback.bot,
        session=session,
        req=req
    )

    if pub_ok:
        await AdvertisingRequestRepository.update_status(session, req.id, "PUBLISHED")
        success_text = (
            f"✅ <b>To‘lov tasdiqlandi va reklama guruhga joylashtirildi!</b>\n\n"
            f"So‘rov: <code>{req.request_number}</code>\n"
            f"Guruh xabar ID: <code>{msg_id}</code>"
        )
        await callback.message.edit_caption(caption=success_text, parse_mode="HTML") if callback.message.caption else await callback.message.edit_text(success_text, parse_mode="HTML")

        # Notify advertiser
        if user_db:
            try:
                await callback.bot.send_message(
                    chat_id=user_db.telegram_id,
                    text=f"🚀 <b>Reklamangiz guruhga muvaffaqiyatli joylashtirildi!</b>\n\nSo‘rov raqami: <code>{req.request_number}</code>",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    else:
        await AdvertisingRequestRepository.update_status(session, req.id, "PUBLICATION_FAILED")
        fail_text = f"⚠️ <b>To‘lov tasdiqlandi, ammo guruhga joylashtirishda xatolik yuz berdi:</b> {pub_text}"
        await callback.message.edit_caption(caption=fail_text, parse_mode="HTML") if callback.message.caption else await callback.message.edit_text(fail_text, parse_mode="HTML")

    await callback.answer("Amal muvaffaqiyatli bajarildi.")


@router.callback_query(F.data.startswith("adm_pay_rej:"))
async def handle_admin_reject_payment_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    admin_id = callback.from_user.id
    if admin_id not in settings.all_admin_ids:
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    await state.set_state(AdminReqPricingStates.entering_payment_reject_reason)
    await state.update_data(reject_req_id=req_id)

    await callback.message.reply(
        "❌ <b>To‘lovni rad etish sababini kiriting:</b>\n"
        "(masalan: <i>Chek summasi to‘liq emas yoki chek qalbaki</i>):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminReqPricingStates.entering_payment_reject_reason, F.text)
async def handle_admin_reject_payment_reason(message: Message, state: FSMContext, session: AsyncSession) -> None:
    admin_id = message.from_user.id
    if admin_id not in settings.all_admin_ids:
        return

    data = await state.get_data()
    req_id = data.get("reject_req_id")
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await message.reply("So‘rov topilmadi.")
        await state.clear()
        return

    reason = message.text.strip()
    req.status = "PAYMENT_REJECTED"
    req.rejection_reason = reason
    await session.flush()
    await state.clear()

    await message.reply(f"❌ To‘lov rad etildi. Sabab: {reason}")

    # Notify advertiser
    user_db = await UserRepository.get_by_id(session, req.user_id)
    if user_db:
        reject_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧾 Qayta chek yuborish", callback_data=f"user_send_receipt:{req.id}")]
        ])
        try:
            await message.bot.send_message(
                chat_id=user_db.telegram_id,
                text=(
                    f"⚠️ <b>To‘lovingiz qabul qilinmadi.</b>\n\n"
                    f"So‘rov raqami: <code>{req.request_number}</code>\n"
                    f"Rad etish sababi: <i>{reason}</i>\n\n"
                    f"Iltimos, haqiqiy to‘lov chekini qayta yuboring:"
                ),
                parse_mode="HTML",
                reply_markup=reject_kb
            )
        except Exception:
            pass


# =========================================================================
# 4. VIEW & GENERAL REJECT / RETURN HANDLERS
# =========================================================================

@router.callback_query(F.data.startswith("adm_view:"))
async def handle_admin_view_request(callback: CallbackQuery, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    media_items = await AdvertisingRequestRepository.get_media_items(session, req_id)
    text = (
        f"📋 <b>E’LON KO‘RINISHI (PREVIEW):</b>\n\n"
        f"So‘rov: <code>{req.request_number}</code>\n"
        f"Kategoriya: <b>{req.category_id} / {req.subcategory_id}</b>\n"
        f"Holati: <b>{req.status}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{req.preview_text or 'Matn kiritilmagan'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Rasmlar soni: {len(media_items)} ta"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Narx belgilash", callback_data=f"adm_price:{req.id}")],
        [InlineKeyboardButton(text="🌐 OLX ga chiqarish", callback_data=f"adm_olx:{req.id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_reject:{req.id}")],
    ])
    await callback.message.reply(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("adm_olx:"))
async def handle_admin_push_olx(callback: CallbackQuery, session: AsyncSession) -> None:
    admin_id = callback.from_user.id
    if admin_id not in settings.all_admin_ids:
        await callback.answer("Ruxsat berilmagan.", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    await callback.answer("🌐 OLX ga yuborish boshlandi, biroz kuting...")
    from app.services.olx_service import OlxService
    success, url, err = await OlxService.publish_request_to_olx(callback.bot, session, req)
    if success:
        await callback.message.reply(
            f"✅ <b>E’lon OLX.uz ga muvaffaqiyatli joylashtirildi!</b>\n\n"
            f"So‘rov: <code>{req.request_number}</code>\n"
            f"🔗 <a href='{url}'>OLX dagi e’lonni ko‘rish</a>",
            parse_mode="HTML"
        )
    else:
        await callback.message.reply(
            f"❌ <b>OLX ga joylashtirishda xatolik:</b>\n\n<code>{err}</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("adm_reject:"))
async def handle_admin_reject_request(callback: CallbackQuery, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[1])
    req = await AdvertisingRequestRepository.update_status(session, req_id, "CANCELLED")
    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(f"❌ So‘rov {req.request_number} rad etildi va bekor qilindi.")

    user_db = await UserRepository.get_by_id(session, req.user_id)
    if user_db:
        try:
            await callback.bot.send_message(
                chat_id=user_db.telegram_id,
                text=f"❌ <b>Reklama so‘rovingiz administrator tomonidan rad etildi.</b>\n\nSo‘rov raqami: <code>{req.request_number}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass
    await callback.answer("So‘rov rad etildi.")
