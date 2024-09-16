import json
from datetime import timedelta

from django.db import IntegrityError
from django.db.models import Count, Subquery, OuterRef, IntegerField, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status
from rest_framework.generics import (
    CreateAPIView, GenericAPIView, ListCreateAPIView,
    ListAPIView, RetrieveUpdateAPIView, RetrieveAPIView, UpdateAPIView
)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from helpers.mixins import GenericDecryptionMixin, CustomDecryptionMixin
from helpers.utils import (
    send_application_shortlisted_mail, send_application_interview_mail,
    send_application_accepted_mail, send_application_rejected_mail, send_assessment_to_applicant
)
from job_star.encryption import encrypt_data, decrypt_data
# from parsers.parsers import CustomJSONParser
from jobs.models import Courses, Job, Cohort
from permissions.permissions import IsAdminOrAssessmentFrontendAuthenticated, IsAdminAuthenticated

from .models import Applicant, Application, ApplicationStatus, ApplicationEmail
from .serializers import (
    ApplicantSerializer, ApplicationDetailSerializer,
    ApplicationSerializer, TrackApplicationSerializer,
    TrackApplicationStatusSerializer, ApplicantListSerializer,
    ApplicationEmailListSerializer, ApplicationEmailDetailSerializer, ApplicationChartDataSerializer,
    ApplicationStatusSerializer,
)
from renderers.renderers import CustomRender


# Create your views here.


class ObjectMixin:

    def get_object(self):
        obj = self.queryset.filter(id=self.kwargs['pk']).first()
        return obj


class ApplicationListAPIView(ListAPIView):
    serializer_class = ApplicationSerializer
    parser_classes = (MultiPartParser, JSONParser,)

    def get_queryset(self):
        if self.kwargs.get('job_id'):
            return Application.active_objects.filter(
                job_id=self.kwargs['job_id']
            )
        return Application.active_objects.all()


class CreateApplicationAPIView(CreateAPIView):
    serializer_class = ApplicationSerializer
    parser_classes = (MultiPartParser, JSONParser,)

    def post(self, request, *args, **kwargs):
        try:
            dec_type = decrypt_data(request.data['data'])
            request._full_data = dec_type

        except:
            request._full_data = request.data

        job_id = kwargs['job_id']
        try:
            applicant = Applicant.objects.get(email__iexact=request.data['email'])
        except:
            applicant_serializer = ApplicantSerializer(data=request.data)
            applicant_serializer.is_valid(raise_exception=True)
            applicant = applicant_serializer.save()
        data = {
            'applicant': applicant.id,
            'job': job_id
        }
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ApplicationDetailAPIView(RetrieveAPIView):
    serializer_class = ApplicationDetailSerializer
    queryset = Application.objects.all()


class ApplicantListAPIView(ListAPIView):
    serializer_class = ApplicantListSerializer
    queryset = Applicant.active_objects.all()


class ApplicantDetailAPIView(GenericDecryptionMixin, RetrieveUpdateAPIView):
    serializer_class = ApplicantSerializer
    queryset = Applicant.objects.all()


