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
from app.bot.handlers.ad_order import start_ad_order_workflow, handle_ad_deep_link, get_user_menu_keyboard

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
        # Check if opened via deep link: /start new_ad, /start ad_<id>, /start ad_order, etc.
        if command and command.args:
            args = command.args.strip()
            if args.startswith("ad_") or args in ("new_ad", "create_ad", "ad_order", "order"):
                await state.clear()
                from app.bot.handlers.questionnaire_handler import (
                    get_categories_keyboard,
                    QuestionnaireStates,
                )
                await state.set_state(QuestionnaireStates.selecting_category)

                # Send persistent reply menu keyboard
                await message.answer(
                    "Assalomu alaykum!\n\n"
                    "🛡 <b>Defender Bot</b> — guruhda reklama joylashtirish xizmati.\n\n"
                    "Bu yerda siz o‘z e’loningizni qulay va sifatli tarzda shakllantirishingiz mumkin.",
                    parse_mode="HTML",
                    reply_markup=get_user_menu_keyboard()
                )

                # Send category selection inline keyboard
                text = (
                    "📋 <b>Yangi reklama yaratish:</b>\n\n"
                    "Reklama joylashtirish uchun mahsulot / xizmat turini tanlang:\n"
                    "Quyidagi toifalardan birini tanlang. Bot sizdan kerakli ma’lumotlarni "
                    "bosqichma-bosqich so‘rab, tayyor va chiroyli e’lon shakllantiradi:"
                )
                await message.answer(text, parse_mode="HTML", reply_markup=get_categories_keyboard())
                return

        welcome_text = (
            "Assalomu alaykum!\n\n"
            "🛡 <b>Defender Bot</b> — guruhlarda reklama xavfsizligini ta’minlash va "
            "rasmiy pullik e’lonlarni qulay hamda sifatli joylashtirish xizmati boti.\n\n"
            "Bu bot orqali siz o‘z mahsulot yoki xizmatlaringiz bo‘yicha e’lonlarni to‘ldirib, "
            "guruh qoidalariga mos tarzda rasmiy joylashtirishingiz mumkin.\n\n"
            "ℹ️ <b>Foydalanish uchun:</b>\n"
            "• Bosh menyuga qaytish yoki botni yangilash uchun <b>/start</b> bosing.\n"
            "• Reklama berish uchun quyidagi <b>«📢 Reklama joylash»</b> tugmasidan foydalaning yoki toifani tanlang."
        )

        from app.bot.handlers.questionnaire_handler import get_start_menu_keyboard

        if is_admin:
            welcome_text += "\n\n🛡 <b>Admin imtiyozi:</b> /admin orqali to‘liq boshqaruv paneliga kirishingiz mumkin."

        # 1. Send intro text with persistent bottom reply keyboard
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_user_menu_keyboard()
        )

        # 2. Send inline category selection (select qismi)
        await message.answer(
            "📋 <b>Reklama joylashtirish uchun mahsulot turini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=get_start_menu_keyboard(is_admin=is_admin)
        )
    else:
        # In groups
        await message.answer(
            "🛡 <b>Defender Bot faol holatda.</b>\n"
            "Guruh reklamalardan avtomatik himoyalangan.",
            parse_mode="HTML"
        )


@router.message(Command("reklama_berish"))
async def handle_cmd_reklama_berish(message: Message, state: FSMContext) -> None:
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


@router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("✅ Amal muvaffaqiyatli bekor qilindi.", reply_markup=get_user_menu_keyboard())
    else:
        await message.answer("ℹ️ Bekor qilinadigan faol jarayon mavjud emas.", reply_markup=get_user_menu_keyboard())


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    user = message.from_user
    is_admin = user and user.id in settings.all_admin_ids

    if is_admin:
        text = (
            "📖 <b>ADMINISTRATOR BUYRUQLARI:</b>\n\n"
            "• /admin — Administrator asosiy boshqaruv paneli\n"
            "• /requests — Barcha reklama so‘rovlari va to‘lovlarni ko‘rish\n"
            "• /stats — Reklama tushumlari va guruh moderatsiya statistikasi\n"
            "• /status — Bot va tizim holati (DB, Redis, xotira)\n"
            "• /settings — Guruh va reklama sozlamalari\n"
            "• /whitelist — Ruxsat etilgan domenlar oq ro‘yxati\n"
            "• /blacklist — Taqiqlangan so‘zlar va domenlar qora ro‘yxati\n"
            "• /cancel — Faol jarayonni bekor qilish\n"
            "• /logs — Oxirgi audit hodisalari\n"
            "• /clusters — AI reklama klasterlari\n"
        )
    else:
        text = (
            "📖 <b>REKLAMA JOYLASHTIRISH VA BOT YO‘RIQNOMASI:</b>\n\n"
            "1️⃣ <b>Reklama joylash:</b> «📢 Reklama joylash» tugmasini bosing va mahsulot turini tanlang.\n"
            "2️⃣ <b>Ma’lumotlarni kiritish:</b> Bot savollariga javob berib, tayyor e’lon shakllantiring.\n"
            "3️⃣ <b>Narx va to‘lov:</b> Administrator narx belgilagach, to‘lov chekini ushbu botga yuborasiz.\n"
            "4️⃣ <b>Tasdiqlash va e’lon:</b> Administrator chekni tasdiqlagach, reklamangiz darhol guruhda e’lon qilinadi.\n\n"
            "ℹ️ <b>Asosiy buyruqlar:</b>\n"
            "• /start — Boshlash va asosiy menyu\n"
            "• /reklama_berish — Yangi reklama berish\n"
            "• /admin — Adminga murojaat (@ads_bot_service)\n"
            "• /myorders — Mening reklama so‘rovlarim\n"
            "• /cancel — Faol amalni bekor qilish\n"
            "• /help — Yordam ma’lumotlari"
        )

    await message.answer(text, parse_mode="HTML", reply_markup=get_user_menu_keyboard())
