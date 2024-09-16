import logging
import os
from decouple import config

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

log = logging.getLogger(__name__)


class ResponseLoggingMiddleware(MiddlewareMixin):
    req = None
    request_by= None
    admin_frontend = None

    def basicConfig(self, **messages):

        api_key = self.req.META.get('HTTP_API_KEY')
        if api_key == config('BK_API_KEY'):
            self.request_by = 'Backend'
        elif api_key == config('API_KEY_FRONTEND'):
            self.request_by = 'Admin frontend'
        elif api_key == config('API_KEY_FOR_WEBSITE_FRONTEND'):
            self.request_by = 'Website frontend'
        else:
            self.request_by = 'Assessment frontend'

        with open(file='app_jobs.log', mode='a') as file:
            handler = file.write(
                f'Time: {messages["time"]}' + "  "
                f'Method:{self.req.method}' + "  "
                f'Request_by:{self.request_by}' + "  "
                f'Status_code:{messages["method"]}' + " "
                f"Endpoint: {messages['endpoint']}\n"
            )

            return handler

    def process_response(self, request, response):
        self.req = request
        try:

            log.info(self.basicConfig(
                time=timezone.now(),
                filename="app_jobs.log",
                method=f'{response.status_code}',
                endpoint=f"{request.META['REMOTE_ADDR']}"
                         f"{request.get_full_path()}"
            ))
        except Exception as e:
            log.error(f'RequestLoggingMiddleware error : {e}')

        return response
