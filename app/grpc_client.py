import logging
import os
import grpc

from grpc_service import recommendation_pb2 as pb
from grpc_service import recommendation_pb2_grpc as pb_grpc

log = logging.getLogger("library-api")
GRPC_TARGET = os.getenv("GRPC_RECOMMENDATION_TARGET", "localhost:50051")

def get_recommendations(preferred_genre_ids, candidates, limit=10):
    log.info("[API] Отправка запроса в gRPC: %d кандидатов", len(candidates))
    with grpc.insecure_channel(GRPC_TARGET) as channel:
        stub = pb_grpc.RecommendationServiceStub(channel)
        request = pb.RecommendationRequest(
            preferred_genre_ids=preferred_genre_ids,
            limit=limit,
        )
        for item in candidates:
            request.candidates.add(
                id=item["id"],
                title=item["title"],
                genre_ids=item["genre_ids"],
                average_rating=item["average_rating"],
            )
        response = stub.GetRecommendations(request, timeout=5)
    log.info("[API] gRPC вернул %d рекомендаций", len(response.recommendations))
    return [
        {"id": item.id, "title": item.title, "score": item.score, "reason": item.reason}
        for item in response.recommendations
    ]
