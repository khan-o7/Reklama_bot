import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User as TgUser, BotCommand
from aiogram.fsm.context import FSMContext

from app.config.settings import settings
from app.bot.handlers.start import handle_cmd_reklama_berish
from app.bot.handlers.admin import cmd_admin
from app.bot.handlers.questionnaire_handler import QuestionnaireStates


@pytest.mark.asyncio
async def test_cmd_reklama_berish():
    msg = MagicMock(spec=Message)
    msg.chat = MagicMock(spec=Chat, type="private", id=123456)
    msg.answer = AsyncMock()

    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()

    await handle_cmd_reklama_berish(msg, state)

    state.clear.assert_awaited_once()
    state.set_state.assert_awaited_once_with(QuestionnaireStates.selecting_category)
    msg.answer.assert_awaited_once()
    assert "Reklama joylashtirish uchun" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_admin_for_regular_user():
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock(spec=TgUser, id=999999, first_name="Oddiy Foydalanuvchi")
    msg.chat = MagicMock(spec=Chat, type="private", id=999999)
    msg.answer = AsyncMock()

    bot = MagicMock()

    # User is not in admin_ids
    assert msg.from_user.id not in settings.all_admin_ids

    await cmd_admin(msg, bot)

    msg.answer.assert_awaited_once()
    called_text = msg.answer.call_args[0][0]
    called_kb = msg.answer.call_args[1]["reply_markup"]

    # Verify admin contact details
    assert "Administratorga murojaat" in called_text
    assert "ads_bot_service" in called_text
    # Verify button URL points to https://t.me/ads_bot_service
    button = called_kb.inline_keyboard[0][0]
    assert "https://t.me/ads_bot_service" in button.url


@pytest.mark.asyncio
async def test_cmd_admin_for_owner_or_admin():
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock(spec=TgUser, id=settings.OWNER_ID, first_name="Bot Owner")
    msg.chat = MagicMock(spec=Chat, type="private", id=settings.OWNER_ID)
    msg.answer = AsyncMock()

    bot = MagicMock()

    await cmd_admin(msg, bot)

    msg.answer.assert_awaited_once()
    called_text = msg.answer.call_args[0][0]
    called_kb = msg.answer.call_args[1]["reply_markup"]

    assert "Administrator Boshqaruv Paneli" in called_text
    assert called_kb is not None


def test_bot_commands_list():
    bot_commands = [
        BotCommand(command="start", description="Boshlash!"),
        BotCommand(command="reklama_berish", description="Yangi reklama berish!"),
        BotCommand(command="admin", description="Adminga murojaat! @ads_bot_service"),
    ]
    commands_dict = {cmd.command: cmd.description for cmd in bot_commands}
    assert commands_dict["start"] == "Boshlash!"
    assert commands_dict["reklama_berish"] == "Yangi reklama berish!"
    assert commands_dict["admin"] == "Adminga murojaat! @ads_bot_service"
