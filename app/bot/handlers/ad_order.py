import re
import io
from datetime import datetime, timezone
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models.order import Order
from app.database.models.advertisement import Advertisement
from app.database.repositories.order_repo import OrderRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.payment_repo import PaymentRepository
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.publication_service import PublicationService
from app.services.request_service import RequestService
from app.services.notification_service import NotificationService
from app.services.state_machine import get_status_label
from app.utils.logger import logger

router = Router(name="ad_order_router")


class AdOrderStates(StatesGroup):
    waiting_for_ad_content = State()
    confirm_ad_content = State()
    waiting_for_payment_receipt = State()
    select_order_for_receipt = State()


class AdminPriceStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_custom_instructions = State()
    waiting_for_reject_reason = State()


def get_user_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Reklama joylash"), KeyboardButton(text="📋 So‘rovlarim")],
            [KeyboardButton(text="ℹ️ Reklama joylashtirish tartibi"), KeyboardButton(text="❓ Yordam")]
        ],
        resize_keyboard=True
    )


# =========================================================================
# Deep Link Handler: /start ad_<ad_id>
# =========================================================================

async def handle_ad_deep_link(
    message: Message,
    ad_id: int,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """
    Handles user entering bot via deep-link from a deleted group ad: /start ad_<ad_id>
    Directs user directly to new questionnaire categories without showing price or old order.
    """
    await state.clear()
    from app.bot.handlers.questionnaire_handler import get_categories_keyboard, QuestionnaireStates
    await state.set_state(QuestionnaireStates.selecting_category)

    await message.answer(
        "Assalomu alaykum!\n\n"
        "🛡 <b>Defender Bot</b> — guruhda reklama joylashtirish xizmati.\n\n"
        "Bu yerda siz o‘z e’loningizni qulay va sifatli tarzda shakllantirishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_user_menu_keyboard()
    )

    text = (
        "📋 <b>Yangi reklama yaratish:</b>\n\n"
        "Reklama joylashtirish uchun mahsulot / xizmat turini tanlang:\n"
        "Quyidagi toifalardan birini tanlang. Bot sizdan kerakli ma’lumotlarni "
        "bosqichma-bosqich so‘rab, tayyor va chiroyli e’lon shakllantiradi:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_categories_keyboard())


# =========================================================================
# Manual Ad Submission Workflow: /reklama or Button
# =========================================================================

async def start_ad_order_workflow(message: Message, state: FSMContext) -> None:
    """Entry point for initiating a fresh advertisement ordering flow."""
    await state.set_state(AdOrderStates.waiting_for_ad_content)
    price_display = settings.AD_PRICE or "Administrator tomonidan belgilanadi"

    text = (
        "📢 <b>Guruhda reklama joylashtirish xizmati</b>\n\n"
        f"💰 <b>Mo‘ljallangan standart narx:</b> <b>{price_display}</b>\n\n"
        "Iltimos, guruhda e’lon qilmoqchi bo‘lgan reklama materialingizni yuboring:\n"
        "• Matn, rasm, video, audio, animatsiya yoki hujjat\n"
        "• Bog‘lanish uchun telefon va havolalar\n\n"
        "Barcha ma’lumotlarni <b>bitta xabarda</b> yuboring. Xabarni yuborganingizdan so‘ng tasdiqlash so‘raladi:"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad_order")]
        ]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cancel_kb)


@router.message(Command("reklama_berish"))
@router.message(Command("reklama"))
@router.message(F.text.in_([
    "📢 Reklama joylash",
    "Reklama joylash",
    "📢 Reklama yuborish",
    "📢 Reklama berish",
    "Reklama berish",
    "Reklama yuborish"
]))
async def cmd_reklama(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return
    await state.clear()
    from app.bot.handlers.questionnaire_handler import get_categories_keyboard, QuestionnaireStates
    await state.set_state(QuestionnaireStates.selecting_category)

    text = (
        "📋 <b>Reklama joylashtirish uchun mahsulot / xizmat turini tanlang:</b>\n\n"
        "Quyidagi toifalardan birini tanlang. Bot sizdan kerakli ma’lumotlarni "
        "bosqichma-bosqich so‘rab, tayyor va chiroyli e’lon shakllantiradi:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_categories_keyboard())


@router.callback_query(F.data == "start_ad_order")
async def callback_start_ad_order(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await state.clear()
        from app.bot.handlers.questionnaire_handler import get_categories_keyboard, QuestionnaireStates
        await state.set_state(QuestionnaireStates.selecting_category)
        text = (
            "📋 <b>Reklama joylashtirish uchun mahsulot / xizmat turini tanlang:</b>\n\n"
            "Quyidagi toifalardan birini tanlang. Bot sizdan kerakli ma’lumotlarni "
            "bosqichma-bosqich so‘rab, tayyor va chiroyli e’lon shakllantiradi:"
        )
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_categories_keyboard())


@router.callback_query(F.data == "cancel_ad_order")
async def cancel_ad_order(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Bekor qilindi")
    if callback.message:
        await callback.message.edit_text(
            "❌ Reklama joylashtirish jarayoni bekor qilindi.",
            reply_markup=None
        )


@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_specific_order(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await OrderService.cancel_order(session, order_id, reason="Foydalanuvchi tomonidan bekor qilindi")
    await state.clear()
    await callback.answer("Buyurtma bekor qilindi")
    if callback.message:
        await callback.message.edit_text("🚫 Ushbu reklama so‘rovi bekor qilindi.")


# =========================================================================
# User Submits Ad Content (with explicit confirmation step)
# =========================================================================

@router.message(AdOrderStates.waiting_for_ad_content)
async def process_ad_content(
    message: Message,
    state: FSMContext
) -> None:
    """Receives proposed advertising content and asks user for confirmation."""
    user = message.from_user
    if not user:
        return

    media_type = "TEXT"
    media_file_id = None
    media_file_unique_id = None

    if message.photo:
        media_type = "PHOTO"
        media_file_id = message.photo[-1].file_id
        media_file_unique_id = message.photo[-1].file_unique_id
    elif message.video:
        media_type = "VIDEO"
        media_file_id = message.video.file_id
        media_file_unique_id = message.video.file_unique_id
    elif message.animation:
        media_type = "ANIMATION"
        media_file_id = message.animation.file_id
        media_file_unique_id = message.animation.file_unique_id
    elif message.document:
        media_type = "DOCUMENT"
        media_file_id = message.document.file_id
        media_file_unique_id = message.document.file_unique_id
    elif message.audio:
        media_type = "AUDIO"
        media_file_id = message.audio.file_id
        media_file_unique_id = message.audio.file_unique_id
    elif message.voice:
        media_type = "VOICE"
        media_file_id = message.voice.file_id
        media_file_unique_id = message.voice.file_unique_id
    elif message.video_note:
        media_type = "VIDEO_NOTE"
        media_file_id = message.video_note.file_id
        media_file_unique_id = message.video_note.file_unique_id

    # Store drafted material in state
    await state.update_data(
        pending_media_type=media_type,
        pending_file_id=media_file_id,
        pending_unique_id=media_file_unique_id,
        pending_text=message.text,
        pending_caption=message.caption,
        pending_message_id=message.message_id
    )
    await state.set_state(AdOrderStates.confirm_ad_content)

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, tasdiqlayman", callback_data="confirm_ad_submission"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad_order")
    ]])

    await message.reply(
        "📝 <b>Material qabul qilindi.</b>\n\n"
        "Ushbu materialni reklama sifatida yuborishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_kb
    )


@router.callback_query(AdOrderStates.confirm_ad_content, F.data == "confirm_ad_submission")
async def cb_confirm_ad_submission(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """User confirms ad submission -> creates DB record, order, and notifies admins."""
    user = callback.from_user
    if not user:
        return

    data = await state.get_data()
    media_type = data.get("pending_media_type", "TEXT")
    media_file_id = data.get("pending_file_id")
    media_file_unique_id = data.get("pending_unique_id")
    text_val = data.get("pending_text")
    caption_val = data.get("pending_caption")
    orig_msg_id = data.get("pending_message_id", 0)

    user_db = await UserRepository.get_or_create(
        session=session,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # 1. Create Advertisement record in DB
    ad = await AdvertisementRepository.create(
        session=session,
        group_id=None,
        user_id=user_db.id,
        telegram_message_id=orig_msg_id,
        chat_id=None,
        username=user.username,
        first_name=user.first_name,
        message_type=media_type,
        media_type=media_type,
        media_file_id=media_file_id,
        media_file_unique_id=media_file_unique_id,
        text=text_val,
        caption=caption_val,
        original_text=text_val,
        original_caption=caption_val,
        detected_links=None,
        score=0,
        detection_reason="Foydalanuvchi bot orqali reklama yubordi",
        deleted=False,
        status="NEW"
    )

    # 2. Create Commercial Order
    order = await OrderService.create_order_for_ad(session, ad)
    await state.clear()
    await callback.answer("Qabul qilindi!")

    # 3. Confirmation to user (Section 9 exact template)
    user_confirm_text = (
        "Reklama materialingiz qabul qilindi.\n\n"
        f"So‘rov raqami: <code>{order.order_number}</code>\n\n"
        "Administrator materialni ko‘rib chiqib, reklama narxini sizga yuboradi."
    )
    if callback.message:
        await callback.message.edit_text(user_confirm_text, parse_mode="HTML")

    # 4. Notify all administrators (Section 6 exact template)
    alert_text = NotificationService.format_new_ad_request_alert(
        order_number=order.order_number,
        username=user.username,
        telegram_id=user.id,
        content_type=media_type,
        status="Narx belgilanmagan"
    )
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Narx belgilash", callback_data=f"set_price:{order.id}"),
            InlineKeyboardButton(text="📋 So‘rov tafsilotlari", callback_data=f"order_details:{order.id}")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_cancel_order:{order.id}")
        ]
    ])

    for admin_id in settings.all_admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=alert_text, parse_mode="HTML", reply_markup=admin_kb)
            if orig_msg_id:
                try:
                    await bot.copy_message(
                        chat_id=admin_id,
                        from_chat_id=user.id,
                        message_id=orig_msg_id
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Adminga reklama ma'lumotlarini yetkazishda xatolik ({admin_id}): {e}")


# =========================================================================
# Admin Sets Price Workflow (Section 6.1)
# =========================================================================

@router.callback_query(F.data.startswith("set_price:"))
async def cb_admin_set_price(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    await state.set_state(AdminPriceStates.waiting_for_price)
    await state.update_data(admin_target_order_id=order_id)

    await callback.answer()
    if callback.message:
        await callback.message.reply(
            f"💰 <b>So‘rov #{order_id} uchun narx belgilash</b>\n\n"
            f"Iltimos, reklama narxini O‘zbek so‘mida raqam bilan yozing (masalan: <code>150 000</code> yoki <code>100000</code>):",
            parse_mode="HTML"
        )


@router.message(AdminPriceStates.waiting_for_price)
async def process_admin_price(message: Message, session: AsyncSession, state: FSMContext) -> None:
    user = message.from_user
    if not user or user.id not in settings.all_admin_ids:
        return

    raw_text = message.text or ""
    clean_num = re.sub(r"[^\d]", "", raw_text)
    if not clean_num or int(clean_num) <= 0:
        await message.reply("⚠️ Iltimos, to‘g‘ri summa kiriting (faqat musbat raqamlar):")
        return

    price = int(clean_num)
    min_p = settings.MIN_AD_PRICE
    max_p = settings.MAX_AD_PRICE
    if price < min_p or price > max_p:
        await message.reply(
            f"⚠️ Narx chegaralardan tashqarida! Minimal: {min_p:,} so‘m, Maksimal: {max_p:,} so‘m.".replace(",", " ")
        )
        return

    data = await state.get_data()
    order_id = data.get("admin_target_order_id")

    if not order_id:
        await message.reply("⚠️ So‘rov identifikatori topilmadi.")
        await state.clear()
        return

    order = await OrderService.get_order_by_id(session, order_id)
    if not order:
        await message.reply("⚠️ So‘rov bazadan topilmadi.")
        await state.clear()
        return

    card = settings.AD_PAYMENT_CARD
    cardholder = settings.AD_CARDHOLDER_NAME
    formatted_price = f"{price:,} so‘m".replace(",", " ")

    confirm_price_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash va mijozga yuborish", callback_data=f"confirm_price:{order.id}:{price}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_price_setting")
        ]
    ])

    await message.reply(
        f"📋 <b>Narx tasdig‘i:</b>\n\n"
        f"<b>So‘rov raqami:</b> <code>{order.order_number}</code>\n"
        f"<b>Reklama narxi:</b> <b>{formatted_price}</b>\n"
        f"<b>Karta egasi:</b> <code>{cardholder}</code>\n"
        f"<b>Karta raqami:</b> <code>{card}</code>\n\n"
        f"Ushbu to‘lov rekvizitlarini mijozga jo‘natishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=confirm_price_kb
    )


