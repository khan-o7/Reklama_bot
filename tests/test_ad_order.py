from app.bot.keyboards.warning_kb import get_warning_keyboard
from app.bot.handlers.ad_order import get_user_menu_keyboard
from app.bot.handlers.questionnaire_handler import get_categories_keyboard
from app.config.settings import settings


def test_warning_keyboard_with_bot():
    kb = get_warning_keyboard(bot_username="antireklamachi_bot")
    assert len(kb.inline_keyboard) >= 1
    # Check that bot referral link is present
    bot_btn = kb.inline_keyboard[0][0]
    assert "reklama joylash" in bot_btn.text.lower()
    assert "https://t.me/antireklamachi_bot?start=ad_order" in bot_btn.url


def test_user_menu_keyboard():
    kb = get_user_menu_keyboard()
    button_texts = [btn.text for row in kb.keyboard for btn in row]
    assert "📢 Reklama joylash" in button_texts
    assert "📢 Reklama yuborish" not in button_texts


def test_categories_keyboard():
    kb = get_categories_keyboard()
    assert len(kb.inline_keyboard) == 4
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert callbacks == ["cat:real_estate", "cat:furniture", "cat:curtains_blinds", "cat:electronics_other"]


def test_admin_username_setting():
    assert bool(settings.ADMIN_USERNAME)


def test_payment_card_setting():
    assert bool(settings.AD_PAYMENT_CARD)
