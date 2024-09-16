from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response

from job_star.encryption import decrypt_data


class GenericDecryptionMixin:

    def post(self, request, *args, **kwargs):
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except:
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )

        return super(GenericDecryptionMixin, self).post(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except:
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )

        return super(GenericDecryptionMixin, self).put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except:
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )

        return super(GenericDecryptionMixin, self).patch(request, *args, **kwargs)


class CustomDecryptionMixin:

    def post(self, request, *args, **kwargs):
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except KeyError:
            # request_data = request.data
            raise KeyError
        except Exception as e:
            # request_data = request.data
            raise e
