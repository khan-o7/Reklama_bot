import pytest
from app.services.user_behavior_service import UserBehaviorService
from app.services.active_learning_service import ActiveLearningService


def test_user_behavior_tracking():
    user_id = 999111222

    # Spammer sends identical promo message across 4 different groups
    for g_id in [-1001, -1002, -1003, -1004]:
        metrics = UserBehaviorService.record_activity(
            user_id=user_id,
            chat_id=g_id,
            text="Yangi mahsulot sotiladi, arzon narxda! Telefon: +998901234567",
            url_count=1,
            phone_count=1,
            promo_score=35,
            is_promo=True
        )

    assert metrics["unique_groups"] == 4
    assert metrics["repetition_count"] == 4
    assert metrics["advertiser_probability"] >= 0.70
    assert metrics["is_suspicious_spammer"] is True
    assert metrics["suggested_threshold_discount"] >= 15


def test_active_learning_uncertainty():
    # Clear ad (score 80) -> not uncertain
    uncertain_high, _ = ActiveLearningService.calculate_uncertainty(80, threshold=40)
    assert uncertain_high is False

    # Clear innocent message (score 10) -> not uncertain
    uncertain_low, _ = ActiveLearningService.calculate_uncertainty(10, threshold=40)
    assert uncertain_low is False

    # Ambiguous message (score 35, near threshold 40) -> UNCERTAIN!
    uncertain_mid, score = ActiveLearningService.calculate_uncertainty(35, threshold=40)
    assert uncertain_mid is True
    assert score >= 0.70
