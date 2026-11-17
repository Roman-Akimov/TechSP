from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.internal import builder

_fd = descriptor_pb2.FileDescriptorProto()
_fd.name = "recommendation.proto"
_fd.package = "library.recommendations"
_fd.syntax = "proto3"

def _message(name, fields):
    m = _fd.message_type.add()
    m.name = name
    for fname, number, ftype, label, type_name in fields:
        f = m.field.add()
        f.name, f.number, f.type, f.label = fname, number, ftype, label
        if type_name:
            f.type_name = type_name

_OPT = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
_REP = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
_I64 = descriptor_pb2.FieldDescriptorProto.TYPE_INT64
_STR = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
_DBL = descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE
_I32 = descriptor_pb2.FieldDescriptorProto.TYPE_INT32
_MSG = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE

_message("CandidateBook", [
    ("id",1,_I64,_OPT,None), ("title",2,_STR,_OPT,None),
    ("genre_ids",3,_I64,_REP,None), ("average_rating",4,_DBL,_OPT,None)])
_message("RecommendationRequest", [
    ("preferred_genre_ids",1,_I64,_REP,None),
    ("candidates",2,_MSG,_REP,".library.recommendations.CandidateBook"),
    ("limit",3,_I32,_OPT,None)])
_message("RecommendedBook", [
    ("id",1,_I64,_OPT,None), ("title",2,_STR,_OPT,None),
    ("score",3,_DBL,_OPT,None), ("reason",4,_STR,_OPT,None)])
_message("RecommendationResponse", [
    ("recommendations",1,_MSG,_REP,".library.recommendations.RecommendedBook")])

_s = _fd.service.add()
_s.name = "RecommendationService"
_m = _s.method.add()
_m.name = "GetRecommendations"
_m.input_type = ".library.recommendations.RecommendationRequest"
_m.output_type = ".library.recommendations.RecommendationResponse"

DESCRIPTOR = descriptor_pool.Default().AddSerializedFile(_fd.SerializeToString())
builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, __name__, globals())
