import html
import io
import re
from typing import Optional, List, Dict, Any
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
from app.services.questionnaire.schema import FieldType, QuestionField
from app.services.questionnaire.definitions import get_categories
from app.services.questionnaire.engine import QuestionnaireEngine
from app.services.questionnaire.preview_generator import AdvertisementPreviewGenerator
from app.database.models.advertising_request import AdvertisingRequest
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.database.repositories.user_repo import UserRepository
from app.services.payment_service import PaymentService
from app.services.publication_service import PublicationService
from app.utils.logger import logger

router = Router(name="questionnaire_router")


class QuestionnaireStates(StatesGroup):
    selecting_category = State()
    selecting_subcategory = State()
    answering_questions = State()
    uploading_media = State()
    preview_confirmation = State()
    editing_field = State()
    submitting_receipt = State()


# =========================================================================
# START MENU KEYBOARD (Section 4)
# =========================================================================

def get_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard for selecting one of the 4 advertisement categories:
    1. 🏠 Uy va ko‘chmas mulk
    2. 🛋 Mebel
    3. 🪟 Jalyuzi va pardalar
    4. 📱 Boshqa mahsulotlar va texnikalar
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Uy va ko‘chmas mulk", callback_data="cat:real_estate")],
            [InlineKeyboardButton(text="🛋 Mebel", callback_data="cat:furniture")],
            [InlineKeyboardButton(text="🪟 Jalyuzi va pardalar", callback_data="cat:curtains_blinds")],
            [InlineKeyboardButton(text="📱 Boshqa mahsulotlar va texnikalar", callback_data="cat:electronics_other")],
        ]
    )


