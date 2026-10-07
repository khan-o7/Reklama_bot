import pytest
from app.services.cluster_service import ClusterService


def test_education_cluster_grouping():
    messages = [
        "🔥 Kursga yoziling, ajoyib chegirmalar bor!",
        "🔥 Kursga qabul boshlandi, ro‘yxatdan o‘ting!",
        "🔥 Yangi dasturlash kursi boshlanmoqda, kursga qatnashing!",
        "📚 Kursga ro‘yxatdan o‘ting va darslarni boshlang!",
        "Bugun yangi sotiladi iPhone 15 pro max arzon narxda!",
        "Sotiladi telefon yangi narxi 200$"
    ]

    clusters = ClusterService.cluster_advertisements(messages, similarity_threshold=0.30)
    assert len(clusters) >= 2

    # Find education cluster
    edu_cluster = next((c for c in clusters if "ta'lim" in c.topic.lower() or "kurs" in c.topic.lower()), None)
    assert edu_cluster is not None
    assert edu_cluster.message_count >= 3
    assert edu_cluster.confidence_pct >= 80.0

    # Test real-time matching
    incoming_variant = "🔥 Kursimizga yoziling va bilim oling!"
    match, sim = ClusterService.match_against_active_clusters(incoming_variant, threshold=0.30)
    assert match is not None
    assert "ta'lim" in match.topic.lower() or "kurs" in match.topic.lower()
