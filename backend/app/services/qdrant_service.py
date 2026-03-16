from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
import uuid

from app.config import get_settings

settings = get_settings()
client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def init_collections():
    """Initialize Qdrant collections if they don't exist."""
    for collection_name in [settings.qdrant_collection_training, settings.qdrant_collection_corrections]:
        try:
            client.get_collection(collection_name)
            print(f"  Collection '{collection_name}' exists")
        except Exception:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"  Created collection '{collection_name}'")


def insert_training_data(
    description_original: str, description_enhanced: str, hs_code: str,
    country: str, embedding: List[float], enhancement_quality: int = 5
) -> str:
    point_id = str(uuid.uuid4())
    hs_code_8digit = hs_code[:8] if len(hs_code) >= 8 else hs_code
    client.upsert(
        collection_name=settings.qdrant_collection_training,
        points=[PointStruct(
            id=point_id, vector=embedding,
            payload={
                "description_original": description_original,
                "description_enhanced": description_enhanced,
                "hs_code": hs_code, "hs_code_8digit": hs_code_8digit,
                "country": country, "enhancement_quality": enhancement_quality,
                "source": "training"
            }
        )]
    )
    return point_id


def insert_correction(
    description: str, hs_code: str, country: str,
    embedding: List[float], confidence: float
) -> str:
    point_id = str(uuid.uuid4())
    hs_code_8digit = hs_code[:8] if len(hs_code) >= 8 else hs_code
    client.upsert(
        collection_name=settings.qdrant_collection_corrections,
        points=[PointStruct(
            id=point_id, vector=embedding,
            payload={
                "description": description, "hs_code": hs_code,
                "hs_code_8digit": hs_code_8digit, "country": country,
                "confidence": confidence, "source": "user_correction"
            }
        )]
    )
    return point_id


def search_similar(
    embedding: List[float], country: Optional[str] = None,
    limit: int = 10, collection_name: Optional[str] = None
) -> List[Dict]:
    if collection_name is None:
        collection_name = settings.qdrant_collection_training

    query_filter = None
    if country:
        query_filter = Filter(must=[FieldCondition(key="country", match=MatchValue(value=country))])

    try:
        results = client.query_points(
            collection_name=collection_name,
            query=embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]
    except Exception as e:
        print(f"Search failed: {e}")
        return []


def search_both_collections(
    embedding: List[float], country: Optional[str] = None,
    limit_per_collection: int = 10
) -> Dict[str, List[Dict]]:
    corrections = search_similar(embedding, country, limit_per_collection, settings.qdrant_collection_corrections)
    training = search_similar(embedding, country, limit_per_collection, settings.qdrant_collection_training)
    return {"corrections": corrections, "training": training}


def get_collection_stats() -> Dict:
    stats = {}
    for name in [settings.qdrant_collection_training, settings.qdrant_collection_corrections]:
        try:
            info = client.get_collection(name)
            stats[name] = {"vectors_count": info.points_count, "status": str(info.status)}
        except Exception as e:
            stats[name] = {"error": str(e)}
    return stats


def test_connection() -> bool:
    try:
        client.get_collections()
        return True
    except Exception as e:
        print(f"Qdrant connection failed: {e}")
        return False