def get_start_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Returns the exact 7 requested menu buttons for the Start menu (Section 4):
    1. Uy va ko‘chmas mulk
    2. Mebel
    3. Jalyuzi va pardalar
    4. Boshqa mahsulotlar va texnikalar
    5. Mening e’lonlarim
    6. Reklama joylashtirish tartibi
    7. Yordam
    """
    keyboard = [
        [InlineKeyboardButton(text="🏠 Uy va ko‘chmas mulk", callback_data="cat:real_estate")],
        [InlineKeyboardButton(text="🛋 Mebel", callback_data="cat:furniture")],
        [InlineKeyboardButton(text="🪟 Jalyuzi va pardalar", callback_data="cat:curtains_blinds")],
        [InlineKeyboardButton(text="📱 Boshqa mahsulotlar va texnikalar", callback_data="cat:electronics_other")],
        [InlineKeyboardButton(text="📋 Mening e’lonlarim", callback_data="menu:my_requests")],
        [InlineKeyboardButton(text="ℹ️ Reklama joylashtirish tartibi", callback_data="menu:ad_rules")],
        [InlineKeyboardButton(text="❓ Yordam", callback_data="menu:help")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🛡 Admin Paneli (/admin)", callback_data="menu:admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================================================================
# 1. CATEGORY SELECTION -> SUBCATEGORIES
# =========================================================================

@router.callback_query(F.data.startswith("cat:"))
async def handle_category_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    cat_id = callback.data.split(":")[1]
    cat = QuestionnaireEngine.get_category(cat_id)
    if not cat:
        await callback.answer("Kategoriya topilmadi.", show_alert=True)
        return

    await state.update_data(selected_category_id=cat_id)

    # Build subcategory inline buttons
    rows = []
    subcats = list(cat.subcategories.values())
    for subcat in subcats:
        icon = subcat.icon or "🔹"
        rows.append([
            InlineKeyboardButton(
                text=f"{icon} {subcat.label}",
                callback_data=f"subcat:{cat_id}:{subcat.id}"
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="menu:back_to_start")])

    text = (
        f"{cat.icon} <b>{cat.label.upper()}</b>\n\n"
        f"Iltimos, e’loningizga mos bo‘limni tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


# =========================================================================
# 2. SUBCATEGORY SELECTION -> START QUESTIONNAIRE
# =========================================================================

@router.callback_query(F.data.startswith("subcat:"))
async def handle_subcategory_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    cat_id = parts[1]
    subcat_id = parts[2]

    user = callback.from_user
    if not user:
        return

    # Ensure user exists in DB
    user_db = await UserRepository.get_or_create(
        session=session,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.id in settings.all_admin_ids
    )

    # Create persistent AdvertisingRequest in PostgreSQL
    req = await AdvertisingRequestRepository.create(
        session=session,
        user_id=user_db.id,
        category_id=cat_id,
        subcategory_id=subcat_id
    )

    await state.set_state(QuestionnaireStates.answering_questions)
    await state.update_data(
        request_id=req.id,
        category_id=cat_id,
        subcategory_id=subcat_id,
        answers={},
        media_count=0
    )

    # Send first question
    await ask_next_question(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        user_id=user.id,
        session=session,
        state=state,
        message_to_edit=callback.message
    )
    await callback.answer()


# =========================================================================
# CORE QUESTIONNAIRE RUNNER: Ask Next Question
# =========================================================================

async def ask_next_question(
    bot: Bot,
    chat_id: int,
    user_id: int,
    session: AsyncSession,
    state: FSMContext,
    message_to_edit: Optional[Message] = None,
    current_field_id: Optional[str] = None
) -> None:
    data = await state.get_data()
    req_id = data.get("request_id")
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")

    # Fetch fresh answers from DB to guarantee resilience against restarts
    answers = await AdvertisingRequestRepository.get_answers_dict(session, req_id)
    await state.update_data(answers=answers)

    next_field, idx, total = QuestionnaireEngine.get_next_field(
        category_id=cat_id,
        subcategory_id=subcat_id,
        answers=answers,
        current_field_id=current_field_id
    )

    # If no more fields, show preview!
    if not next_field:
        await show_advertisement_preview(bot, chat_id, req_id, session, state)
        return

    await state.update_data(current_field_id=next_field.id)

    # Check media count if multi_photo
    media_count = 0
    if next_field.field_type in (FieldType.MULTI_PHOTO, FieldType.PHOTO):
        media_items = await AdvertisingRequestRepository.get_media_items(session, req_id)
        media_count = len(media_items)

    kb = QuestionnaireEngine.build_field_keyboard(
        field_def=next_field,
        can_go_back=idx > 1,
        is_optional=not next_field.required,
        include_done_media_btn=media_count > 0,
        media_count=media_count
    )

    req_badge = "🔴 <i>Majburiy</i>" if next_field.required else "⚪️ <i>Ixtiyoriy</i>"
    help_str = f"\n💡 <i>{html.escape(next_field.help_text)}</i>" if next_field.help_text else ""
    placeholder_str = f"\n✍️ <i>Masalan: {html.escape(next_field.placeholder)}</i>" if next_field.placeholder else ""

    text = (
        f"📋 <b>Savol {idx} / {total}</b> ({req_badge})\n\n"
        f"<b>{html.escape(next_field.label)}:</b>\n"
        f"{next_field.prompt}"
        f"{placeholder_str}"
        f"{help_str}"
    )

    try:
        if message_to_edit:
            await message_to_edit.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.debug(f"Could not edit message, sending fresh one: {e}")
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)


# =========================================================================
# 3. ANSWER HANDLER — INLINE CALLBACK (Single Select / Boolean)
# =========================================================================

async def validate_active_request(
    session: AsyncSession,
    state: FSMContext,
    event: Message | CallbackQuery
) -> Optional[AdvertisingRequest]:
    """
    Validates that the active questionnaire request exists in PostgreSQL.
    If stale or missing, clears state and guides the user to start afresh.
    """
    data = await state.get_data()
    req_id = data.get("request_id")
    if not req_id:
        req = None
    else:
        req = await AdvertisingRequestRepository.get_by_id(session, req_id)

    if not req:
        await state.clear()
        warn_text = (
            "⚠️ <b>E’lon so‘rovi topilmadi yoki eskirgan.</b>\n\n"
            "Iltimos, pastdagi toifalardan birini tanlab, e’lon berishni qaytadan boshlang:"
        )
        if isinstance(event, CallbackQuery):
            await event.answer("⚠️ E’lon so‘rovi topilmadi, qaytadan boshlang.", show_alert=True)
            if event.message:
                await event.message.answer(
                    warn_text,
                    parse_mode="HTML",
                    reply_markup=get_categories_keyboard()
                )
        else:
            await event.answer(
                warn_text,
                parse_mode="HTML",
                reply_markup=get_categories_keyboard()
            )
        return None
    return req


@router.callback_query(F.data.startswith("qans:"), QuestionnaireStates.answering_questions)
async def handle_inline_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req = await validate_active_request(session, state, callback)
    if not req:
        return

    parts = callback.data.split(":")
    field_id = parts[1]
    option_id = parts[2]

    data = await state.get_data()
    req_id = data.get("request_id")
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")

    field_def = QuestionnaireEngine.get_field_by_id(cat_id, subcat_id, field_id)
    if not field_def:
        await callback.answer("Maydon topilmadi.", show_alert=True)
        return

    is_valid, parsed_val, err_msg = QuestionnaireEngine.validate_input(field_def, option_id)
    if not is_valid:
        await callback.answer(err_msg or "Noto‘g‘ri qiymat", show_alert=True)
        return

    # Save to persistent PostgreSQL database
    await AdvertisingRequestRepository.save_answer(
        session=session,
        request_id=req_id,
        field_id=field_id,
        value=parsed_val,
        field_label=field_def.label
    )

    # Next question
    await ask_next_question(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        session=session,
        state=state,
        message_to_edit=callback.message,
        current_field_id=field_id
    )
    await callback.answer()


# =========================================================================
# 4. ANSWER HANDLER — TEXT INPUT (Validation & Storage)
# =========================================================================

@router.message(QuestionnaireStates.answering_questions, F.text)
async def handle_text_answer(message: Message, state: FSMContext, session: AsyncSession) -> None:
    req = await validate_active_request(session, state, message)
    if not req:
        return

    data = await state.get_data()
    req_id = data.get("request_id")
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")
    current_field_id = data.get("current_field_id")

    if not current_field_id:
        return

    field_def = QuestionnaireEngine.get_field_by_id(cat_id, subcat_id, current_field_id)
    if not field_def:
        return

    is_valid, parsed_val, err_msg = QuestionnaireEngine.validate_input(field_def, message.text)
    if not is_valid:
        await message.answer(f"⚠️ {err_msg}", parse_mode="HTML")
        return

    # Save answer to database
    await AdvertisingRequestRepository.save_answer(
        session=session,
        request_id=req_id,
        field_id=current_field_id,
        value=parsed_val,
        field_label=field_def.label
    )

    # If user was editing a single field from preview, jump straight back to preview
    if data.get("editing_single_field"):
        await state.update_data(editing_single_field=False)
        await show_advertisement_preview(message.bot, message.chat.id, req_id, session, state)
        return

    # Proceed to next applicable question
    await ask_next_question(
        bot=message.bot,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        session=session,
        state=state,
        current_field_id=current_field_id
    )


# =========================================================================
# 5. ANSWER HANDLER — PHOTO & VIDEO INPUT (Multi-Media Support)
# =========================================================================

@router.message(QuestionnaireStates.answering_questions, F.photo | F.video)
async def handle_media_answer(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    album: Optional[List[Message]] = None
) -> None:
    req = await validate_active_request(session, state, message)
    if not req:
        return

    data = await state.get_data()
    req_id = data.get("request_id")
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")
    current_field_id = data.get("current_field_id")

    field_def = QuestionnaireEngine.get_field_by_id(cat_id, subcat_id, current_field_id) if current_field_id else None

    # Handle incoming album or single photo/video
    messages_to_process = album if album else [message]

    existing_items = await AdvertisingRequestRepository.get_media_items(session, req_id)
    current_count = len(existing_items)
    max_allowed = 10
    remaining_slots = max(0, max_allowed - current_count)

    newly_added = 0
    for msg in messages_to_process:
        if newly_added >= remaining_slots:
            break
        if msg.photo:
            photo = msg.photo[-1]
            await AdvertisingRequestRepository.add_media(
                session=session,
                request_id=req_id,
                file_id=photo.file_id,
                media_type="PHOTO",
                file_unique_id=photo.file_unique_id,
                caption=msg.caption,
                file_size=photo.file_size
            )
            newly_added += 1
        elif msg.video:
            video = msg.video
            await AdvertisingRequestRepository.add_media(
                session=session,
                request_id=req_id,
                file_id=video.file_id,
                media_type="VIDEO",
                file_unique_id=video.file_unique_id,
                caption=msg.caption,
                file_size=video.file_size
            )
            newly_added += 1

    # Fetch updated media count
    items = await AdvertisingRequestRepository.get_media_items(session, req_id)
    count = len(items)
    await state.update_data(media_count=count)

    # Auto-save answer record
    await AdvertisingRequestRepository.save_answer(
        session=session,
        request_id=req_id,
        field_id="media",
        value=f"{count} ta media yuklandi",
        field_label="Rasmlar va video"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Yuklashni yakunlash ({count} ta)", callback_data="qnav:media_done")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="qnav:back"), InlineKeyboardButton(text="❌ Bekor qilish", callback_data="qnav:cancel")]
    ])

    batch_note = f" (ushbu guruhda: <b>{newly_added} ta</b>)" if len(messages_to_process) > 1 else ""
    await message.answer(
        f"📸 <b>Media fayl qabul qilindi{batch_note}!</b>\n"
        f"Jami yuklangan: <b>{count} ta</b> (ruxsat etilgan: {max_allowed} tagacha).\n\n"
        f"Yana rasm yuborishingiz yoki yakunlash uchun quyidagi tugmani bosishingiz mumkin:",
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================================================================
# 6. NAVIGATION: Back, Skip, Cancel, Media Done
# =========================================================================

@router.callback_query(F.data == "qnav:media_done", QuestionnaireStates.answering_questions)
async def handle_media_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req = await validate_active_request(session, state, callback)
    if not req:
        return

    data = await state.get_data()
    req_id = data.get("request_id")
    current_field_id = data.get("current_field_id")

    if data.get("editing_single_field"):
        await state.update_data(editing_single_field=False)
        await show_advertisement_preview(callback.bot, callback.message.chat.id, req_id, session, state)
        await callback.answer()
        return

    await ask_next_question(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        session=session,
        state=state,
        message_to_edit=callback.message,
        current_field_id=current_field_id
    )
    await callback.answer()


@router.callback_query(F.data == "qnav:back", QuestionnaireStates.answering_questions)
async def handle_back_button(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req = await validate_active_request(session, state, callback)
    if not req:
        return

    data = await state.get_data()
    req_id = data.get("request_id")
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")
    current_field_id = data.get("current_field_id")

    answers = await AdvertisingRequestRepository.get_answers_dict(session, req_id)
    prev_field = QuestionnaireEngine.get_previous_field(cat_id, subcat_id, answers, current_field_id)

    if not prev_field:
        # Return to subcategory selection
        await callback.answer("Boshlang‘ich savolga yetib kelindi.", show_alert=False)
        return

    # Delete or keep previous answer and show that question
    await state.update_data(current_field_id=prev_field.id)
    applicable = QuestionnaireEngine.get_applicable_fields(cat_id, subcat_id, answers)
    idx = 1
    for i, f in enumerate(applicable):
        if f.id == prev_field.id:
            idx = i + 1
            break

    kb = QuestionnaireEngine.build_field_keyboard(
        field_def=prev_field,
        can_go_back=idx > 1,
        is_optional=not prev_field.required
    )

    req_badge = "🔴 <i>Majburiy</i>" if prev_field.required else "⚪️ <i>Ixtiyoriy</i>"
    prev_val = answers.get(prev_field.id)
    prev_val_note = f"\n\n📝 <i>Hozirgi qiymat:</i> <b>{html.escape(str(prev_val))}</b>" if prev_val else ""

    text = (
        f"📋 <b>Savol {idx} / {len(applicable)}</b> ({req_badge})\n\n"
        f"<b>{html.escape(prev_field.label)}:</b>\n"
        f"{prev_field.prompt}"
        f"{prev_val_note}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "qnav:skip", QuestionnaireStates.answering_questions)
async def handle_skip_button(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req = await validate_active_request(session, state, callback)
    if not req:
        return

    data = await state.get_data()
    req_id = data.get("request_id")
    current_field_id = data.get("current_field_id")

    # Remove any existing value
    if current_field_id:
        await AdvertisingRequestRepository.delete_answer(session, req_id, current_field_id)

    await ask_next_question(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        session=session,
        state=state,
        message_to_edit=callback.message,
        current_field_id=current_field_id
    )
    await callback.answer("Savol o‘tkazib yuborildi.")


@router.callback_query(F.data == "qnav:cancel")
async def handle_cancel_questionnaire(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    req_id = data.get("request_id")
    if req_id:
        await AdvertisingRequestRepository.update_status(session, req_id, "CANCELLED")

    await state.clear()
    is_admin = callback.from_user.id in settings.all_admin_ids
    await callback.message.edit_text(
        "❌ <b>E’lon berish bekor qilindi.</b>\n\n"
        "Yangi e’lon joylashtirish uchun quyidagi mahsulot turini tanlang:",
        parse_mode="HTML",
        reply_markup=get_start_menu_keyboard(is_admin)
    )
    await callback.answer()


# =========================================================================
# 7. ADVERTISEMENT PREVIEW AND CONFIRMATION (Section 12)
# =========================================================================

async def show_advertisement_preview(
    bot: Bot,
    chat_id: int,
    req_id: int,
    session: AsyncSession,
    state: FSMContext
) -> None:
    data = await state.get_data()
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")

    answers = await AdvertisingRequestRepository.get_answers_dict(session, req_id)
    preview_text = AdvertisementPreviewGenerator.generate_preview(
        category_id=cat_id,
        subcategory_id=subcat_id,
        answers=answers
    )

    # Save generated preview text to DB
    req = await AdvertisingRequestRepository.get_by_id(session, req_id)
    if req:
        req.preview_text = preview_text
        req.status = "AWAITING_USER_CONFIRMATION"
        await session.flush()

    await state.set_state(QuestionnaireStates.preview_confirmation)

    media_items = await AdvertisingRequestRepository.get_media_items(session, req_id)

    # Send media preview if exists
    if media_items:
        try:
            if len(media_items) == 1:
                item = media_items[0]
                if item.media_type == "PHOTO":
                    await bot.send_photo(chat_id=chat_id, photo=item.file_id)
                elif item.media_type == "VIDEO":
                    await bot.send_video(chat_id=chat_id, video=item.file_id)
            elif len(media_items) <= 10:
                media_group = []
                for m in media_items[:10]:
                    if m.media_type == "PHOTO":
                        media_group.append(InputMediaPhoto(media=m.file_id))
                    elif m.media_type == "VIDEO":
                        media_group.append(InputMediaVideo(media=m.file_id))
                if media_group:
                    await bot.send_media_group(chat_id=chat_id, media=media_group)
        except Exception as e:
            logger.warning(f"Preview media group send failed: {e}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data=f"qconfirm:submit:{req_id}")],
        [InlineKeyboardButton(text="✏️ Ma’lumotlarni tahrirlash", callback_data=f"qconfirm:edit:{req_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"qconfirm:cancel:{req_id}")],
    ])

    full_message = (
        "👀 <b>E’LONNING YAKUNIY KO‘RINISHI (PREVIEW):</b>\n\n"
        "<i>Guruhga joylashtiriladigan e’lon ko‘rinishini tekshiring:</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"{preview_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Barcha ma’lumotlar to‘g‘ri bo‘lsa, <b>«Tasdiqlash va yuborish»</b> tugmasini bosing."
    )
    await bot.send_message(chat_id=chat_id, text=full_message, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("qconfirm:edit:"))
async def handle_edit_preview(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")

    answers = await AdvertisingRequestRepository.get_answers_dict(session, req_id)
    applicable = QuestionnaireEngine.get_applicable_fields(cat_id, subcat_id, answers)

    # Show fields as selectable buttons to edit
    rows = []
    for f in applicable:
        current_val = answers.get(f.id, "—")
        snippet = str(current_val)[:20]
        btn_text = f"✏️ {f.label}: {snippet}"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"qeditfield:{req_id}:{f.id}")])

    rows.append([InlineKeyboardButton(text="⬅️ E’longa qaytish", callback_data=f"qedit_return:{req_id}")])

    await callback.message.edit_text(
        "✏️ <b>Qaysi ma’lumotni o‘zgartirmoqchisiz?</b>\n\n"
        "Kerakli bandni tanlang:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("qeditfield:"))
async def handle_select_field_to_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    req_id = int(parts[1])
    field_id = parts[2]

    data = await state.get_data()
    cat_id = data.get("category_id")
    subcat_id = data.get("subcategory_id")

    field_def = QuestionnaireEngine.get_field_by_id(cat_id, subcat_id, field_id)
    if not field_def:
        await callback.answer("Maydon topilmadi.", show_alert=True)
        return

    await state.set_state(QuestionnaireStates.answering_questions)
    await state.update_data(current_field_id=field_id, editing_single_field=True)

    kb = QuestionnaireEngine.build_field_keyboard(
        field_def=field_def,
        can_go_back=False,
        is_optional=not field_def.required
    )

    text = (
        f"✏️ <b>{html.escape(field_def.label)}ni qayta kiritish:</b>\n\n"
        f"{field_def.prompt}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("qedit_return:"))
async def handle_return_from_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[1])
    await show_advertisement_preview(callback.bot, callback.message.chat.id, req_id, session, state)
    await callback.answer()


# =========================================================================
# 8. SUBMIT CONFIRMATION -> NOTIFY ADMIN FOR PRICING (Section 14)
# =========================================================================

@router.callback_query(F.data.startswith("qconfirm:submit:"))
async def handle_confirm_submission(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    req_id = int(callback.data.split(":")[2])

    req = await AdvertisingRequestRepository.update_status(session, req_id, "AWAITING_PRICE")
    await state.clear()

    if not req:
        await callback.answer("So‘rov topilmadi.", show_alert=True)
        return

    user = callback.from_user
    username_str = f"@{user.username}" if user.username else "mavjud emas"

    # 1. Notify Advertiser
    user_confirm_text = (
        "✅ <b>E’loningiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"📋 <b>So‘rov raqami:</b> <code>{req.request_number}</code>\n"
        f"📊 <b>Holati:</b> ⏳ Administrator ko‘rib chiqmoqda\n\n"
        "Administrator e’loningizni ko‘rib chiqib, reklama narxi va to‘lov ma’lumotlarini shaxsiy xabar orqali yuboradi.\n\n"
        "<i>E’loningiz holatini «📋 Mening e’lonlarim» bo‘limida kuzatib borishingiz mumkin.</i>"
    )
    await callback.message.edit_text(user_confirm_text, parse_mode="HTML")

    # 2. Notify Administrators with [💰 Narx belgilash] Keyboard
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Narx belgilash", callback_data=f"adm_price:{req.id}"),
            InlineKeyboardButton(text="👁 E’lonni ko‘rish", callback_data=f"adm_view:{req.id}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Qaytarish", callback_data=f"adm_return:{req.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_reject:{req.id}"),
        ]
    ])

    admin_alert_text = (
        f"📢 <b>YANGI REKLAMA SO‘ROVI (TAYYOR SHAKL)</b>\n\n"
        f"🔢 <b>So‘rov raqami:</b> <code>{req.request_number}</code>\n"
        f"👤 <b>Foydalanuvchi:</b> {html.escape(user.full_name or '')} ({username_str})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"📂 <b>Kategoriya:</b> {req.category_id} / {req.subcategory_id}\n\n"
        f"📝 <b>E’LON MATNI:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{req.preview_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Iltimos, reklama narxini belgilang:"
    )

    media_items = await AdvertisingRequestRepository.get_media_items(session, req.id)

    for admin_id in settings.all_admin_ids:
        try:
            # Send media to admin if available
            if media_items:
                try:
                    if len(media_items) == 1:
                        m = media_items[0]
                        if m.media_type == "PHOTO":
                            await callback.bot.send_photo(chat_id=admin_id, photo=m.file_id)
                        elif m.media_type == "VIDEO":
                            await callback.bot.send_video(chat_id=admin_id, video=m.file_id)
                    elif len(media_items) <= 10:
                        mg = []
                        for m in media_items[:10]:
                            if m.media_type == "PHOTO":
                                mg.append(InputMediaPhoto(media=m.file_id))
                            elif m.media_type == "VIDEO":
                                mg.append(InputMediaVideo(media=m.file_id))
                        if mg:
                            await callback.bot.send_media_group(chat_id=admin_id, media=mg)
                except Exception as media_err:
                    logger.debug(f"Media to admin {admin_id} failed: {media_err}")

            await callback.bot.send_message(
                chat_id=admin_id,
                text=admin_alert_text,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        except Exception as e:
            logger.error(f"Failed to alert admin {admin_id}: {e}")

    await callback.answer("E’lon adminga yuborildi.")


# =========================================================================
# 9. START MENU HANDLERS (Mening e'lonlarim, Qoidalar, Yordam)
# =========================================================================

@router.callback_query(F.data == "menu:back_to_start")
async def handle_back_to_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    is_admin = callback.from_user.id in settings.all_admin_ids
    text = (
        "Assalomu alaykum!\n\n"
        "🛡 <b>Defender Bot</b> — guruhda reklama joylashtirish xizmati.\n\n"
        "Reklama joylashtirish uchun quyidagi toifalardan birini tanlang. "
        "Bot sizdan kerakli ma’lumotlarni so‘rab, tayyor va chiroyli e’lon shakllantiradi:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_start_menu_keyboard(is_admin))
    await callback.answer()


@router.callback_query(F.data == "menu:ad_rules")
async def handle_ad_rules(callback: CallbackQuery) -> None:
    rules_text = (
        "ℹ️ <b>REKLAMA JOYLASHTIRISH TARTIBI:</b>\n\n"
        "1. <b>Mahsulot turini tanlang:</b> O‘zingizga mos bo‘limni tanlang (Ko‘chmas mulk, Mebel, Jalyuzi va h.k.).\n"
        "2. <b>Ma’lumotlarni kiriting:</b> Bot savollariga javob bering, narx, manzil va rasmlarni yuklang.\n"
        "3. <b>E’lonni tasdiqlang:</b> Yakuniy ko‘rinishni tekshiring va adminga yuboring.\n"
        "4. <b>Narx va to‘lov:</b> Administrator narx belgilagach, to‘lov kartasi yuboriladi.\n"
        "5. <b>Chekni yuboring:</b> To‘lov chekini botga yuboring.\n"
        "6. <b>Chop etish:</b> To‘lov tasdiqlangach, e’loningiz guruhga avtomatik joylashtiriladi!\n\n"
        "<i>Barcha e’lonlar moderator nazoratidan o‘tadi.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="menu:back_to_start")]
    ])
    await callback.message.edit_text(rules_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def handle_menu_help(callback: CallbackQuery) -> None:
    admin_contact = f"@{settings.ADMIN_USERNAME.lstrip('@')}" if settings.ADMIN_USERNAME else "administrator"
    help_text = (
        "❓ <b>YORDAM VA QO‘LLAB-QUVVATLASH:</b>\n\n"
        "Botdan foydalanishda savollaringiz yoki qiyinchiliklar tug‘ilsa, administratorga murojaat qilishingiz mumkin:\n\n"
        f"👨‍💼 <b>Administrator:</b> {admin_contact}\n\n"
        "<b>Asosiy buyruqlar:</b>\n"
        "• /start — Botni qayta ishga tushirish va asosiy menyu\n"
        "• /cancel — Joriy amalni bekor qilish\n"
        "• /admin — Administrator boshqaruv paneli"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="menu:back_to_start")]
    ])
    await callback.message.edit_text(help_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "menu:my_requests")
async def handle_my_requests(callback: CallbackQuery, session: AsyncSession) -> None:
    user = callback.from_user
    user_db = await UserRepository.get_by_telegram_id(session, user.id)
    if not user_db:
        await callback.answer("E’lonlar topilmadi.", show_alert=True)
        return

    requests = await AdvertisingRequestRepository.get_user_requests(session, user_db.id, limit=5)
    if not requests:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi e’lon berish", callback_data="menu:back_to_start")]
        ])
        await callback.message.edit_text(
            "📋 <b>Sizda hali faol reklama so‘rovlari mavjud emas.</b>\n\n"
            "Yangi reklama berish uchun quyidagi tugmani bosing:",
            parse_mode="HTML",
            reply_markup=kb
        )
        await callback.answer()
        return

    text_lines = ["📋 <b>SIZNING E’LONLARINGIZ:</b>\n"]
    rows = []
    for r in requests:
        status_map = {
            "COLLECTING_INFORMATION": "Jarayonda",
            "AWAITING_USER_CONFIRMATION": "Tasdiqlash kutilmoqda",
            "AWAITING_PRICE": "Narx belgilanmoqda",
            "AWAITING_PAYMENT": "To‘lov kutilmoqda",
            "RECEIPT_SUBMITTED": "Chek tekshirilmoqda",
            "PAYMENT_APPROVED": "To‘lov tasdiqlandi",
            "PUBLISHED": "Chop etildi",
            "CANCELLED": "Bekor qilingan"
        }
        st_label = status_map.get(r.status, r.status)
        text_lines.append(f"• <b>{r.request_number}</b> | {r.category_id} | <i>{st_label}</i>")
        if r.status == "AWAITING_PAYMENT":
            rows.append([InlineKeyboardButton(text=f"💳 To‘lov qilish ({r.request_number})", callback_data=f"user_pay:{r.id}")])

    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="menu:back_to_start")])

    await callback.message.edit_text(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()
