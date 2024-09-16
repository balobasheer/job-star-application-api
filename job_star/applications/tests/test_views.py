import json
import os

from decouple import config
from django.test import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from applications.models import Application, Applicant, ApplicationEmail
from jobs.models import Job, Cohort, Courses


# TODO Disable encryption before testing

class ApplicationListAPIViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        number_of_items = 15
        cohort = Cohort.objects.create(
            name='ATS 1',
            start_date="2023-01-05", end_date= "2023-06-30",
            application_start_date="2022-11-28T12:53:23+01:00",
            application_end_date="2022-12-21T12:53:23+01:00",
        )
        course = Courses.objects.create(title="Frontend")
        job = Job.objects.create(cohort=cohort, course=course)
        for num in range(1, number_of_items+1):
            applicant = Applicant.objects.create(
                first_name=f'First name {num}',
                last_name=f"Last name {num}",
                email=f"email{num}@gmail.com",
                **cls.applicant_detail()
            )
            Application.objects.create(
                job=job, applicant=applicant
            )

    @staticmethod
    def applicant_detail():
        applicant_data = {
            'phone_number': '08024918221',
            'gender': 'male',
            'date_of_birth': '2000-01-03',
            'country_of_origin': 'Nigeria',
            'current_location': 'Ibadan',
            'cover_letter': 'This is my cover letter of 400 characters',
            'qualification': 'B.Tech',
            'graduation_school': 'LAUTECH',
            'course_of_study': 'Computer Engineering',
            'graduation_grade': 'First Class',
            'years_of_experience': 1,
            'is_willing_to_relocate': 1,
        }
        return applicant_data

    @property
    def request_headers(self):
        headers = {
            'HTTP_API_KEY': config('BK_API_KEY'),
            'HTTP_REQUEST_TS': config('REQUEST_TS'),
            'HTTP_HASH_KEY': config('HASH_KEY')
        }
        return headers

    @property
    def file_url(self):
        return r'applications\tests\test.doc'

    def test_authorization(self):
        url = reverse('applications:applications')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_applications(self):
        url = reverse('applications:applications')
        self.client.credentials(**self.request_headers)
        res = self.client.get(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertTrue(bool(response['data']['next']), True)
        self.assertGreater(response['data']['count'], 0)

    def test_create_application(self):
        url = reverse('applications:create_application', args=[1])
        data = self.applicant_detail()
        data.update({
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'create@gmail.com',
            'resume': open(self.file_url, 'rb'),
            'other_attachment': open(self.file_url, 'rb')
        })
        self.client.credentials(**self.request_headers)
        response = self.client.post(url, data=data)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['success'], True)

    def test_application_detail(self):
        url = reverse('applications:application_detail', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.get(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertTrue(bool(response['data']['applicant']), True)
        self.assertTrue(bool(response['data']['application_id']), True)
        self.assertGreaterEqual(len(response['data']['application_id']), 10)
        self.assertTrue(bool(response['data']['course']), True)
        self.assertTrue(bool(response['data']['status']), True)

    def test_set_application_shortlisted(self):
        url = reverse('applications:shortlist', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'shortlisted')

    def test_set_application_invited_for_interview(self):
        url = reverse('applications:invite', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'invited')

    def test_set_application_passed(self):
        url = reverse('applications:passed', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'passed')

    def test_set_application_fai(self):
        url = reverse('applications:failed', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'failed')

    def test_set_application_accepted(self):
        url = reverse('applications:accept', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'accepted')

    def test_set_application_rejected(self):
        url = reverse('applications:reject', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.post(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['application_status'], 'rejected')

    def test_delete_application(self):
        url = reverse('applications:delete_application', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.delete(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['deleted'], True)


class ApplicationEmailTemplateTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        type = [
            'Shortlisted', 'Invited for Interview',
            'Accepted', 'Rejected', 'Invited for Assessment'
        ]
        for num in range(0,5):
            ApplicationEmail.objects.create(
                type=type[num],
                subject='Email Test',
                salutation='Hello',
                body="This is a new email"
            )

    @property
    def request_headers(self):
        headers = {
            'HTTP_API_KEY': config('BK_API_KEY'),
            'HTTP_REQUEST_TS': config('REQUEST_TS'),
            'HTTP_HASH_KEY': config('HASH_KEY')
        }
        return headers

    def test_get_all_email_templates(self):
        url = reverse('applications:emails')
        self.client.credentials(**self.request_headers)
        res = self.client.get(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertGreater(response['data']['count'], 0)

    def test_create_email_template(self):
        url = reverse('applications:emails')
        data = {
            'type': 'Completed Application',
            'subject': 'Completed',
            'salutation': 'Hi',
            'body': 'uyiop[ojhghjk'
        }
        self.client.credentials(**self.request_headers)
        response = self.client.post(url, data=data)
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['success'], True)

    def test_email_template_detail(self):
        url = reverse('applications:email_detail', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.get(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertTrue(bool(response['data']['type']), True)
        self.assertTrue(bool(response['data']['subject']), True)
        self.assertTrue(bool(response['data']['body']), True)

    def test_delete_email_template(self):
        url = reverse('applications:delete_email', args=[1])
        self.client.credentials(**self.request_headers)
        res = self.client.delete(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertEqual(response['data']['deleted'], True)

    def test_get_deleted_email_templates(self):
        email_object = ApplicationEmail.objects.get(id=1)
        email_object.is_deleted = True
        email_object.save()
        url = reverse('applications:trashed_emails')
        self.client.credentials(**self.request_headers)
        res = self.client.get(url, format='json')
        response = json.loads(res.content)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(response['success'], True)
        self.assertGreater(response['data']['count'], 0)

