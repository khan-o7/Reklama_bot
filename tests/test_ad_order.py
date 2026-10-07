from app.bot.keyboards.warning_kb import get_warning_keyboard
from app.config.settings import settings


def test_warning_keyboard_with_bot():
    kb = get_warning_keyboard(bot_username="antireklamachi_bot")
    assert len(kb.inline_keyboard) >= 1
    # Check that bot referral link is present
    bot_btn = kb.inline_keyboard[0][0]
    assert "botga murojaat" in bot_btn.text.lower()
    assert "https://t.me/antireklamachi_bot?start=ad_order" in bot_btn.url


def test_payment_card_setting():
    assert settings.AD_PAYMENT_CARD == "5614683515901387"
