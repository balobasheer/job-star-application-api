import json
from decouple import config

from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from jobs.models import Courses, Cohort, Job

# TODO : celery must be running before performing any CRUD on course
# TODO : encryption must also be set to false

class TestCourseCRUDAPI(APITestCase):

    @classmethod
    def setUpTestData(cls):
        course = Courses.objects.bulk_create([
            Courses(title='Mobile Development with dart',
                    description='for mobile only'),
            Courses(title='Product Management',
                    description='for pm only'),
            Courses(title='Frontend Web development',
                    description='for frontend  only')
        ])
        course_d = Courses.objects.get(id=2)

        for cohort_number in range(1, 4):
            cohort = Cohort.objects.create(
                name=f"Ats {cohort_number}",
                start_date="2022-11-30",
                end_date=f"2022-12-1{cohort_number}",
                application_start_date=f"2022-{cohort_number}-07T12:52:59+01:00",
                application_end_date=f"2022-{cohort_number}-25T12:53:10+01:00",
            )
            cohort.courses.set(course)
            cohort.save()

            Job.objects.create(
                course=course_d,
                cohort=cohort,
                requirement='This short description for this job '
            )



    @property
    def request_headers(self):
        headers = {
            'HTTP_API_KEY': config('API_KEY'),
            'HTTP_REQUEST_TS': config('REQUEST_TS'),
            'HTTP_HASH_KEY': config('HASH_KEY')
        }
        return headers

    def test_create_courses(self):
        self.client.credentials(**self.request_headers)
        previous_course_count = Courses.objects.all()
        payload = {
            'title': 'Programming is easy',
            'description': 'The best way to programming'
        }
        response = self.client.post(reverse('job:course-create'), data=payload)
        self.assertEqual(Courses.objects.all().count(), previous_course_count + 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Programming is easy')

    def test_create_cohort(self):
        payload = {
            "name": "ats 1.1",
            "courses": [
                    {
                        "title": "Mobile Development with dart"
                    },
                    {
                        "title": "Product Management"
                    },
                    {
                        "title": "Frontend Web development"
                    },
                ], "cohort": 4,
            "application_start_date": "2022-12-07T12:52:59+01:00",
            "application_end_date": "2023-01-07T12:52:59+01:00",
            "start_date": "2022-01-02", "end_date": "2022-11-09"
        }
        self.client.credentials(**self.request_headers)
        res = self.client.post(reverse('job:cohort-create'), data=payload, format='json')
        response = json.loads(res.content)
        # print(response)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_all_cohorts(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:cohorts'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)
        self.assertGreater(len(response.data['results']), 0)

    def test_retrieve_one_cohort(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:cohort-detail', args=[1]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertIsInstance(response.data[''], dict)

    def test_update_cohort(self):
        payload = {
            "name": "ats 1.2",
            "courses": [
                {
                    "title": "Mobile Development with dart"
                },
                {
                    "title": "Product Management"
                },
                {
                    "title": "Frontend Web development"
                },
            ], "cohort": 4,
            "application_start_date": "2022-12-07T12:52:59+01:00",
            "application_end_date": "2023-01-07T12:52:59+01:00",
            "start_date": "2022-01-02", "end_date": "2022-11-09"
        }
        self.client.credentials(**self.request_headers)
        response = self.client.put(reverse('job:cohort-update', args=[1]), data=payload, format='json')
        res = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_cohort(self):
        self.client.credentials(**self.request_headers)
        response = self.client.post(reverse('job:cohort-delete', args=[1]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_count_down_application_end_date(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:count-down'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_job_create(self):
        self.client.credentials(**self.request_headers)
        payload = {
            "course": 1,
            "cohort": 1,
            "requirement": "This is the small requirement on this job biko.",
            'created_by': 'admin'
        }
        response = self.client.post(reverse('job:job-list-create'), data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_all_jobs(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:job-list-create'))
        # print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_job(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:job-detail', args=[1]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_jobs(self):
        self.client.credentials(**self.request_headers)
        response = self.client.post(reverse('job:job-delete', args=[1]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_edit_jobs(self):
        payload = {
            "course": 1,
            "cohort": 1,
            "requirement": "Job modified the small requirement on this job biko.",
            "created_by": "admin"
        }
        self.client.credentials(**self.request_headers)
        response = self.client.put(reverse('job:job-update', args=[1]), data=payload, format='json')
        print('Hey:', response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_job_application(self):
        self.client.credentials(**self.request_headers)
        response = self.client.get(reverse('job:applications', args=[1]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)