class SetShortlistedApplicationAPIView(ObjectMixin, GenericAPIView):
    queryset = Application.active_objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if application:
            try:
                application_status = ApplicationStatus.objects.create(
                    application=application,
                    status="shortlisted",
                    activity="Shortlisted",
                    details="After reviewing all applications, yours was shortlisted"
                )
            except IntegrityError:
                latest_status = ApplicationStatus.objects.filter(
                    application=application
                ).first()
                if latest_status.status != "shortlisted":
                    return Response(
                        data=f"Application status cannot be changed"
                             f" to shortlisted after {latest_status.status}",
                        status=status.HTTP_400_BAD_REQUEST
                    )
                return Response(
                    data="Application status is already set to shortlisted",
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {
                'application_status': application_status.status
            }
            send_application_shortlisted_mail(application.applicant)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(
            data="No such application exists!",
            status=status.HTTP_404_NOT_FOUND
        )


class SetInvitedForInterviewAPIView(ObjectMixin, GenericAPIView):
    queryset = Application.active_objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if application:
            try:
                application_status = ApplicationStatus.objects.create(
                    application=application,
                    status="invited",
                    activity="Invited for Interview",
                    details="After reviewing all applications, you've been invited for interview"
                )
            except IntegrityError:
                latest_status = ApplicationStatus.objects.filter(
                    application=application
                ).first()
                if latest_status.status.lower() != "invited":
                    return Response(
                        data=f"Application status cannot be changed"
                             f" to invited after {latest_status.status}",
                        status=status.HTTP_400_BAD_REQUEST
                    )
                return Response(
                    data="Application status is already set to invited",
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {
                'application_status': application_status.status
            }
            send_application_interview_mail(application.applicant)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(
            data="No such application exists!",
            status=status.HTTP_404_NOT_FOUND
        )


class SetInvitedForAssessmentAPIView(ObjectMixin, GenericAPIView):
    queryset = Application.active_objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if application:
            try:
                application_status = ApplicationStatus.objects.create(
                    application=application,
                    status="invited for assessment",
                    activity="Invited for Assessment",
                    details="After reviewing all applications, you've been invited to take assessment"
                )
            except IntegrityError:
                latest_status = ApplicationStatus.objects.filter(
                    application=application
                ).first()
                if latest_status.status.lower() != "invited for assessment":
                    number_of_rejected = ApplicationStatus.objects.filter(
                        application=application,
                        status='rejected'
                    ).count()
                    application_status = ApplicationStatus.objects.create(
                        application=application,
                        status="invited for assessment",
                        activity=f"Invited for Assessment {number_of_rejected + 1}",
                        details="After reviewing all applications, you've been invited to take assessment"
                    )
                    data = {
                        'application_status': application_status.status
                    }
                    send_assessment_to_applicant(application)
                    return Response(data=data, status=status.HTTP_200_OK)
                return Response(
                    data="Application status is already set to invited for assessment",
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {
                'application_status': application_status.status
            }
            send_assessment_to_applicant(application)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(
            data="No such application exists!",
            status=status.HTTP_404_NOT_FOUND
        )


class SetAcceptedApplicationAPIView(ObjectMixin, GenericAPIView):
    queryset = Application.active_objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if application:
            try:
                application_status = ApplicationStatus.objects.create(
                    application=application,
                    status="accepted",
                    activity="Accepted Application",
                    details="We are pleased to inform you that you have "
                            "been selected for the AFEX TECH STARS. More "
                            "details on this will be sent to you by mail. "
                            "Congratulations."
                )
            except IntegrityError:
                latest_status = ApplicationStatus.objects.filter(
                    application=application
                ).first()
                if latest_status.status.lower() != "accepted":
                    number_of_accepted_time = ApplicationStatus.objects.filter(
                        application=application,
                        status='accepted'
                    ).count()
                    application_status = ApplicationStatus.objects.create(
                        application=application,
                        status="accepted",
                        activity=f"Accepted Application {number_of_accepted_time + 1}",
                        details="We are pleased to inform you that you have "
                                "been selected for the AFEX TECH STARS. More "
                                "details on this will be sent to you by mail. "
                                "Congratulations."
                    )
                    data = {
                        'application_status': application_status.status
                    }
                    send_application_accepted_mail(application.applicant)
                    return Response(data=data, status=status.HTTP_200_OK)
                return Response(
                    data="Application status is already set to accepted",
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {
                'application_status': application_status.status
            }
            send_application_accepted_mail(application.applicant)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(
            data="No such application exists!",
            status=status.HTTP_404_NOT_FOUND
        )


class SetRejectedApplicationAPIView(ObjectMixin, GenericAPIView):
    queryset = Application.objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if application:
            try:
                application_status = ApplicationStatus.objects.create(
                    application=application,
                    status="rejected",
                    activity="Rejected Application",
                    details="After reviewing your application,"
                            " we are sorry to inform you that we will "
                            "not be proceeding with your application. "
                            "Thank you."
                )
            except IntegrityError:
                latest_status = ApplicationStatus.objects.filter(
                    application=application
                ).first()
                if latest_status.status.lower() != "rejected":
                    number_of_rejected = ApplicationStatus.objects.filter(
                        application=application,
                        status='rejected'
                    ).count()
                    application_status = ApplicationStatus.objects.create(
                        application=application,
                        status="rejected",
                        activity=f"Rejected Application {number_of_rejected + 1}",
                        details="After reviewing your application,"
                                " we are sorry to inform you that we will "
                                "not be proceeding with your application. "
                                "Thank you."
                    )
                    data = {
                        'application_status': application_status.status
                    }
                    send_application_rejected_mail(application.applicant)
                    return Response(data=data, status=status.HTTP_200_OK)
                return Response(
                    data=f"Application status is already set to rejected",
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {
                'application_status': application_status.status
            }
            send_application_rejected_mail(application.applicant)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(
            data="No such application exists!",
            status=status.HTTP_404_NOT_FOUND
        )


class SetPassedApplicationTestAPIView(CustomDecryptionMixin, GenericAPIView):

    def post(self, request, *args, **kwargs):
        # req = super(SetPassedApplicationTestAPIView, self).post(request, *args, **kwargs)
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except KeyError:
            # request_data = request.data
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # request_data = request.data
            return Response(
                data=f"Invalid encryption: {e}",
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.data.get('application_id'):
            try:
                application = Application.objects.get(
                    application_id__iexact=request.data['application_id']
                )
                try:
                    application_status = ApplicationStatus.objects.create(
                        application=application,
                        status="passed",
                        activity="Passed Assessment",
                        details="You have passed your assessment and will "
                                "receive a mail when there is an update"
                    )
                    data = {
                        'application_status': application_status.status
                    }
                    return Response(data=data, status=status.HTTP_200_OK)
                except IntegrityError:
                    return Response(
                        data="Application status is already set to passed",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except:
                return Response(
                    data="No such application exists",
                    status=status.HTTP_404_NOT_FOUND
                )
        data = {
            'application_id': "This field is required"
        }
        return Response(
            data=data,
            status=status.HTTP_404_NOT_FOUND
        )


class SetFailedApplicationTestAPIView(CustomDecryptionMixin, GenericAPIView):

    def post(self, request, *args, **kwargs):
        try:
            super(SetFailedApplicationTestAPIView, self).post(request, *args, **kwargs)
        except KeyError:
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # request_data = request.data
            return Response(
                data=f"Invalid encryption: {e}",
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.data.get('application_id'):
            try:
                application = Application.objects.get(
                    application_id__iexact=request.data['application_id']
                )
                try:
                    application_status = ApplicationStatus.objects.create(
                        application=application,
                        status="failed",
                        activity="Failed Assessment",
                        details="You have failed your assessment and will "
                                "receive a mail when there is an update"
                    )
                    data = {
                        'application_status': application_status.status
                    }
                    return Response(data=data, status=status.HTTP_200_OK)
                except IntegrityError:
                    return Response(
                        data="Application status is already set to failed",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except:
                return Response(
                    data="No such application exists",
                    status=status.HTTP_404_NOT_FOUND
                )
        data = {
            'application_id': "This field is required"
        }
        return Response(
            data=data,
            status=status.HTTP_404_NOT_FOUND
        )


class PendingApplicationListAPIView(ListAPIView):
    queryset = Application.active_objects.filter(
        status='pending'
    )
    serializer_class = ApplicationSerializer


class ShortlistedApplicationListAPIView(ListAPIView):
    # queryset = Application.active_objects.filter(
    #     status='shortlisted'
    # )
    # queryset = Application.active_objects.filter(
    #     application_status__status__='shortlisted'
    # )
    queryset = ApplicationStatus.objects.filter(
        status='shortlisted'
    )
    serializer_class = ApplicationStatusSerializer


class InvitedApplicationListAPIView(ListAPIView):
    queryset = Application.active_objects.filter(
        status='invited'
    )
    serializer_class = ApplicationSerializer


class AcceptedApplicationListAPIView(ListAPIView):
    queryset = Application.active_objects.filter(
        status='accepted'
    )
    serializer_class = ApplicationSerializer


class RejectedApplicationListAPIView(ListAPIView):
    queryset = Application.active_objects.filter(
        status='rejected'
    )
    serializer_class = ApplicationSerializer


class TrackApplicationAPIView(CustomDecryptionMixin, GenericAPIView):
    # parser_classes = (CustomJSONParser,)

    def post(self, request, *args, **kwargs):
        # req = super(TrackApplicationAPIView, self).post(request, *args, **kwargs)
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except KeyError:
            # request_data = request.data
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # request_data = request.data
            return Response(
                data=f"Invalid encryption: {e}",
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.data.get('application_id'):
            try:
                application = Application.objects.get(
                    application_id__iexact=request.data['application_id']
                )
            except:
                return Response(
                    data="No such application exists",
                    status=status.HTTP_404_NOT_FOUND
                )
            queryset = ApplicationStatus.objects.filter(application=application)
            serializer = TrackApplicationStatusSerializer(queryset, many=True)
            data = {
                'applicant_name': application.applicant.fullname(),
                'application_id': application.application_id,
                'application_status': serializer.data,
            }
            return Response(
                # data=encrypt_data(data=data),
                data=data,
                status=status.HTTP_200_OK
            )
        data = {
            'application_id': "This field is required"
        }
        return Response(
            data=data,
            status=status.HTTP_404_NOT_FOUND
        )


class ValidateApplicationIDAPIView(CustomDecryptionMixin, GenericAPIView):
    permission_classes = (
        IsAdminOrAssessmentFrontendAuthenticated,
    )

    def post(self, request, *args, **kwargs):
        # super(ValidateApplicationIDAPIView, self).post(request, *args, **kwargs)
        try:
            dec_data = decrypt_data(request.data['data'])
            request._full_data = dec_data
        except KeyError:
            # request_data = request.data
            return Response(
                data="Got a plain data instead of encrypted data",
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # request_data = request.data
            return Response(
                data=f"Invalid encryption: {e}",
                status=status.HTTP_400_BAD_REQUEST
            )

        application_id = request.data.get('application_id')
        try:
            data = urlsafe_base64_decode(application_id).decode('utf-8')
        except UnicodeError:
            return Response(
                data="Sorry, the data is not same as the encoded id",
                status=status.HTTP_400_BAD_REQUEST
            )
        request.data['application_id'] = data
        serializer = TrackApplicationSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        application = Application.objects.filter(
            application_id__iexact=serializer.data['application_id']
        ).first()
        if application:
            data = {
                'applicant_name': application.applicant_name(),
                'applicant_email': application.applicant_email(),
                'application_id': application.application_id,
                'course': application.course
            }
            return Response(
                data=data,
                status=status.HTTP_200_OK
            )
        return Response(
            data="No such application exists",
            status=status.HTTP_404_NOT_FOUND
        )


class ApplicationEmailTemplateAPIView(GenericDecryptionMixin, ListCreateAPIView):
    serializer_class = ApplicationEmailListSerializer
    queryset = ApplicationEmail.active_objects.all()


class ApplicationEmailTemplateDetailAPIView(RetrieveAPIView):
    serializer_class = ApplicationEmailDetailSerializer
    queryset = ApplicationEmail.active_objects.all()


class ApplicationEmailTemplateEditAPIView(GenericDecryptionMixin, UpdateAPIView):
    serializer_class = ApplicationEmailDetailSerializer
    queryset = ApplicationEmail.active_objects.all()


class DeleteApplicationAPIView(GenericAPIView):
    queryset = Application.objects.all()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = not instance.is_deleted
        instance.save()
        state = "trashed" if instance.is_deleted else "restored"
        data = {
            'deleted': instance.is_deleted,
            'message': f"Application {state} successfully"
        }
        return Response(
            data=data,
            status=status.HTTP_200_OK
        )


class DeleteApplicantAPIView(GenericAPIView):
    queryset = Applicant.objects.all()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = not instance.is_deleted
        instance.save()
        for application in instance.applications(manager='objects').all():
            application.is_deleted = instance.is_deleted
            application.save()
        state = "trashed" if instance.is_deleted else "restored"
        data = {
            'deleted': instance.is_deleted,
            'message': f"Applicant {state} successfully"
        }
        return Response(
            data=data,
            status=status.HTTP_200_OK
        )


class DeleteEmailTemplateAPIView(GenericAPIView):
    queryset = ApplicationEmail.objects.all()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = not instance.is_deleted
        instance.save()
        state = "trashed" if instance.is_deleted else "restored"
        data = {
            'deleted': instance.is_deleted,
            'message': f"Email template {state} successfully"
        }
        return Response(
            data=data,
            status=status.HTTP_200_OK
        )


class DeletedApplicationAPIView(ListAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.deleted_objects.all()


class DeletedApplicantAPIView(ListAPIView):
    serializer_class = ApplicantListSerializer
    queryset = Applicant.deleted_objects.all()


class DeletedEmailTemplateAPIView(ListAPIView):
    serializer_class = ApplicationEmailListSerializer
    queryset = ApplicationEmail.deleted_objects.all()


class SendAssessmentToApplicantAPIView(GenericAPIView):
    queryset = Application.active_objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        send_assessment_to_applicant(application)
        return Response(data="Assessment sent successfully")


class OneWeekApplicationDataAPIView(GenericAPIView):
    serializer_class = ApplicationChartDataSerializer

    @property
    def get_days_ago(self):
        path = self.request.path
        if '7-days-ago' in path:
            return 7
        elif '14-days-ago' in path:
            return 14
        elif '30-days-ago' in path:
            return 30

    def get_queryset(self, cohort):
        one_week_ago = timezone.now() - timedelta(days=self.get_days_ago)
        queryset = Courses.active_courses.filter(cohort=cohort).annotate(# Application.objects.filter(job__course_id=OuterRef('pk')
            total_applications=Coalesce(Subquery(
                Job.active_jobs.filter(
                    course=OuterRef('pk'),
                    applications__timestamp__gte=one_week_ago
                ).annotate(
                    number_of_applications=Count('applications')
                ).values('number_of_applications'),
                output_field=IntegerField()
            ), 0)
        ).annotate(
            total_assessments_taken=Coalesce(Subquery(
                Job.active_jobs.filter(
                    Q (course=OuterRef('pk')) &
                    Q (applications__timestamp__gte=one_week_ago) &
                    Q ( Q (applications__status__iexact='passed') |
                        Q (applications__status__iexact='failed'))
                ).annotate(
                    number_of_applications=Count('applications')
                ).values('number_of_applications'),
                output_field=IntegerField()
            ), 0)
        ).order_by('total_applications', 'title')
        return queryset

    def get(self, request, *args, **kwargs):
        cohort = Cohort.objects.filter(
            id=kwargs['pk']
        ).first()
        if cohort:
            serializer = self.get_serializer(self.get_queryset(cohort), many=True)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            data="No such cohort exists",
            status=status.HTTP_404_NOT_FOUND
        )


class AllTimeApplicationDataAPIView(GenericAPIView):
    serializer_class = ApplicationChartDataSerializer

    def get_queryset(self, cohort):
        queryset = Courses.active_courses.filter(cohort=cohort).annotate(
            total_applications=Count('jobs__applications')
        ).annotate(
            total_assessments_taken=Coalesce(Subquery(
                Job.active_jobs.filter(
                    Q (course=OuterRef('pk')) &
                    Q ( Q (applications__status__iexact='passed') |
                        Q (applications__status__iexact='failed'))
                ).annotate(
                    number_of_applications=Count('applications')
                ).values('number_of_applications'),
                output_field=IntegerField()
            ), 0)
        ).order_by('total_applications', 'title')
        return queryset

    def get(self, request, *args, **kwargs):
        cohort = Cohort.objects.filter(
            id=kwargs['pk']
        ).first()
        if cohort:
            serializer = self.get_serializer(self.get_queryset(cohort), many=True)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            data="No such cohort exists",
            status=status.HTTP_404_NOT_FOUND
        )