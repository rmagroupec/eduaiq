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


class Department(models.Model):
    name = models.CharField(_('Department Name'), max_length=100, unique=True)
    code = models.CharField(_('Department Code'), max_length=20, unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return self.name


class Designation(models.Model):
    title = models.CharField(_('Designation Title'), max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Designation')
        verbose_name_plural = _('Designations')

    def __str__(self):
        return f"{self.title} ({self.department.name})"


class EmployeeProfile(models.Model):
    class OnboardingStatusChoices(models.TextChoices):
        DOCS_PENDING = 'docs_pending', _('Documents Pending')
        UNDER_REVIEW = 'under_review', _('Under Review')
        ACTIVE = 'active', _('Active / Completed')
        REJECTED = 'rejected', _('Rejected')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(_('Employee ID'), max_length=30, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    joining_date = models.DateField(_('Joining Date'), null=True, blank=True)
    probation_end_date = models.DateField(_('Probation End Date'), null=True, blank=True)
    
    emergency_contact_name = models.CharField(_('Emergency Contact Name'), max_length=150, blank=True)
    emergency_contact_phone = models.CharField(_('Emergency Contact Phone'), max_length=20, blank=True)
    bank_account_number = models.CharField(_('Bank Account Number'), max_length=50, blank=True)
    bank_ifsc = models.CharField(_('Bank IFSC Code'), max_length=20, blank=True)
    bank_name = models.CharField(_('Bank Name'), max_length=100, blank=True)
    
    onboarding_status = models.CharField(
        _('Onboarding Status'),
        max_length=20,
        choices=OnboardingStatusChoices.choices,
        default=OnboardingStatusChoices.DOCS_PENDING
    )
    notes = models.TextField(_('HR Notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Employee Profile')
        verbose_name_plural = _('Employee Profiles')

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"


class EmployeeDocument(models.Model):
    class DocTypeChoices(models.TextChoices):
        ID_PROOF = 'id_proof', _('ID Proof (Aadhaar/Passport/Govt ID)')
        PAN_CARD = 'pan_card', _('PAN Card')
        DEGREE = 'degree', _('Educational Certificate / Degree')
        EXPERIENCE = 'experience', _('Relieving / Experience Letter')
        BANK_PROOF = 'bank_proof', _('Bank Proof / Cancelled Cheque')
        OTHER = 'other', _('Other Document')

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(_('Document Type'), max_length=30, choices=DocTypeChoices.choices)
    document_name = models.CharField(_('Document Name/Title'), max_length=255)
    file = models.FileField(_('Document File'), upload_to='employee_documents/%Y/%m/')
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Employee Document')
        verbose_name_plural = _('Employee Documents')

    def __str__(self):
        return f"{self.employee.employee_id} - {self.get_doc_type_display()}"


class OnboardingTask(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='onboarding_tasks')
    title = models.CharField(_('Task Title'), max_length=255)
    description = models.TextField(_('Task Description'), blank=True)
    is_completed = models.BooleanField(_('Is Completed'), default=False)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Onboarding Task')
        verbose_name_plural = _('Onboarding Tasks')

    def __str__(self):
        status = "Done" if self.is_completed else "Pending"
        return f"{self.employee.employee_id}: {self.title} ({status})"


class Attendance(models.Model):
    """
    Attendance model for tracking daily attendance of Users (Employees, Teachers, Students).
    """
    class StatusChoices(models.TextChoices):
        PRESENT = 'P', _('Present')
        ABSENT = 'A', _('Absent')
        HOLIDAY = 'H', _('Holiday')
        HALF_DAY = 'F', _('Half Day')
        LATE = 'L', _('Late')
        WORK_FROM_HOME = 'WFH', _('Work From Home')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(_('Date'))
    status = models.CharField(
        _('Status'),
        max_length=5,
        choices=StatusChoices.choices,
        default=StatusChoices.PRESENT
    )
    academic_year = models.CharField(_('Academic Year'), max_length=20, default='2025/2026')
    check_in = models.TimeField(_('Check In Time'), null=True, blank=True)
    check_out = models.TimeField(_('Check Out Time'), null=True, blank=True)
    remarks = models.CharField(_('Remarks'), max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        unique_together = ('user', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['academic_year']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.date}: {self.get_status_display()}"


class WFHRequest(models.Model):
    """
    Model to track Work From Home (WFH) applications and Admin approvals.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wfh_requests')
    leave_type = models.CharField(_('Leave Type'), max_length=100, default='Work From Home (WFH)')
    target_email = models.CharField(_('Target Email'), max_length=255, blank=True, null=True)
    target_name = models.CharField(_('Target Name'), max_length=255, blank=True, null=True)
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    reason = models.TextField(_('Reason for WFH'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_wfh_requests'
    )
    admin_remarks = models.CharField(_('Admin Remarks'), max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('WFH Request')
        verbose_name_plural = _('WFH Requests')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.start_date} to {self.end_date}) - {self.get_status_display()}"

