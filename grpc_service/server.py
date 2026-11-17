from concurrent import futures
import logging
import grpc

from grpc_service import recommendation_pb2 as pb
from grpc_service import recommendation_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [gRPC] %(message)s")
log = logging.getLogger("recommendation-service")

class RecommendationService(pb_grpc.RecommendationServiceServicer):
    def GetRecommendations(self, request, context):
        preferred = set(request.preferred_genre_ids)
        log.info("Получен запрос: предпочтительные жанры=%s, кандидатов=%d",
                 sorted(preferred), len(request.candidates))
        ranked = []
        for book in request.candidates:
            overlap = len(preferred.intersection(book.genre_ids))
            # Совпадение жанров важнее рейтинга; рейтинг помогает ранжировать книги.
            score = overlap * 10.0 + book.average_rating
            if preferred and overlap:
                reason = f"Совпадает жанров: {overlap}; рейтинг: {book.average_rating:.1f}/5"
            elif preferred:
                reason = f"Популярная книга: рейтинг {book.average_rating:.1f}/5"
            else:
                reason = f"Высокий рейтинг: {book.average_rating:.1f}/5"
            ranked.append((score, book.id, book.title, reason))
        ranked.sort(key=lambda item: (-item[0], item[2].lower()))
        limit = request.limit if request.limit > 0 else 10
        response = pb.RecommendationResponse()
        for score, book_id, title, reason in ranked[:limit]:
            response.recommendations.add(id=book_id, title=title,
                                         score=round(score, 2), reason=reason)
        log.info("Сформированы рекомендации: %s",
                 [item.id for item in response.recommendations])
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_RecommendationServiceServicer_to_server(RecommendationService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    log.info("gRPC-сервис рекомендаций запущен на 0.0.0.0:50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
