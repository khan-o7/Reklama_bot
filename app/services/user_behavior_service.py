import time
from typing import Dict, List, Any, Tuple
from collections import deque
from dataclasses import dataclass, field

from app.utils.text_utils import normalize_text, cyrillic_to_latin
from app.utils.logger import logger


@dataclass
class UserActivityEvent:
    timestamp: float
    chat_id: int
    text_hash: str
    url_count: int
    phone_count: int
    promo_score: int
    is_promo: bool


@dataclass
class UserBehaviorProfile:
    user_id: int
    events: deque = field(default_factory=lambda: deque(maxlen=50))

    def clean_old_events(self, window_seconds: float = 600.0) -> None:
        """Removes events older than window_seconds (default 10 minutes)."""
        now = time.time()
        while self.events and (now - self.events[0].timestamp) > window_seconds:
            self.events.popleft()

    def calculate_metrics(self, window_seconds: float = 600.0) -> Dict[str, Any]:
        """Calculates multi-group activity, repetition, velocity, and advertiser probability."""
        self.clean_old_events(window_seconds)
        if not self.events:
            return {
                "message_count": 0,
                "unique_groups": 0,
                "repetition_count": 0,
                "total_urls": 0,
                "total_phones": 0,
                "promo_ratio": 0.0,
                "advertiser_probability": 0.0,
                "is_suspicious_spammer": False,
                "suggested_threshold_discount": 0
            }

        total_msgs = len(self.events)
        unique_groups = len(set(e.chat_id for e in self.events))
        
        # Message repetition check (identical / near-identical text hashes)
        text_counts = {}
        for e in self.events:
            text_counts[e.text_hash] = text_counts.get(e.text_hash, 0) + 1
        max_repetition = max(text_counts.values()) if text_counts else 0

        total_urls = sum(e.url_count for e in self.events)
        total_phones = sum(e.phone_count for e in self.events)
        promo_msgs = sum(1 for e in self.events if e.is_promo or e.promo_score >= 20)
        promo_ratio = promo_msgs / total_msgs if total_msgs > 0 else 0.0

        # Calculate Advertiser Probability Score (0.0 to 1.0)
        prob_score = 0.0

        # Signal 1: Cross-group broadcasting (spammer joining multiple groups to blast)
        if unique_groups >= 3:
            prob_score += min(0.35, unique_groups * 0.08)

        # Signal 2: Repetitive message broadcasting
        if max_repetition >= 3:
            prob_score += min(0.30, max_repetition * 0.06)

        # Signal 3: URL & Phone density
        if total_urls >= 2:
            prob_score += min(0.20, total_urls * 0.05)
        if total_phones >= 1:
            prob_score += min(0.15, total_phones * 0.08)

        # Signal 4: Promotional content ratio
        if promo_ratio >= 0.5:
            prob_score += 0.25

        advertiser_probability = min(0.99, round(prob_score, 2))
        is_suspicious = advertiser_probability >= 0.70

        # Dynamic threshold discount: lowers threshold for high-probability commercial spammers
        threshold_discount = int(advertiser_probability * 25)

        return {
            "message_count": total_msgs,
            "unique_groups": unique_groups,
            "repetition_count": max_repetition,
            "total_urls": total_urls,
            "total_phones": total_phones,
            "promo_ratio": round(promo_ratio, 2),
            "advertiser_probability": advertiser_probability,
            "is_suspicious_spammer": is_suspicious,
            "suggested_threshold_discount": threshold_discount
        }


class UserBehaviorService:
    """
    Tracks and analyzes individual user messaging behavior across time and groups.
    Detects aggressive promotional blast campaigns and computes advertiser probability.
    """
    _profiles: Dict[int, UserBehaviorProfile] = {}

    @classmethod
    def record_activity(
        cls,
        user_id: int,
        chat_id: int,
        text: str,
        url_count: int,
        phone_count: int,
        promo_score: int,
        is_promo: bool
    ) -> Dict[str, Any]:
        """Records an outgoing message and returns the updated behavioral profile metrics."""
        if user_id not in cls._profiles:
            cls._profiles[user_id] = UserBehaviorProfile(user_id=user_id)

        # Short normalized fingerprint hash
        clean = cyrillic_to_latin(normalize_text(text)).lower()[:100]
        text_hash = str(hash(clean))

        event = UserActivityEvent(
            timestamp=time.time(),
            chat_id=chat_id,
            text_hash=text_hash,
            url_count=url_count,
            phone_count=phone_count,
            promo_score=promo_score,
            is_promo=is_promo
        )
        profile = cls._profiles[user_id]
        profile.events.append(event)
        return profile.calculate_metrics()

    @classmethod
    def get_user_metrics(cls, user_id: int) -> Dict[str, Any]:
        """Fetches current behavioral metrics for a user."""
        if user_id not in cls._profiles:
            return {
                "message_count": 0,
                "unique_groups": 0,
                "repetition_count": 0,
                "total_urls": 0,
                "total_phones": 0,
                "promo_ratio": 0.0,
                "advertiser_probability": 0.0,
                "is_suspicious_spammer": False,
                "suggested_threshold_discount": 0
            }
        return cls._profiles[user_id].calculate_metrics()
