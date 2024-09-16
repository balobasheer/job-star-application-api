import hashlib

from decouple import config
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.permissions import BasePermission


class IsAdminAuthenticated(BasePermission):

    def has_permission(self, request, view):
        try:
            API_KEY = request.META['HTTP_API_KEY']
            request_ts = request.META['HTTP_REQUEST_TS']
            hash_key = request.META['HTTP_HASH_KEY']
        except KeyError as key:
            raise NotAuthenticated(
                f'Authentication credentials not provided, {key}'
            )
        local_api_key = config('BK_API_KEY')
        local_secret_key = config('BK_SECRET_KEY')
        local_api_key_for_website = config('API_KEY_FRONTEND')
        local_secret_key_for_website = config('SECRET_KEY_FRONTEND')
        try:
            if API_KEY == local_api_key:
                de_hash = local_api_key + local_secret_key + request_ts
            elif API_KEY == local_api_key_for_website:
                de_hash = local_api_key_for_website + local_secret_key_for_website + request_ts
            else:
                de_hash = None
            hash = hashlib.sha256(de_hash.encode('utf8')).hexdigest()

        except:
            raise AuthenticationFailed()

        if hash_key != hash:
            raise AuthenticationFailed()

        return True


class IsAdminOrWebsiteFrontendAuthenticated(BasePermission):

    def has_permission(self, request, view):
        try:
            API_KEY = request.META['HTTP_API_KEY']
            request_ts = request.META['HTTP_REQUEST_TS']
            hash_key = request.META['HTTP_HASH_KEY']
        except KeyError as key:
            raise NotAuthenticated(
                f'Authentication credentials not provided, {key}'
            )
        local_api_key = config('API_KEY_FOR_WEBSITE_FRONTEND')
        local_secret_key = config('SECRET_KEY_FOR_WEBSITE_FRONTEND')
        local_api_key_for_admin = config('BK_API_KEY')
        local_secret_key_for_admin = config('BK_SECRET_KEY')
        local_api_key_for_admin_frontend = config('API_KEY_FRONTEND')
        local_secret_key_for_admin_frontend = config('SECRET_KEY_FRONTEND')
        try:
            if API_KEY == local_api_key:
                de_hash = local_api_key + local_secret_key + request_ts
            elif API_KEY == local_api_key_for_admin:
                de_hash = local_api_key_for_admin + local_secret_key_for_admin + request_ts
            elif API_KEY == local_api_key_for_admin_frontend:
                de_hash = local_api_key_for_admin_frontend + local_secret_key_for_admin_frontend + request_ts
            else:
                de_hash = None
            hash = hashlib.sha256(de_hash.encode('utf8')).hexdigest()

        except:
            raise AuthenticationFailed()

        if hash_key != hash:
            raise AuthenticationFailed()

        return True


class IsAdminOrAssessmentFrontendAuthenticated(BasePermission):

    def has_permission(self, request, view):
        try:
            API_KEY = request.META['HTTP_API_KEY']
            request_ts = request.META['HTTP_REQUEST_TS']
            hash_key = request.META['HTTP_HASH_KEY']
        except KeyError as key:
            raise NotAuthenticated(
                f'Authentication credentials not provided, {key}'
            )
        local_api_key = config('BK_API_KEY')
        local_secret_key = config('BK_SECRET_KEY')
        local_api_key_for_assessment = config('API_KEY_FOR_ASSESS_FRONTEND')
        local_secret_key_for_assessment = config('SECRET_KEY_FOR_ASSESS_FRONTEND')
        try:
            if API_KEY == local_api_key:
                de_hash = local_api_key + local_secret_key + request_ts
            elif API_KEY == local_api_key_for_assessment:
                de_hash = local_api_key_for_assessment + local_secret_key_for_assessment + request_ts
            else:
                de_hash = None
            hash = hashlib.sha256(de_hash.encode('utf8')).hexdigest()

        except:
            raise AuthenticationFailed()

        if hash_key != hash:
            raise AuthenticationFailed()

        return True