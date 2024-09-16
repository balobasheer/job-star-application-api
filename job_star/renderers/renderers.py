from rest_framework.renderers import JSONRenderer

from job_star.encryption import encrypt_data


class CustomRender(JSONRenderer):

    def render(
            self,
            data,
            accepted_media_type=None,
            renderer_context=None):
        status_code = renderer_context["response"].status_code
        response = {}
        if str(status_code).startswith("4") or str(status_code).startswith("5"):
            response['success'] = False
            response['error'] = data
        else:
            response['success'] = True
            response['data'] = data
            # response['data'] = encrypt_data(data)

        return super(CustomRender, self).render(response, accepted_media_type, renderer_context)