@router.callback_query(F.data == "cancel_price_setting")
async def cb_cancel_price_setting(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Bekor qilindi")
    if callback.message:
        await callback.message.edit_text("❌ Narx belgilash bekor qilindi.")


@router.callback_query(F.data.startswith("confirm_price:"))
async def cb_confirm_price(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    parts = callback.data.split(":")
    order_id = int(parts[1])
    price = int(parts[2])
    await state.clear()

    card = settings.AD_PAYMENT_CARD
    cardholder = settings.AD_CARDHOLDER_NAME

    order = await OrderService.set_order_price(session, order_id=order_id, price=price, card_number=card)
    if not order:
        await callback.answer("So‘rov topilmadi!", show_alert=True)
        return

    formatted_price = f"{price:,} so‘m".replace(",", " ")

    # Record Audit Log
    await AuditRepository.create(
        session=session,
        event_type="price_set",
        group_id=order.group_id,
        user_id=order.user_id,
        details=f"order={order.order_number} | price={price} | admin={user.id}"
    )

    await callback.answer("✅ Narx belgilandi!")
    if callback.message:
        await callback.message.edit_text(
            f"✅ <b>Narx muvaffaqiyatli belgilandi!</b>\n\n"
            f"So‘rov: <code>{order.order_number}</code>\n"
            f"Narx: <b>{formatted_price}</b>\n"
            f"Karta egasi: <b>{cardholder}</b>\n"
            f"Karta: <code>{card}</code>\n\n"
            f"Mijozga to‘lov rekvizitlari jo‘natildi.",
            parse_mode="HTML"
        )

    # Deliver exact private message to advertiser (Section 6.1)
    advertiser_user_id = order.user.telegram_id if order.user else None
    if advertiser_user_id:
        user_text = (
            "Reklamangiz qabul qilindi va narxi belgilandi.\n\n"
            f"So‘rov raqami: <code>{order.order_number}</code>\n"
            f"Reklama narxi: <b>{formatted_price}</b>\n\n"
            "To‘lov uchun:\n"
            f"Karta egasi: <code>{cardholder}</code>\n"
            f"Karta raqami: <code>{card}</code>\n\n"
            "To‘lovni amalga oshirgach, to‘lov chekini ushbu botga yuboring.\n\n"
            "Eslatma: Reklama to‘lov administrator tomonidan tasdiqlangandan keyingina joylashtiriladi."
        )
        try:
            await bot.send_message(
                chat_id=advertiser_user_id,
                text=user_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga narx bildirishnomasini jo'natishda xatolik ({advertiser_user_id}): {e}")


# =========================================================================
# User Submits Payment Receipt (Section 7)
# =========================================================================

@router.message(F.photo | F.document)
async def process_payment_receipt(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """
    Handles payment receipt submission.
    Validates file size (max 20MB).
    If user has multiple active requests in AWAITING_PAYMENT, prompts user to select which one!
    """
    if message.chat.type != "private":
        return

    user = message.from_user
    if not user:
        return

    # Check if admin is sending files without receipt state (ignore)
    cur_state = await state.get_state()
    if user.id in settings.all_admin_ids and not cur_state:
        return

    # Check file size if document
    if message.document and message.document.file_size and message.document.file_size > 20 * 1024 * 1024:
        await message.reply("⚠️ Fayl hajmi juda katta (maksimal 20 MB). Iltimos, kichikroq o‘lchamdagi chek yuboring.")
        return

    user_db = await UserRepository.get_by_telegram_id(session, user.id)
    if not user_db:
        return

    # Extract file details
    file_id = None
    file_unique_id = None
    receipt_type = "PHOTO"
    if message.photo:
        highest = message.photo[-1]
        file_id = highest.file_id
        file_unique_id = highest.file_unique_id
        receipt_type = "PHOTO"
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        receipt_type = "DOCUMENT"

    # Download bytes for deterministic hash deduplication
    file_bytes = None
    try:
        file_io = io.BytesIO()
        await bot.download(file_id, destination=file_io)
        file_bytes = file_io.getvalue()
    except Exception as dl_err:
        logger.warning(f"Could not download receipt bytes for hashing: {dl_err}")

    # Check active payment orders
    active_orders = await RequestService.get_user_active_payment_orders(session, user_db.id)

    if not active_orders:
        await message.answer(
            "⚠️ <b>Sizda to‘lov kutilayotgan faol reklama so‘rovi topilmadi.</b>\n\n"
            "Yangi reklama berish uchun quyidagi menyudan <b>«📢 Reklama joylash»</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_user_menu_keyboard()
        )
        return

    # If user has multiple active orders awaiting payment -> ask which order (Section 7)
    if len(active_orders) > 1:
        # Cache receipt in state and prompt selection
        await state.set_state(AdOrderStates.select_order_for_receipt)
        await state.update_data(
            pending_receipt_file_id=file_id,
            pending_receipt_unique_id=file_unique_id,
            pending_receipt_type=receipt_type,
            pending_receipt_bytes=file_bytes
        )
        buttons = []
        for o in active_orders:
            p_text = f"{o.price:,} so‘m".replace(",", " ") if o.price else "Narxsiz"
            buttons.append([InlineKeyboardButton(
                text=f"📋 {o.order_number} ({p_text})",
                callback_data=f"attach_rcpt:{o.id}"
            )])
        buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad_order")])

        await message.reply(
            "Sizda bir nechta faol reklama so‘rovi mavjud. Ushbu to‘lov cheki qaysi so‘rovga tegishli?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return

    # Exactly 1 active order -> attach directly
    target_order = active_orders[0]
    await _execute_receipt_attachment(
        bot=bot,
        session=session,
        order=target_order,
        user=user,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_bytes=file_bytes,
        receipt_type=receipt_type,
        message_to_reply=message
    )
    await state.clear()


@router.callback_query(AdOrderStates.select_order_for_receipt, F.data.startswith("attach_rcpt:"))
async def cb_attach_receipt_to_selected_order(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
) -> None:
    order_id = int(callback.data.split(":")[1])
    order = await OrderService.get_order_by_id(session, order_id)
    if not order:
        await callback.answer("So‘rov topilmadi!", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    file_id = data.get("pending_receipt_file_id")
    file_unique_id = data.get("pending_receipt_unique_id")
    file_bytes = data.get("pending_receipt_bytes")
    receipt_type = data.get("pending_receipt_type", "PHOTO")

    await state.clear()
    await callback.answer()

    await _execute_receipt_attachment(
        bot=bot,
        session=session,
        order=order,
        user=callback.from_user,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_bytes=file_bytes,
        receipt_type=receipt_type,
        callback_to_edit=callback
    )


async def _execute_receipt_attachment(
    bot: Bot,
    session: AsyncSession,
    order: Order,
    user,
    file_id: str,
    file_unique_id: str,
    file_bytes: bytes | None,
    receipt_type: str,
    message_to_reply: Message | None = None,
    callback_to_edit: CallbackQuery | None = None
) -> None:
    """Attaches receipt, updates status to RECEIPT_SUBMITTED, notifies user and admins."""
    payment, is_duplicate = await PaymentService.submit_receipt(
        session=session,
        order=order,
        receipt_file_id=file_id,
        receipt_file_unique_id=file_unique_id,
        file_bytes=file_bytes,
        receipt_type=receipt_type
    )

    user_reply = (
        "✅ <b>To‘lov chekingiz qabul qilindi va tekshirish uchun adminga yuborildi!</b>\n\n"
        f"So‘rov raqami: <code>{order.order_number}</code>\n"
        "Administrator tomonidan tasdiqlangach, reklamangiz guruhda e’lon qilinadi."
    )
    if message_to_reply:
        await message_to_reply.answer(user_reply, parse_mode="HTML", reply_markup=get_user_menu_keyboard())
    elif callback_to_edit and callback_to_edit.message:
        await callback_to_edit.message.edit_text(user_reply, parse_mode="HTML")

    # Notify all admins with Section 7 review buttons:
    # To'lovni tasdiqlash, Rad etish, Chekni ko'rish, So'rov tafsilotlari
    dup_warning = "\n⚠️ <b>DIQQAT: Ushbu chek avval ishlatilgan (DUBLIKAT CHEK)!</b>\n" if is_duplicate else ""
    username_str = f"@{user.username}" if user.username else "mavjud emas"
    price_str = f"{order.price:,} so‘m".replace(",", " ") if order.price else "Ko'rsatilmagan"

    admin_text = (
        f"💳 <b>YANGI TO‘LOV CHEKI KELDI!</b>\n"
        f"{dup_warning}\n"
        f"<b>So‘rov:</b> <code>{order.order_number}</code>\n"
        f"<b>Mijoz:</b> {user.full_name} ({username_str})\n"
        f"<b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"<b>Kutilgan summa:</b> <b>{price_str}</b>\n"
        f"<b>Karta:</b> <code>{order.card_number or settings.AD_PAYMENT_CARD}</code>\n"
        f"<b>Vaqt:</b> {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}\n\n"
        f"To‘lovni tasdiqlaysizmi yoki rad etasizmi?"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To‘lovni tasdiqlash", callback_data=f"ad_approve:{order.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ad_reject:{order.id}")
        ],
        [
            InlineKeyboardButton(text="🧾 Chekni ko‘rish", callback_data=f"view_receipt:{order.id}"),
            InlineKeyboardButton(text="📋 So‘rov tafsilotlari", callback_data=f"order_details:{order.id}")
        ]
    ])

    for admin_id in settings.all_admin_ids:
        try:
            if receipt_type == "PHOTO":
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=admin_text,
                    parse_mode="HTML",
                    reply_markup=admin_kb
                )
            else:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=admin_text,
                    parse_mode="HTML",
                    reply_markup=admin_kb
                )
        except Exception as e:
            logger.error(f"Adminga to'lov chekini yuborishda xatolik ({admin_id}): {e}")


# =========================================================================
# Admin Approves Payment & Publishes Ad (Section 7 & 8)
# =========================================================================

@router.callback_query(F.data.startswith("ad_approve:"))
async def cb_admin_approve_payment(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession
) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    # 1. Atomically approve payment (idempotent, concurrency-safe)
    success, order, msg = await PaymentService.approve_payment(session, order_id, admin_id=user.id)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    # Record Audit Log
    await AuditRepository.create(
        session=session,
        event_type="payment_approved",
        group_id=order.group_id,
        user_id=order.user_id,
        details=f"order={order.order_number} | admin={user.id}"
    )

    await callback.answer("✅ To‘lov tasdiqlandi!")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # 2. Confirm to advertiser (Section 8 exact template)
    advertiser_id = order.user.telegram_id if order.user else None
    if advertiser_id:
        user_congrats = (
            "To‘lovingiz administrator tomonidan tasdiqlandi.\n\n"
            f"So‘rov raqami: <code>{order.order_number}</code>\n\n"
            "Reklamangiz tasdiqlandi va tez orada guruhga joylashtiriladi."
        )
        try:
            await bot.send_message(chat_id=advertiser_id, text=user_congrats, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Foydalanuvchiga tasdiq xabarini yetkazishda xatolik ({advertiser_id}): {e}")

    # 3. Automatically publish advertisement to group
    ad = order.advertisement
    pub_ok, pub_msg_id, pub_err = await PublicationService.publish_advertisement(
        bot=bot,
        session=session,
        ad=ad,
        order=order
    )

    status_extra = "va reklama muvaffaqiyatli guruhga chop etildi!" if pub_ok else f"(Chop etishda xatolik: {pub_err})"
    retry_kb = None
    if not pub_ok:
        retry_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Qayta chop etish", callback_data=f"retry_publish:{order.id}")
        ]])

    if callback.message:
        await callback.message.reply(
            f"✅ <b>To‘lov tasdiqlandi</b> {status_extra}\n"
            f"So‘rov: <code>{order.order_number}</code>",
            parse_mode="HTML",
            reply_markup=retry_kb
        )


@router.callback_query(F.data.startswith("retry_publish:"))
async def cb_retry_publish(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    order = await OrderService.get_order_by_id(session, order_id)
    if not order or not order.advertisement:
        await callback.answer("So‘rov topilmadi!", show_alert=True)
        return

    pub_ok, pub_msg_id, pub_err = await PublicationService.publish_advertisement(
        bot=bot,
        session=session,
        ad=order.advertisement,
        order=order
    )
    if pub_ok:
        await callback.answer("Muvaffaqiyatli chop etildi!")
        if callback.message:
            await callback.message.edit_text(
                f"🚀 <b>Reklama muvaffaqiyatli guruhga chop etildi!</b>\n"
                f"So‘rov: <code>{order.order_number}</code>",
                parse_mode="HTML"
            )
    else:
        await callback.answer(f"Xatolik: {pub_err}", show_alert=True)


# =========================================================================
# Admin Rejects Payment (Section 7)
# =========================================================================

@router.callback_query(F.data.startswith("ad_reject:"))
async def cb_admin_reject_payment(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    reason_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Noto‘g‘ri summa", callback_data=f"rej_res:{order_id}:Noto‘g‘ri summa to‘langan")],
        [InlineKeyboardButton(text="Chek ko‘rinmayapti / Soxta", callback_data=f"rej_res:{order_id}:Chek ko‘rinmayapti yoki soxta")],
        [InlineKeyboardButton(text="Boshqa kartaga to‘langan", callback_data=f"rej_res:{order_id}:Boshqa karta rekvizitiga to‘langan")],
        [InlineKeyboardButton(text="✍️ Boshqa sabab yozish", callback_data=f"rej_custom:{order_id}")]
    ])
    await callback.answer()
    if callback.message:
        await callback.message.reply(
            f"❌ <b>So‘rov #{order_id} to‘lovini rad etish sababini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=reason_kb
        )


@router.callback_query(F.data.startswith("rej_custom:"))
async def cb_admin_reject_custom(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.set_state(AdminPriceStates.waiting_for_reject_reason)
    await state.update_data(reject_order_id=order_id)
    await callback.answer()
    if callback.message:
        await callback.message.reply("Iltimos, rad etish sababini matn ko‘rinishida yozing:")


@router.message(AdminPriceStates.waiting_for_reject_reason)
async def process_custom_reject_reason(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext
) -> None:
    user = message.from_user
    if not user or user.id not in settings.all_admin_ids:
        return

    reason = (message.text or "").strip()
    data = await state.get_data()
    order_id = data.get("reject_order_id")
    await state.clear()

    if not order_id:
        await message.reply("So‘rov topilmadi.")
        return

    await _apply_payment_rejection(bot, session, order_id, user.id, reason, reply_msg=message)


@router.callback_query(F.data.startswith("rej_res:"))
async def cb_admin_apply_rejection(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession
) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        return

    parts = callback.data.split(":", 2)
    order_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "To‘lov cheki qabul qilinmadi"

    await callback.answer("Rad etildi")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _apply_payment_rejection(bot, session, order_id, user.id, reason, reply_msg=callback.message)


async def _apply_payment_rejection(
    bot: Bot,
    session: AsyncSession,
    order_id: int,
    admin_id: int,
    reason: str,
    reply_msg: Message | None = None
) -> None:
    success, order, msg = await PaymentService.reject_payment(
        session=session,
        order_id=order_id,
        admin_id=admin_id,
        reason=reason
    )

    # Record Audit Log
    await AuditRepository.create(
        session=session,
        event_type="payment_rejected",
        group_id=order.group_id if order else None,
        user_id=order.user_id if order else None,
        details=f"order={order.order_number if order else order_id} | reason={reason} | admin={admin_id}"
    )

    if reply_msg:
        await reply_msg.reply(
            f"❌ <b>To‘lov rad etildi.</b>\n"
            f"So‘rov: <code>{order.order_number if order else order_id}</code>\n"
            f"Sabab: <b>{reason}</b>",
            parse_mode="HTML"
        )

    # Notify advertiser (Section 7 exact template)
    if order and order.user:
        advertiser_id = order.user.telegram_id
        user_alert = (
            "To‘lov cheki tasdiqlanmadi.\n\n"
            f"So‘rov raqami: <code>{order.order_number}</code>\n"
            f"Sabab: <b>{reason}</b>\n\n"
            "Iltimos, to‘lov ma’lumotlarini tekshiring va zarur bo‘lsa, yangi chek yuboring."
        )
        try:
            await bot.send_message(chat_id=advertiser_id, text=user_alert, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Foydalanuvchiga rad etish xabarini yetkazishda xatolik ({advertiser_id}): {e}")


# =========================================================================
# View Receipt & Order Details Actions (Section 7 & 10)
# =========================================================================

@router.callback_query(F.data.startswith("view_receipt:"))
async def cb_view_receipt(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    payments = await PaymentRepository.get_by_order_id(session, order_id)
    if not payments:
        await callback.answer("To‘lov cheki topilmadi!", show_alert=True)
        return

    latest_payment = payments[-1]
    await callback.answer()
    try:
        if latest_payment.receipt_type == "PHOTO":
            await bot.send_photo(
                chat_id=user.id,
                photo=latest_payment.receipt_file_id,
                caption=f"🧾 <b>So‘rov #{order_id} to‘lov cheki</b>\nHolat: {latest_payment.status}",
                parse_mode="HTML"
            )
        else:
            await bot.send_document(
                chat_id=user.id,
                document=latest_payment.receipt_file_id,
                caption=f"🧾 <b>So‘rov #{order_id} to‘lov hujjati</b>\nHolat: {latest_payment.status}",
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.reply(f"Chekni ochishda xatolik: {e}")


@router.callback_query(F.data.startswith("order_details:"))
async def cb_order_details(callback: CallbackQuery, session: AsyncSession) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    order = await OrderService.get_order_by_id(session, order_id)
    if not order:
        await callback.answer("So‘rov topilmadi!", show_alert=True)
        return

    ad = order.advertisement
    u = order.user
    status_label = get_status_label(order.status)
    price_str = f"{order.price:,} so‘m".replace(",", " ") if order.price else "Belgilanmagan"
    created_str = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "Noma'lum"
    pub_str = order.published_at.strftime("%d.%m.%Y %H:%M") if order.published_at else "Chop etilmagan"

    ad_content = (ad.original_caption or ad.caption or ad.original_text or ad.text or "[Media]") if ad else "Noma'lum"

    text = (
        f"📋 <b>SO‘ROV TAFSILOTLARI</b>\n\n"
        f"<b>So‘rov:</b> <code>{order.order_number}</code> (ID: <code>{order.id}</code>)\n"
        f"<b>Holati:</b> {status_label}\n"
        f"<b>Narx:</b> {price_str}\n"
        f"<b>Mijoz:</b> {u.first_name if u else ''} (@{u.username if u and u.username else 'anon'}) ID: <code>{u.telegram_id if u else 0}</code>\n"
        f"<b>Kontent turi:</b> {ad.media_type if ad else 'TEXT'}\n"
        f"<b>Yaratilgan:</b> {created_str}\n"
        f"<b>Chop etilgan:</b> {pub_str}\n\n"
        f"<b>Reklama matni:</b>\n<i>{ad_content[:300]}</i>"
    )

    action_buttons = []
    if order.status in ("NEW", "CREATED", "AWAITING_PRICE", "PRICE_PENDING"):
        action_buttons.append([InlineKeyboardButton(text="💰 Narx belgilash", callback_data=f"set_price:{order.id}")])
    if order.status in ("RECEIPT_SUBMITTED", "PAYMENT_REVIEW"):
        action_buttons.append([
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ad_approve:{order.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ad_reject:{order.id}")
        ])
        action_buttons.append([InlineKeyboardButton(text="🧾 Chekni ko‘rish", callback_data=f"view_receipt:{order.id}")])
    if order.status == "PUBLICATION_FAILED":
        action_buttons.append([InlineKeyboardButton(text="🔄 Qayta chop etish", callback_data=f"retry_publish:{order.id}")])
    if order.status not in ("PUBLISHED", "CANCELLED", "EXPIRED"):
        action_buttons.append([InlineKeyboardButton(text="🚫 Bekor qilish", callback_data=f"admin_cancel_order:{order.id}")])

    action_buttons.append([InlineKeyboardButton(text="⬅️ Yopish", callback_data="close_details")])

    await callback.answer()
    if callback.message:
        await callback.message.reply(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=action_buttons))


@router.callback_query(F.data == "close_details")
async def cb_close_details(callback: CallbackQuery) -> None:
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_cancel_order:"))
async def cb_admin_cancel_order(callback: CallbackQuery, session: AsyncSession) -> None:
    user = callback.from_user
    if not user or user.id not in settings.all_admin_ids:
        await callback.answer("Faqat adminlar uchun!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    order = await OrderService.cancel_order(session, order_id, reason=f"Admin {user.id} tomonidan bekor qilindi")
    await callback.answer("So‘rov bekor qilindi!")
    if callback.message:
        await callback.message.reply(f"🚫 <b>So‘rov {order.order_number if order else order_id} bekor qilindi.</b>", parse_mode="HTML")


# =========================================================================
# Admin Text Approval: "tasdiqlandi" / "tasdiq" on Reply
# =========================================================================

@router.message(F.text.casefold().in_([
    "tasdiqlandi", "tasdiq", "tasdiqlayman", "ok", "to'lov tasdiqlandi", "tolov tasdiqlandi"
]))
async def handle_admin_text_approval(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Allows admin to reply with text 'tasdiqlandi' to approve payment."""
    if not message.from_user or message.from_user.id not in settings.all_admin_ids:
        return

    reply_to = message.reply_to_message
    if not reply_to:
        await message.reply(
            "ℹ️ To‘lovni matn orqali tasdiqlash uchun bot yuborgan chek xabariga <b>Reply</b> qilib "
            "<code>tasdiqlandi</code> deb yozing yoki xabar ostidagi <b>[To‘lovni tasdiqlash]</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    search_text = f"{reply_to.text or ''} {reply_to.caption or ''}"
    order_num_match = re.search(r'AD-\d{4}-\d+', search_text)
    order_id_match = re.search(r'(?:Buyurtma|Order|So‘rov)\s*(?:#|ID:?)\s*<code>?(\d+)</code>?', search_text, re.IGNORECASE)

    order = None
    if order_num_match:
        order = await OrderService.get_order_by_number(session, order_num_match.group(0))
    elif order_id_match:
        order = await OrderService.get_order_by_id(session, int(order_id_match.group(1)))

    if not order:
        await message.reply("⚠️ Ushbu xabardan so‘rov aniqlanmadi. Iltimos, xabar ostidagi tugmani bosing.")
        return

    success, order, msg = await PaymentService.approve_payment(session, order.id, admin_id=message.from_user.id)
    if not success:
        await message.reply(f"⚠️ {msg}")
        return

    advertiser_id = order.user.telegram_id if order.user else None
    if advertiser_id:
        user_congrats = (
            "To‘lovingiz administrator tomonidan tasdiqlandi.\n\n"
            f"So‘rov raqami: <code>{order.order_number}</code>\n\n"
            "Reklamangiz tasdiqlandi va tez orada guruhga joylashtiriladi."
        )
        try:
            await bot.send_message(chat_id=advertiser_id, text=user_congrats, parse_mode="HTML")
        except Exception:
            pass

    pub_ok, pub_id, pub_err = await PublicationService.publish_advertisement(
        bot=bot,
        session=session,
        ad=order.advertisement,
        order=order
    )
    status_extra = "va reklama guruhga chop etildi!" if pub_ok else f"(Chop etishda ogohlantirish: {pub_err})"

    await message.reply(
        f"✅ <b>To‘lov tasdiqlandi</b> {status_extra}\n"
        f"So‘rov: <code>{order.order_number}</code>",
        parse_mode="HTML"
    )


# =========================================================================
# User Views Active Requests: /myorders, "So‘rovlarim", "📋 Buyurtma holati"
# =========================================================================

@router.message(Command("myorders"))
@router.message(F.text.in_(["📋 So‘rovlarim", "So‘rovlarim", "📋 Buyurtma holati", "📋 Buyurtmalarim"]))
async def cmd_my_orders(message: Message, session: AsyncSession) -> None:
    if message.chat.type != "private":
        return

    user = message.from_user
    if not user:
        return

    user_db = await UserRepository.get_by_telegram_id(session, user.id)
    if not user_db:
        await message.answer("Sizda hali hech qanday reklama so‘rovi mavjud emas.")
        return

    orders = await RequestService.get_user_requests(session, user_db.id, limit=10)
    if not orders:
        await message.answer(
            "📋 <b>Sizda hali so‘rovlar mavjud emas.</b>\n\n"
            "Reklama joylashtirish uchun <b>«📢 Reklama joylash»</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    text_lines = ["📋 <b>SIZNING REKLAMA SO‘ROVLARINGIZ:</b>\n"]
    for o in orders:
        status_label = get_status_label(o.status)
        price_str = f"{o.price:,} so‘m".replace(",", " ") if o.price else "Belgilanmoqda"
        created_str = o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else ""
        ad_type = o.advertisement.media_type if o.advertisement else "TEXT"
        pub_status = "Chop etilgan" if o.status == "PUBLISHED" else "Kutilmoqda"
        text_lines.append(
            f"• <b>{o.order_number}</b>\n"
            f"  Turi: <b>{ad_type}</b> | Narx: <b>{price_str}</b>\n"
            f"  Holat: <b>{status_label}</b> | Guruh: <i>{pub_status}</i>\n"
            f"  Sana: <i>{created_str}</i>\n"
        )

    await message.answer("\n".join(text_lines), parse_mode="HTML")


# =========================================================================
# Explanatory Guidelines: "Reklama joylashtirish tartibi" & "Yordam"
# =========================================================================

@router.message(F.text.in_(["ℹ️ Reklama joylashtirish tartibi", "Reklama joylashtirish tartibi"]))
async def handle_ad_rules_info(message: Message) -> None:
    text = (
        "ℹ️ <b>REKLAMA JOYLASHTIRISH TARTIBI:</b>\n\n"
        "1️⃣ <b>Mahsulot turini tanlash:</b>\n"
        "«📢 Reklama joylash» tugmasini bosib, mahsulotingiz yoki xizmatingiz turini tanlaysiz.\n\n"
        "2️⃣ <b>Ma’lumotlarni to‘ldirish:</b>\n"
        "Bot savollariga (sarlavha, narx, manzil, tavsif, rasmlar) javob berib, tayyor e’lonni shakllantirasiz.\n\n"
        "3️⃣ <b>Narx va to‘lov:</b>\n"
        "Administrator e’loningizni ko‘rib chiqib reklama narxini belgilaydi va karta rekvizitlarini yuboradi.\n\n"
        "4️⃣ <b>Chek yuborish va chop etish:</b>\n"
        "To‘lov chekini botga yuborasiz. Tasdiqlangach, e’loningiz darhol guruhda rasmiy chop etiladi!\n\n"
        "<i>Eslatma: Guruhda ruxsatsiz e’lon qilingan reklamalar bot tomonidan avtomatik o‘chiriladi.</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_user_menu_keyboard())


@router.message(F.text.in_(["❓ Yordam", "Yordam"]))
async def handle_user_help_menu(message: Message) -> None:
    text = (
        "❓ <b>YORDAM VA SAVOL-JAVOBLAR:</b>\n\n"
        "• <b>Qanday qilib reklama berish mumkin?</b>\n"
        "Pastdagi «📢 Reklama joylash» tugmasini bosing va mahsulot turini tanlang.\n\n"
        "• <b>So‘rovim holatini qayerdan ko‘raman?</b>\n"
        "«📋 So‘rovlarim» tugmasi orqali barcha buyurtmalaringiz va ularning holatini kuzatib borishingiz mumkin.\n\n"
        "• <b>To‘lov cheki qanday bo‘lishi kerak?</b>\n"
        "Bank ilovasi (Click, Payme, Uzum va h.k.) orqali o‘tkazilgan to‘lovning aniq skrinshotini yuborishingiz kerak.\n\n"
        "• <b>Admin bilan bog‘lanish:</b>\n"
        f"Savollaringiz bo‘lsa, @{settings.ADMIN_USERNAME.lstrip('@')} profiliga murojaat qilishingiz mumkin."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_user_menu_keyboard())
