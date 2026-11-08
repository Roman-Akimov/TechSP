import grpc
from grpc import StatusCode
from grpc_service import recommendation_pb2 as pb

class RecommendationServiceStub:
    def __init__(self, channel):
        self.GetRecommendations = channel.unary_unary(
            "/library.recommendations.RecommendationService/GetRecommendations",
            request_serializer=pb.RecommendationRequest.SerializeToString,
            response_deserializer=pb.RecommendationResponse.FromString)

class RecommendationServiceServicer:
    def GetRecommendations(self, request, context):
        raise NotImplementedError()

def add_RecommendationServiceServicer_to_server(servicer, server):
    handler = grpc.unary_unary_rpc_method_handler(
        servicer.GetRecommendations,
        request_deserializer=pb.RecommendationRequest.FromString,
        response_serializer=pb.RecommendationResponse.SerializeToString)
    generic = grpc.method_handlers_generic_handler(
        "library.recommendations.RecommendationService",
        {"GetRecommendations": handler})
    server.add_generic_rpc_handlers((generic,))
