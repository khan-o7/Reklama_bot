from datetime import datetime
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config.settings import settings
from app.utils.logger import logger

router = Router(name="ad_order_router")


class AdOrderStates(StatesGroup):
    waiting_for_ad_content = State()
    waiting_for_payment_receipt = State()


async def start_ad_order_workflow(message: Message, state: FSMContext) -> None:
    """Entry point for initiating the advertisement ordering flow."""
    await state.set_state(AdOrderStates.waiting_for_ad_content)
    text = (
        "📢 <b>Reklama joylashtirish xizmati</b>\n\n"
        "Guruh va platformalarda reklama bermoqchi bo‘lsangiz, iltimos, reklama ma’lumotlarini yuboring:\n"
        "• Reklama matni (tavsif, narx, telefon va h.k.)\n"
        "• Rasm yoki video (mavjud bo‘lsa)\n"
        "• Kanal/guruh yoki sayt havolalari\n\n"
        "Barcha ma’lumotlarni <b>bitta xabarda</b> yuboring:"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad_order")]
        ]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cancel_kb)


@router.message(Command("reklama"))
@router.message(F.text == "📢 Reklama berish")
async def cmd_reklama(message: Message, state: FSMContext) -> None:
    """Triggered by command or menu button."""
    if message.chat.type != "private":
        return
    await start_ad_order_workflow(message, state)


@router.callback_query(F.data == "start_ad_order")
async def callback_start_ad_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Triggered by inline button."""
    await callback.answer()
    if callback.message:
        await start_ad_order_workflow(callback.message, state)


@router.callback_query(F.data == "cancel_ad_order")
async def cancel_ad_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancels the active ad ordering flow."""
    await state.clear()
    await callback.answer("Bekor qilindi")
    if callback.message:
        await callback.message.edit_text("❌ Reklama berish jarayoni bekor qilindi.")


@router.message(AdOrderStates.waiting_for_ad_content)
async def process_ad_content(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Receives ad content (text, photo, video, etc.), forwards it to admins,
    and asks the advertiser for payment card transfer + screenshot.
    """
    user = message.from_user
    if not user:
        return

    username_str = f"@{user.username}" if user.username else "mavjud emas"
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    admin_text = (
        f"📢 <b>YANGI REKLAMA BUYURTMASI KELDI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.full_name} ({username_str})\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"📅 <b>Vaqt:</b> {now_str}\n\n"
        f"Quyida yuborilgan reklama ma’lumotlari:"
    )

    # 1. Forward/Copy ad content to all admins
    for admin_id in settings.all_admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            await bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        except Exception as e:
            logger.error(f"Adminga reklama ma'lumotlarini yetkazishda xatolik ({admin_id}): {e}")

    # 2. Transition state to wait for payment receipt
    await state.set_state(AdOrderStates.waiting_for_payment_receipt)

    # 3. Inform user with payment instructions
    card_number = settings.AD_PAYMENT_CARD
    response_to_user = (
        f"To'lovni ushbu <code>{card_number}</code> kartaga tashlang hamda skrinshot yuboring "
        f"admin tomonidan tasdiqlangach reklama malumotlari guruhda, olxda avtomatik qo'yib boriladi."
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_ad_order")]
        ]
    )
    await message.answer(response_to_user, parse_mode="HTML", reply_markup=cancel_kb)


@router.message(AdOrderStates.waiting_for_payment_receipt, F.photo | F.document)
async def process_payment_receipt(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Receives payment screenshot, sends it to admins with approve/reject buttons,
    and acknowledges receipt to the user.
    """
    user = message.from_user
    if not user:
        return

    username_str = f"@{user.username}" if user.username else "mavjud emas"
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    admin_receipt_text = (
        f"💳 <b>TO‘LOV SKRINSHOTI (CHEK) KELDI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.full_name} ({username_str})\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💳 <b>Karta:</b> <code>{settings.AD_PAYMENT_CARD}</code>\n"
        f"📅 <b>Vaqt:</b> {now_str}\n\n"
        f"Quyida to‘lov cheki:"
    )

    admin_actions_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ To‘lovni tasdiqlash", callback_data=f"ad_approve:{user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ad_reject:{user.id}")
            ]
        ]
    )

    for admin_id in settings.all_admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_receipt_text, parse_mode="HTML")
            await bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=admin_actions_kb
            )
        except Exception as e:
            logger.error(f"Adminga to'lov chekini yuborishda xatolik ({admin_id}): {e}")

    await state.clear()

    await message.answer(
        "✅ <b>To‘lov skrinshotingiz qabul qilindi va adminga yuborildi!</b>\n\n"
        "Admin tomonidan tasdiqlangach reklama malumotlari guruhda, olxda avtomatik qo'yib boriladi.",
        parse_mode="HTML"
    )


@router.message(AdOrderStates.waiting_for_payment_receipt)
async def prompt_for_screenshot_photo(message: Message) -> None:
    """Reminds the user to send an image/screenshot when text is received."""
    card_number = settings.AD_PAYMENT_CARD
    await message.answer(
        f"📸 Iltimos, to‘lov chekining <b>skrinshotini (rasmini)</b> yuboring.\n\n"
        f"To'lovni ushbu <code>{card_number}</code> kartaga tashlang hamda skrinshot yuboring "
        f"admin tomonidan tasdiqlangach reklama malumotlari guruhda, olxda avtomatik qo'yib boriladi.",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ad_approve:"))
async def handle_ad_approve(callback: CallbackQuery, bot: Bot) -> None:
    """Admin approves payment and advertisement."""
    user_id = int(callback.data.split(":")[1])
    await callback.answer("✅ To‘lov tasdiqlandi!")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if callback.message:
        await callback.message.reply(
            f"✅ <b>To‘lov va reklama tasdiqlandi!</b> (Mijoz ID: <code>{user_id}</code>)",
            parse_mode="HTML"
        )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>XUSHXABAR!</b>\n\n"
                "Sizning to‘lovingiz va reklama ma’lumotlaringiz admin tomonidan <b>tasdiqlandi!</b>\n"
                "Reklama ma’lumotlari guruhda, olxda avtomatik qo‘yib boriladi. Rahmat!"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga tasdiq xabarini jo'natishda xatolik ({user_id}): {e}")


@router.callback_query(F.data.startswith("ad_reject:"))
async def handle_ad_reject(callback: CallbackQuery, bot: Bot) -> None:
    """Admin rejects payment or advertisement."""
    user_id = int(callback.data.split(":")[1])
    await callback.answer("❌ Rad etildi")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if callback.message:
        await callback.message.reply(
            f"❌ <b>Reklama/to‘lov rad etildi.</b> (Mijoz ID: <code>{user_id}</code>)",
            parse_mode="HTML"
        )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>Xabarnoma:</b>\n\n"
                "Siz yuborgan reklama yoki to‘lov admin tomonidan rad etildi.\n"
                "Qo‘shimcha ma’lumot uchun administratorga murojaat qilishingiz mumkin."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga rad etish xabarini jo'natishda xatolik ({user_id}): {e}")
