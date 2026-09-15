from django.core.exceptions import ValidationError
from django.db import models

class OlympiadCategory(models.Model):
    name = models.CharField(max_length=100)   # Science, Maths, AI, Coding, Robotics, GK, Olympiad Entrance

    def __str__(self):
        return self.name

class Olympiad(models.Model):
    LEVELS = [('school', 'School Level'), ('zonal', 'Zonal'), ('national', 'National')]
    RESULT_MODES = [
        ('immediate', 'Instant Result'),
        ('after_2_hours', 'After 2 Hours of Submission'),
        ('next_day', 'Next Day (Following Day)'),
        ('scheduled', 'Scheduled Specific Date/Time'),
        ('manual', 'Manual Release'),
    ]

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
    result_display_mode = models.CharField(max_length=20, choices=RESULT_MODES, default='immediate')
    result_timing_mode = models.CharField(max_length=20, choices=RESULT_MODES, default='immediate')
    result_declaration_date = models.DateTimeField(null=True, blank=True)
    result_publish_at = models.DateTimeField(null=True, blank=True)
    is_result_published = models.BooleanField(default=False)
    next_day_release_time = models.TimeField(default='09:00:00', help_text="Release time for 'Next Day' result mode")
    quizzes = models.ManyToManyField('courses.Quiz', through='OlympiadQuiz', blank=True, related_name='olympiad_exams')
    is_entrance_exam = models.BooleanField(default=True, help_text="Designates if this exam is an Olympiad Entrance Exam")
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.name

class OlympiadQuiz(models.Model):
    """Bridge model to assign one or more quizzes to an Olympiad Entrance Exam."""
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='olympiad_quizzes')
    quiz = models.ForeignKey('courses.Quiz', on_delete=models.CASCADE, related_name='olympiad_assignments')
    section_name = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Section A - Logical Reasoning")
    order = models.PositiveIntegerField(default=1)
    weightage_marks = models.PositiveIntegerField(default=0, help_text="Custom section weightage marks if any")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Olympiad Assigned Quiz'
        verbose_name_plural = 'Olympiad Assigned Quizzes'

    def __str__(self):
        return f"{self.olympiad.name} - {self.quiz.lesson.title} ({self.section_name or 'Default Section'})"

class OlympiadQuestion(models.Model):
    DIFFICULTY = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    QUESTION_TYPES = [
        ('mcq', 'Single Choice MCQ'),
        ('true_false', 'True / False'),
        ('multi_select', 'Multiple Correct Options'),
        ('numerical', 'Numerical Answer'),
    ]

    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255, blank=True, default='')
    option_b = models.CharField(max_length=255, blank=True, default='')
    option_c = models.CharField(max_length=255, blank=True, default='')
    option_d = models.CharField(max_length=255, blank=True, default='')
    correct_option = models.CharField(max_length=255, help_text="Answer option key: 'a', 'true', 'a,c', or numerical value")
    explanation = models.TextField(blank=True, default='')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:50]}"

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

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} - {self.olympiad.name} ({self.roll_number})"

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
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    responses_json = models.TextField(blank=True, default='{}')

    def __str__(self):
        return f"Attempt by {self.registration.student.username} for {self.registration.olympiad.name}"

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

    def __str__(self):
        return f"Result: {self.registration.student.username} - Grade: {self.grade}"

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