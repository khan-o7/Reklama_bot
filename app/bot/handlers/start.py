from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.bot.keyboards.admin_kb import get_admin_main_menu

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession) -> None:
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
                f"🤖 Men Telegram guruhlarini reklamalar, spam va keraksiz havolalardan "
                f"himoya qiluvchi professional <b>Defender Bot</b>man.\n\n"
                f"Meni guruhingizga qo‘shing va <b>Administrator</b> qilib tayinlang!"
            )
            await message.answer(text, parse_mode="HTML")
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
