from datetime import timedelta, datetime

from django.utils import timezone
from django.utils.baseconv import base64
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueTogetherValidator

from helpers.utils import send_application_success_mail
from jobs.models import Job, Cohort, Courses
from .models import Applicant, Application, ApplicationStatus, ApplicationEmail


class ApplicantListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='applications:applicant_detail',
        lookup_field='pk',
        read_only=True
    )

    class Meta:
        model = Applicant
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'number_of_applications',
            'url',
        )


class ApplicantApplicationsSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='applications:application_detail',
        lookup_field='pk',
        read_only=True
    )

    class Meta:
        model = Application
        fields = (
            'application_id',
            'course',
            'status',
            'url',
        )


class ApplicantApplicationDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Applicant
        exclude = ('id', 'is_deleted',)


class ApplicantSerializer(serializers.ModelSerializer):
    applications = ApplicantApplicationsSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Applicant
        exclude = ('id',)

        extra_kwargs = {
            'resume': {'required': True}
        }

    def validate_gender(self, value):
        # check if the applicant's gender is either male or female
        if value.lower() not in ('male', 'female'):
            raise serializers.ValidationError(
                "Gender can either be male or female"
            )
        return value

    def validate_date_of_birth(self, value):
        # minimum age of an applicant is 16
        # get the minimum age in days
        min_age_in_days = timedelta(days=16*365)

        # get today's date
        today = datetime.today().date()

        # check if difference of today's date and the applicant date of birth
        # is more than minimum age
        if (today-value) < min_age_in_days:
            raise serializers.ValidationError(
                "Minimum age for an applicant is 16, kindly enter a valid date of birth."
            )
        return value

    def validate_resume(self, value):
        size_limit = 1 * 1024 * 1024

        if value and value.size > size_limit:
            raise serializers.ValidationError(
                "Resume size cannot be greater than 1MB"
            )

        return value

    def validate_other_attachment(self, value):
        size_limit = 1 * 1024 * 1024

        if value and value.size > size_limit:
            raise serializers.ValidationError(
                "Attachment size cannot be greater than 1MB"
            )

        return value


class ApplicationSerializer(serializers.ModelSerializer):
    # applicant = ApplicantSerializer(write_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='applications:application_detail',
        lookup_field='pk',
        read_only=True
    )

    class Meta:
        model = Application
        fields = (
            'job',
            'applicant',
            'applicant_name',
            'applicant_email',
            'applicant_phone',
            'application_id',
            'course',
            'status',
            'url',
        )

        extra_kwargs = {
            'applicant': {'write_only': True},
            'job': {'write_only': True}
        }

    def validate(self, attrs):
        try:
            job = attrs['job']
        except:
            raise serializers.ValidationError(
                "Application must be tied to a job"
            )

        try:
            cohort = Cohort.objects.get(jobs=job)
        except:
            raise serializers.ValidationError(
                "Job does not belong to a cohort"
            )

        if not cohort.application_end_date >= timezone.now():
            raise serializers.ValidationError(
                "No open application for job's cohort"
            )
        applicant = attrs.get('applicant')
        application = Application.objects.filter(
            job__cohort=cohort,
            applicant=applicant
        ).exists()
        if application:
            raise serializers.ValidationError(
                "Applicant already applied for the job"
            )
        return attrs

    def create(self, validated_data):
        application = Application.objects.create(
            **validated_data
        )
        application_status = ApplicationStatus.objects.create(
            application=application,
            activity="Completed Application",
            details="You have completed your application and "
                    "will receive a mail when there is an update"
        )
        send_application_success_mail(application)
        return application


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant = ApplicantApplicationDetailSerializer(read_only=True)

    class Meta:
        model = Application
        fields = (
            'applicant',
            'application_id',
            'course',
            'status',
        )


class TrackApplicationSerializer(serializers.Serializer):
    application_id = serializers.CharField()


class TrackApplicationStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApplicationStatus
        fields = (
            'status',
            'application',
            'activity',
            'details',
            'timestamp',
        )
        extra_kwargs = {
            'application': {'write_only': True}
        }


class ApplicationEmailListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='applications:email_detail',
        lookup_field='pk',
        read_only=True
    )

    class Meta:
        model = ApplicationEmail
        fields = (
            'id',
            'type',
            'subject',
            'salutation',
            'body',
            'created_on',
            'last_modified',
            'url'
        )
        extra_kwargs = {
            'salutation': {'write_only': True},
            'body': {'write_only': True},
        }


class ApplicationEmailDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApplicationEmail
        exclude = ('id',)


class ApplicationChartDataSerializer(serializers.ModelSerializer):
    total_applications = serializers.IntegerField()
    total_assessments_taken = serializers.IntegerField()
    course = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('course', 'total_applications', 'total_assessments_taken',)

    def get_course(self, obj):
        return obj.title


class ApplicationStatusSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApplicationStatus
        fields = (
            'applicant_name',
            'applicant_email',
            'applicant_phone',
            'application__id',
            'course',
            'status',
            'url',
        )

    def get_url(self, obj):
        request = self.context.get('request')
        return reverse(
            'applications:application_detail',
            args=[obj.application_id],
            request=request
        )

