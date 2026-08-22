from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models

validate_image_extension = FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])


class Institution(models.Model):
    TYPE_CHOICES = [
        ('school', 'School'),
        ('college', 'College'),
        ('coaching', 'Coaching Institute')
    ]
    STATUS_CHOICES = [('active', 'Active'), ('pending', 'Pending'), ('suspended', 'Suspended')]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    board_affiliation = models.CharField(max_length=100, blank=True)  # CBSE/ICSE/State/Univ/Exam Target
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    admin_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                    related_name='managed_institution')
    onboarded_by_partner = models.ForeignKey('partners.Partner', null=True, blank=True,
                                              on_delete=models.SET_NULL)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_institutions')
    assigned_employee = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='assigned_institutions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    allowed_categories = models.ManyToManyField('courses.CourseCategory', blank=True, related_name='institutions')
    allowed_courses = models.ManyToManyField('courses.Course', blank=True, related_name='institutions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Batch(models.Model):
    """
    Batches for Coaching Institutes, Schools, or Colleges.
    Allows grouping students into target batches (e.g. NEET Droppers, JEE Target 2027).
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    target_exam = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.institution.name})"


class Student(models.Model):
    """
    Replaces InstitutionStudent. One row per student, 1:1 with accounts.User
    (role='student'), holding everything academic/personal that Institution
    Admin, Teacher, and Parent dashboards need.
    """

    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'),
                       ('other', 'Other'), ('prefer_not_to_say', 'Prefer Not to Say')]
    BLOOD_GROUP_CHOICES = [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
                            ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-')]
    CATEGORY_CHOICES = [('general', 'General'), ('obc', 'OBC'), ('sc', 'SC'),
                         ('st', 'ST'), ('ews', 'EWS')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'),
                       ('graduated', 'Graduated'), ('transferred', 'Transferred'),
                       ('dropped', 'Dropped Out')]

    # Core links
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE,
                                 related_name='student_profile',
                                 limit_choices_to={'role': 'student'})
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='students')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='students')

    # Academic identity
    admission_no = models.CharField(max_length=50, unique=True)
    roll_number = models.CharField(max_length=20, blank=True)
    class_grade = models.CharField(max_length=50)          # "Class 10", "NEET Batch", "B.Tech CSE"
    section = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=9)          # "2026-27"
    admission_date = models.DateField(null=True, blank=True)

    # Personal details
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES,
                               default='prefer_not_to_say', blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general', blank=True)

    # Parent / Guardian
    father_name = models.CharField(max_length=255, blank=True)
    mother_name = models.CharField(max_length=255, blank=True)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message='Enter a valid phone number.')])
    guardian_email = models.EmailField(blank=True)
    parent_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='children', limit_choices_to={'role': 'parent'})

    # Documents
    aadhar_or_id_proof = models.FileField(upload_to='student_docs/id_proof/', null=True, blank=True)
    profile_photo = models.ImageField(upload_to='student_docs/photos/', null=True, blank=True, validators=[validate_image_extension])

    # Logistics
    emergency_contact_phone = models.CharField(max_length=15, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['institution', 'class_grade', 'section']),
            models.Index(fields=['admission_no']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['institution', 'roll_number', 'class_grade', 'academic_year'],
                condition=models.Q(roll_number__gt=''),
                name='unique_roll_number_per_class_per_year'
            )
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.admission_no})"

    def clean(self):
        if self.institution and self.institution.type not in ('school', 'college', 'coaching'):
            raise ValidationError("Institution must be School, College, or Coaching Institute.")

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )