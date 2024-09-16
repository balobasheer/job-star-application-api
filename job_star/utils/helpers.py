import requests

from celery import shared_task
from decouple import config

from jobs.models import Courses


endpoint = f"https://assessbk.afexats.com/api/assessment/application-type"

def header():
    head = {
        'api-key': config('ASSESSMENT_BACKEND_API_KEY'),
        'request-ts': config('REQUEST_TS'),
        'hash-key': config('ASSESSMENT_HASH_KEY')
    }
    return head


@shared_task()
def course_create_assessment_server(course_title, course_desc, course_uid):
    data = {
        'title': course_title,
        'description': course_desc,
        'uid': course_uid
    }
    response = requests.post(url=endpoint, json=data, headers=header())
    if str(response.status_code).startswith('2'):
        return "Created"
    return course_create_assessment_server.delay(
        course_title,
        course_desc,
        course_uid
    )


@shared_task()
def course_update_assessment_server(course_uid, course_title, course_desc):
    data = {
        'uid': course_uid,
        'title': course_title,
        'description': course_desc
    }

    response = requests.put(url=endpoint + f"/{course_uid}", json=data, headers=header())
    if str(response.status_code).startswith('2'):
        return 'Updated'
    elif response.status_code == 404:
        return False
    return course_update_assessment_server.delay(
        course_uid,
        course_title,
        course_desc,
    )


@shared_task()
def course_delete_assessment_server(is_deleted, course_uid):
    data = {
        'is_delete': is_deleted
    }
    response = requests.delete(url=endpoint + f"/{course_uid}", data=data, headers=header())
    if str(response.status_code).startswith('2'):
        return 'Delete status changed'
    elif str(response.status_code).startswith('4'):
        return False
    return course_delete_assessment_server.delay(
        is_deleted, course_uid
    )
