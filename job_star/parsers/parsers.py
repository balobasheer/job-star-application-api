# from rest_framework.parsers import JSONParser, MultiPartParser
#
# from job_star.encryption import decrypt_data
#
#
# class CustomJSONParser(JSONParser):
#
#     def parse(self, stream, media_type=None, parser_context=None):
#         enc_data = super(CustomJSONParser, self).parse(
#             stream,
#             media_type=None,
#             parser_context=None
#         )
#         data = decrypt_data(enc_data)
#         print(data)
#         return data
#
#
# class CustomMultiPartParser(MultiPartParser):
#
#     def parse(self, stream, media_type=None, parser_context=None):
#         return super(CustomMultiPartParser, self).parse(
#             stream,
#             media_type=None,
#             parser_context=None
#         )