from ckeditor.fields import RichTextField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.reverse import reverse

from jobs.models import Job

# Create your models here.


class ActiveObject(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class DeletedObject(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class Applicant(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone_number = PhoneNumberField()
    gender = models.CharField(max_length=10)
    marital_status = models.CharField(max_length=10, default='single')
    date_of_birth = models.DateField()
    country_of_origin = models.CharField(max_length=50)
    current_location = models.CharField(max_length=50)
    resume = models.FileField(
        upload_to='resume',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc']
        )]
    )
    other_attachment = models.FileField(
        upload_to='other_attachments',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png']
        )],
        null=True, blank=True
    )
    cover_letter = models.TextField()
    qualification = models.CharField(max_length=20)
    years_of_experience = models.IntegerField(default=0)
    last_company_worked = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    last_position = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    graduation_school = models.CharField(max_length=200)
    course_of_study = models.CharField(max_length=100)
    graduation_grade = models.CharField(max_length=20)
    is_willing_to_relocate = models.BooleanField()
    is_completed_NYSC = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    active_objects = ActiveObject()
    deleted_objects = DeletedObject()

    objects = models.Manager()

    class Meta:
        ordering = ('first_name', 'last_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def fullname(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def number_of_applications(self):
        return self.applications(manager='active_objects').count()


class Application(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    application_id = models.CharField(max_length=20, null=True, blank=True)
    applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE,
        related_name='applications'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, null=True, blank=True, default="pending")
    is_deleted = models.BooleanField(default=False)

    active_objects = ActiveObject()
    deleted_objects = DeletedObject()

    objects = models.Manager()

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f"Application for {self.job} by {self.applicant}"

    def applicant_name(self):
        return f'{self.applicant.first_name} {self.applicant.last_name}'

    def applicant_email(self):
        return self.applicant.email

    def applicant_phone(self):
        phone_number = f"{self.applicant.phone_number.country_code}" \
                       f"{self.applicant.phone_number.national_number}"
        return phone_number

    @property
    def course(self):
        return self.job.course.title


@receiver(post_save, sender=Application)
def set_application_id(sender, instance, created, **kwargs):
    if created and not instance.application_id:
        if instance.id <= 9999:
            fill = 4
        elif instance.id <= 99999:
            fill = 5
        else:
            fill = 6
        id2string = str(instance.id).zfill(fill)
        course_title = instance.course.upper()
        specification = course_title.split(' ')
        first_name_id = instance.applicant.first_name[0].upper()
        last_name_id = instance.applicant.last_name[0].upper()
        spec_id_1 = specification[0][0]
        spec_id_2 = specification[1][0] if len(specification) > 1 else specification[0][1]
        application_id = f"{first_name_id}{last_name_id}-" \
                         f"{spec_id_1}{spec_id_2}-{id2string}"
        instance.application_id = application_id
        instance.save()


class ApplicationStatus(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='application_status',
    )
    status = models.CharField(
        max_length=30,
        default='pending',
    )
    activity = models.CharField(max_length=50)
    details = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)
        unique_together = ('application', 'status', 'activity',)

    @property
    def application__id(self):
        return self.application.application_id

    @property
    def applicant_name(self):
        return self.application.applicant_name()

    @property
    def applicant_email(self):
        return self.application.applicant.email

    @property
    def applicant_phone(self):
        return self.application.applicant_phone()

    @property
    def course(self):
        return self.application.course


@receiver(post_save, sender=ApplicationStatus)
def send_status_email(sender, instance, created, **kwargs):
    if created:
        application = instance.application
        application.status = instance.status
        application.save()


EMAIL_TYPE_CHOICES = (
    ('Completed Application', 'Completed Application'),
    ('Shortlisted', 'Shortlisted'),
    ('Invited for Interview', 'Invited for Interview'),
    ('Invited to Assessment', 'Invited to Assessment'),
    ('Accepted', 'Accepted'),
    ('Rejected', 'Rejected'),
)


class ApplicationEmail(models.Model):
    subject = models.CharField(max_length=100)
    salutation = models.CharField(max_length=10)
    body = RichTextField()
    type = models.CharField(
        choices=EMAIL_TYPE_CHOICES,
        max_length=30,
        unique=True
    )
    created_on = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    active_objects = ActiveObject(  )
    deleted_objects = DeletedObject()

    objects = models.Manager()

    class Meta:
        ordering = ('-created_on',)

