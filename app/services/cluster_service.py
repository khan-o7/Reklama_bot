import re
import math
from typing import List, Dict, Any, Tuple, Set, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.text_utils import normalize_text, cyrillic_to_latin
from app.utils.logger import logger


@dataclass
class AdCluster:
    cluster_id: int
    topic: str
    confidence_pct: float
    sample_texts: List[str] = field(default_factory=list)
    message_count: int = 0
    keywords: List[str] = field(default_factory=list)
    centroid_vector: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ClusterService:
    """
    Intelligent Ad Clustering and Semantic Pattern Recognition Engine.
    
    Features:
    - Semantic Topic Identification & Dynamic Thematic Clustering
    - Lexical Vector Cosine Similarity
    - Automatic Topic / Campaign Labelling (Ta'lim, Savdo, Ish, Kripto, Kanallar, etc.)
    - Cluster Confidence % (e.g., 87% advertisement)
    - Real-time matching against recurring ad campaign clusters
    """

    TOPIC_SIGNATURES: Dict[str, Set[str]] = {
        "Ta'lim va Kurslar (Education)": {
            "kurs", "kursi", "kurslar", "dars", "darslar", "talim", "ta'lim", "oqish", "o'qish",
            "repetitor", "ielts", "cefr", "ingliz", "dasturlash", "akademik", "grant", "sertifikat",
            "уроки", "курс", "курсы", "обучение", "английский", "education", "course", "courses",
            "learn", "study", "training"
        },
        "Savdo va Mahsulotlar (E-commerce)": {
            "sotiladi", "sotamiz", "narx", "narxi", "som", "so'm", "chegirma", "aksiya", "dostavka",
            "mahsulot", "kiyim", "oyoq", "telefon", "mashina", "uy", "kvartira", "skidka", "iphone",
            "продажа", "продаю", "товар", "цена", "скидка", "распродажа", "sale", "shop", "store",
            "discount", "product", "buy"
        },
        "Ish va Daromad (Jobs & Income)": {
            "ish", "ishga", "vakansiya", "oylik", "daromad", "maosh", "kadr", "xodim", "ishchi",
            "pul ishlash", "onlayn ish", "daromad qilish", "rabota", "vakansiya", "zarabotok",
            "работа", "вакансия", "доход", "зарплата", "job", "vacancy", "income", "hiring"
        },
        "Moliya va Kripto (Finance & Crypto)": {
            "kripto", "bitcoin", "usdt", "dollar", "valyuta", "investitsiya", "daromad", "foiz",
            "treyding", "signal", "depozit", "kredit", "kriptovalyuta", "крипта", "инвестиции",
            "трейдинг", "доход", "crypto", "trading", "finance", "investment", "forex"
        },
        "Kanal va Obuna (Channels & Growth)": {
            "obuna", "kanal", "kanalimizga", "qo'shiling", "link", "havola", "bepul", "podpiska",
            "подписывайтесь", "канал", "ссылка", "join", "channel", "subscribe", "link"
        },
        "Shubhali va Qimor (Scam & Gambling)": {
            "1xbet", "melbet", "linebet", "aviator", "kazino", "stavka", "yutuq", "bonus", "tez pul",
            "казино", "ставки", "выигрыш", "бонус", "casino", "bet", "win", "scam"
        }
    }

    _active_clusters: List[AdCluster] = []

    @classmethod
    def get_primary_topic(cls, text: str) -> str:
        """Determines the primary category for a single text."""
        clean = cyrillic_to_latin(normalize_text(text)).lower()
        topic_scores: Dict[str, int] = defaultdict(int)

        for topic, kws in cls.TOPIC_SIGNATURES.items():
            for kw in kws:
                if re.search(rf'\b{re.escape(kw)}', clean):
                    topic_scores[topic] += 1

        if not topic_scores:
            return "Umumiy Reklama (General Advertisement)"

        return max(topic_scores.items(), key=lambda item: item[1])[0]

    @classmethod
    def extract_feature_vector(cls, text: str) -> Dict[str, float]:
        """Extracts normalized lexical token vector with 4-char roots and topic signal."""
        clean = cyrillic_to_latin(normalize_text(text)).lower()
        vec: Dict[str, float] = {}

        # 1. Semantic Topic Feature
        topic = cls.get_primary_topic(text)
        if topic != "Umumiy Reklama (General Advertisement)":
            vec[f"topic_{topic}"] = 2.0

        # 2. 4-character roots for suffix-invariant similarity
        words = re.findall(r'\b[a-z0-9\']{3,}\b', clean)
        for w in words:
            root = w[:4]
            vec[f"root_{root}"] = vec.get(f"root_{root}", 0.0) + 1.0

        norm = math.sqrt(sum(v ** 2 for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    @classmethod
    def cosine_similarity(cls, vec1: Dict[str, float], vec2: Dict[str, float] = None) -> float:
        """Calculates cosine similarity between two normalized sparse vectors."""
        if not vec1 or not vec2:
            return 0.0
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0
        return sum(vec1[k] * vec2[k] for k in common)

    @classmethod
    def cluster_advertisements(
        cls,
        texts: List[str],
        similarity_threshold: float = 0.15
    ) -> List[AdCluster]:
        """
        Clusters advertisement texts by semantic topic and campaign templates.
        """
        if not texts:
            return []

        # 1. Group documents by primary topic
        topic_buckets: Dict[str, List[int]] = defaultdict(list)
        for idx, text in enumerate(texts):
            topic = cls.get_primary_topic(text)
            topic_buckets[topic].append(idx)

        vectors = [cls.extract_feature_vector(t) for t in texts]
        result_clusters: List[AdCluster] = []
        cluster_counter = 1

        # 2. For each topic bucket, build cohesive clusters
        for topic, indices in topic_buckets.items():
            cluster_texts = [texts[idx] for idx in indices]

            # Compute centroid vector for the cluster
            centroid: Dict[str, float] = defaultdict(float)
            for idx in indices:
                for k, v in vectors[idx].items():
                    centroid[k] += v / len(indices)

            top_keywords = [
                k.replace("root_", "")
                for k, _ in sorted(centroid.items(), key=lambda item: item[1], reverse=True)[:5]
            ]

            # Dynamic confidence score (e.g. 87% advertisement)
            base_conf = 82.0 if topic != "Umumiy Reklama (General Advertisement)" else 75.0
            confidence = min(98.0, base_conf + (len(indices) * 2.0))

            ad_cluster = AdCluster(
                cluster_id=cluster_counter,
                topic=topic,
                confidence_pct=round(confidence, 1),
                sample_texts=cluster_texts[:3],
                message_count=len(indices),
                keywords=top_keywords,
                centroid_vector=dict(centroid)
            )
            result_clusters.append(ad_cluster)
            cluster_counter += 1

        result_clusters.sort(key=lambda c: c.message_count, reverse=True)
        cls._active_clusters = result_clusters
        return result_clusters

    @classmethod
    def match_against_active_clusters(cls, text: str, threshold: float = 0.15) -> Optional[Tuple[AdCluster, float]]:
        """
        Real-time matching against active ad campaign clusters.
        """
        if not cls._active_clusters or not text:
            return None

        topic = cls.get_primary_topic(text)
        vec = cls.extract_feature_vector(text)
        best_match: Optional[AdCluster] = None
        best_sim = 0.0

        for cluster in cls._active_clusters:
            if cluster.topic == topic:
                sim = cls.cosine_similarity(vec, cluster.centroid_vector)
                if sim > best_sim:
                    best_sim = sim
                    best_match = cluster

        if best_match and best_sim >= threshold:
            return best_match, round(best_sim, 2)

        return None
