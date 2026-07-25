from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """
    Dynamic Role model for storing user roles.
    """
    name = models.CharField(
        _('Role Name'),
        max_length=100,
        unique=True
    )

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom User model extending AbstractUser for EduAiQ School Management System.
    """

    # Gender Choices
    class GenderChoices(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHER = 'other', _('Other')
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', _('Prefer Not to Say')

    # Caste Category Choices
    class CasteCategoryChoices(models.TextChoices):
        GENERAL = 'general', _('General')
        OBC = 'obc', _('OBC')
        SC = 'sc', _('SC')
        ST = 'st', _('ST')
        EWS = 'ews', _('EWS')

    # Marital Status Choices
    class MaritalStatusChoices(models.TextChoices):
        SINGLE = 'single', _('Single')
        MARRIED = 'married', _('Married')
        DIVORCED = 'divorced', _('Divorced')
        WIDOWED = 'widowed', _('Widowed')

    # Contract Type Choices
    class ContractTypeChoices(models.TextChoices):
        FULL_TIME = 'full_time', _('Full Time')
        PART_TIME = 'part_time', _('Part Time')
        CONTRACT = 'contract', _('Contract')
        TEMPORARY = 'temporary', _('Temporary')
        PERMANENT = 'permanent', _('Permanent')

    # Shift Choices
    class ShiftChoices(models.TextChoices):
        MORNING = 'morning', _('Morning')
        AFTERNOON = 'afternoon', _('Afternoon')
        EVENING = 'evening', _('Evening')
        NIGHT = 'night', _('Night')

    # Status Choices
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')

    # Authentication Fields (extending AbstractUser)
    phone = models.CharField(
        _('Phone'),
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Phone number must be between 9 and 15 digits.'),
                code='invalid_phone'
            )
        ]
    )

    # Personal Details
    profile_image = models.ImageField(
        _('Profile Image'),
        upload_to='profile_images/%Y/%m/%d/',
        null=True,
        blank=True
    )
    date_of_birth = models.DateField(
        _('Date of Birth'),
        null=True,
        blank=True
    )
    gender = models.CharField(
        _('Gender'),
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.PREFER_NOT_TO_SAY,
        blank=True
    )
    caste_category = models.CharField(
        _('Caste Category'),
        max_length=20,
        choices=CasteCategoryChoices.choices,
        default=CasteCategoryChoices.GENERAL,
        blank=True
    )
    marital_status = models.CharField(
        _('Marital Status'),
        max_length=20,
        choices=MaritalStatusChoices.choices,
        default=MaritalStatusChoices.SINGLE,
        blank=True
    )
    father_name = models.CharField(
        _('Father Name'),
        max_length=255,
        blank=True
    )
    mother_name = models.CharField(
        _('Mother Name'),
        max_length=255,
        blank=True
    )

    # Professional Details
    role = models.CharField(
        _('Role'),
        max_length=100,
        blank=False
    )
    qualification = models.CharField(
        _('Qualification'),
        max_length=255,
        blank=True
    )
    experience = models.PositiveIntegerField(
        _('Experience (in years)'),
        default=0,
        blank=True
    )
    contract_type = models.CharField(
        _('Contract Type'),
        max_length=20,
        choices=ContractTypeChoices.choices,
        blank=True
    )
    shift = models.CharField(
        _('Shift'),
        max_length=20,
        choices=ShiftChoices.choices,
        blank=True
    )
    joining_date = models.DateField(
        _('Joining Date'),
        null=True,
        blank=True
    )
    school_name = models.CharField(
        _('School Name'),
        max_length=255,
        blank=True
    )
    academic_year = models.CharField(
        _('Academic Year'),
        max_length=9,
        blank=True
    )

    # Social Links
    facebook = models.URLField(
        _('Facebook'),
        blank=True
    )
    instagram = models.URLField(
        _('Instagram'),
        blank=True
    )
    linkedin = models.URLField(
        _('LinkedIn'),
        blank=True
    )

    # Other Fields
    description = models.TextField(
        _('Description'),
        blank=True
    )
    is_verified = models.BooleanField(
        _('Is Verified'),
        default=False
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Updated At'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class Profile(models.Model):
    """
    Extended profile model for storing address information linked to User.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    address = models.TextField(
        _('Address'),
        blank=True
    )
    city = models.CharField(
        _('City'),
        max_length=255,
        blank=True
    )
    state = models.CharField(
        _('State'),
        max_length=255,
        blank=True
    )
    pincode = models.CharField(
        _('Pincode'),
        max_length=10,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{5,10}$',
                message=_('Pincode must be between 5 and 10 digits.'),
                code='invalid_pincode'
            )
        ]
    )

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"