from aiogram import Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.bot.keyboards.admin_kb import get_admin_main_menu
from app.bot.handlers.ad_order import start_ad_order_workflow

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    command: CommandObject = None
) -> None:
    user = message.from_user
    if not user:
        return

    is_admin = user.id in settings.all_admin_ids

    # Register or update user
    await UserRepository.get_or_create(
        session=session,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=is_admin
    )

    if message.chat.type == "private":
        # Check if opened via deep link for ad order: /start ad_order
        if command and command.args == "ad_order":
            await start_ad_order_workflow(message, state)
            return

        if is_admin:
            text = (
                f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
                f"🛡 <b>Defender Bot Admin Paneli</b>ga xush kelibsiz.\n"
                f"Siz bot boshqaruvchisiz. Quyidagi menyu orqali botni boshqarishingiz mumkin:"
            )
            await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_menu())
        else:
            text = (
                f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
                f"🤖 Men Telegram guruhlarini reklamalar va spamdan himoya qiluvchi "
                f"hamda rasmiy reklama xizmatlarini qabul qiluvchi <b>Defender Bot</b>man.\n\n"
                f"📢 Guruh yoki platformalarda reklama joylashtirmoqchi bo‘lsangiz, "
                f"quyidagi <b>«📢 Reklama berish»</b> tugmasini bosing:"
            )
            user_reply_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📢 Reklama berish")]],
                resize_keyboard=True
            )
            user_inline_kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="📢 Reklama berish", callback_data="start_ad_order")
                ]]
            )
            await message.answer(text, parse_mode="HTML", reply_markup=user_reply_kb)
            await message.answer("Tanlang:", reply_markup=user_inline_kb)
    else:
        # In groups
        await message.answer(
            "🛡 <b>Defender Bot faol holatda.</b>\n"
            "Guruh reklamalardan avtomatik himoyalangan.",
            parse_mode="HTML"
        )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    user = message.from_user
    is_admin = user and user.id in settings.all_admin_ids

    if is_admin:
        text = (
            "📖 <b>ADMIN BUYRUQLARI RO‘YXATI:</b>\n\n"
            "• /status — Botning hozirgi holati va statistikasi\n"
            "• /stats — Bugungi, haftalik va oylik batafsil statistika\n"
            "• /settings — Guruh va global bot sozlamalari\n"
            "• /users — Faol va qoidabuzar foydalanuvchilar\n"
            "• /blacklist — Qora ro‘yxatni ko‘rish va boshqarish\n"
            "• /whitelist — Oq ro‘yxat (ruxsat etilgan domenlar)\n"
            "• /warnings — Foydalanuvchining ogohlantirishlarini ko‘rish\n"
            "• /clusters — Takroriy reklama va kampaniyalarni AI klasterlash\n"
            "• /mute — Foydalanuvchini yozishdan cheklash (reply qilib)\n"
            "• /unmute — Foydalanuvchidan cheklovni yechish\n"
            "• /ban — Foydalanuvchini guruhdan chetlatish\n"
            "• /unban — Foydalanuvchini bandan chiqarish\n"
            "• /logs — Oxirgi audit hodisalari jurnali\n"
        )
    else:
        text = (
            "📖 <b>BOT HAQIDA MA’LUMOT:</b>\n\n"
            "Ushbu bot guruhlardagi reklama, spam va ruxsat etilmagan havolalarni "
            "avtomatik o‘chiradi va guruh xavfsizligini ta'minlaydi.\n\n"
            "Admin bilan bog‘lanish uchun guruh administratorlariga murojaat qiling."
        )

    await message.answer(text, parse_mode="HTML")
