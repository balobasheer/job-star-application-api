import json

from django.http import QueryDict
from django.utils.deprecation import MiddlewareMixin

from job_star.encryption import encrypt_data, decrypt_data


class EncryptionMiddleware(MiddlewareMixin):

    # def process_request(self, request):
    #     request_body = json.loads(request.body)
    #     decrypted_body = (decrypt_data(request_body['data']))
    #     data = QueryDict('', mutable=True)
    #     # print(data)
    #     data.update(**decrypted_body)
    #     # print(data)
    #     if request.method == 'GET':
    #         request.GET = data
    #     elif request.method == 'POST':
    #         request.POST = data

    def process_response(self, request, response):
        # if str(response.status_code).startswith('2'):
        #     response.data = encrypt_data(response.data)
        #     response._is_rendered = False
        #     response.render()
        return response
