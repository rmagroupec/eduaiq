from django.core.exceptions import ValidationError
from django.db import models

class OlympiadCategory(models.Model):
    name = models.CharField(max_length=100)   # Science, Maths, AI, Coding, Robotics, GK

class Olympiad(models.Model):
    LEVELS = [('school', 'School Level'), ('zonal', 'Zonal'), ('national', 'National')]

    category = models.ForeignKey(OlympiadCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    academic_year = models.CharField(max_length=9)          # "2026-27"
    level = models.CharField(max_length=10, choices=LEVELS, default='school')
    class_group = models.CharField(max_length=50)           # "Class 6-8"
    fee = models.DecimalField(max_digits=8, decimal_places=2)
    syllabus_pdf = models.FileField(upload_to='olympiad_syllabus/', blank=True, null=True)
    registration_start = models.DateField()
    registration_end = models.DateField()
    exam_date = models.DateTimeField()
    exam_duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)

class OlympiadQuestion(models.Model):
    DIFFICULTY = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]

    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('a','A'),('b','B'),('c','C'),('d','D')])
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    marks = models.PositiveIntegerField(default=1)

class OlympiadRegistration(models.Model):
    STATUS = [('registered', 'Registered'), ('admit_card_issued', 'Admit Card Issued'),
              ('appeared', 'Appeared'), ('absent', 'Absent')]

    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    institution = models.ForeignKey('institutions.Institution', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    referred_by_partner = models.ForeignKey('partners.Partner', null=True, blank=True,
                                             on_delete=models.SET_NULL)
    used_plan_credit = models.BooleanField(default=False)
    roll_number = models.CharField(max_length=20, unique=True)
    transaction = models.ForeignKey('payments.Transaction', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('olympiad', 'student')

    def clean(self):
        # Olympiad is School-only — reject College students outright
        inst = self.institution or getattr(self.student, 'managed_institution', None)
        if inst and inst.type == 'college':
            raise ValidationError(
                "Olympiad registration is only available to School students; "
                "this student's institution is registered as a College."
            )

class OlympiadAttempt(models.Model):
    registration = models.OneToOneField(OlympiadRegistration, on_delete=models.CASCADE,
                                         related_name='attempt')
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    raw_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)

class OlympiadResult(models.Model):
    GRADES = [('gold', 'Gold'), ('silver', 'Silver'), ('bronze', 'Bronze'),
              ('participation', 'Participation')]

    registration = models.OneToOneField(OlympiadRegistration, on_delete=models.CASCADE,
                                         related_name='result')
    percentile = models.DecimalField(max_digits=5, decimal_places=2)
    rank_school = models.PositiveIntegerField(null=True, blank=True)
    rank_zonal = models.PositiveIntegerField(null=True, blank=True)
    rank_national = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=15, choices=GRADES)
    certificate_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

class OlympiadScholarship(models.Model):
    TYPES = [('fee_waiver', 'Fee Waiver on Next Registration'),
             ('cash_award', 'Cash Award'), ('course_credit', 'Free Course Credit')]

    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='scholarship_bands')
    min_percentile = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentile = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    scholarship_type = models.CharField(max_length=20, choices=TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)

class OlympiadAward(models.Model):
    TYPES = [('gold_medal', 'Gold Medal'), ('silver_medal', 'Silver Medal'),
             ('bronze_medal', 'Bronze Medal'), ('certificate', 'Certificate of Excellence'),
             ('scholarship', 'Scholarship')]

    result = models.ForeignKey(OlympiadResult, on_delete=models.CASCADE, related_name='awards')
    award_type = models.CharField(max_length=20, choices=TYPES)
    scholarship = models.ForeignKey(OlympiadScholarship, null=True, blank=True,
                                     on_delete=models.SET_NULL)
    title = models.CharField(max_length=150)
    certificate_url = models.URLField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)