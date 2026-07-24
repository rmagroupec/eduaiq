from django.core.exceptions import ValidationError
from django.db import models

class Course(models.Model):
    STATUS = [('draft', 'Draft'), ('in_review', 'In Review'),
              ('changes_requested', 'Changes Requested'),
              ('approved', 'Approved'), ('published', 'Published'), ('archived', 'Archived')]
    DELIVERY_MODES = [('video_lecture', 'Video Lecture Based'),
                       ('content_based', 'Content/Reading Based'),
                       ('hybrid', 'Hybrid \u2014 Video + Content')]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=100)          # AI&Robotics, Coding, Foundation...
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODES, default='hybrid')
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbs/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)   # a-la-carte price (College path)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                    related_name='authored_courses')
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name='reviewed_courses')
    version = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = ('course', 'order')

class Lesson(models.Model):
    CONTENT_TYPES = [('video', 'Video'), ('pdf', 'PDF'), ('quiz', 'Quiz'), ('live', 'Live Class')]

    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_url = models.URLField(blank=True)             # S3 URL or live meeting link
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField()
    is_preview = models.BooleanField(default=False)       # visible before purchase

    class Meta:
        unique_together = ('module', 'order')

    def clean(self):
        if self.content_type == 'quiz' and not hasattr(self, 'quiz'):
            raise ValidationError("A 'quiz' Lesson must have a related Quiz object.")

class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    passing_score_pct = models.PositiveIntegerField(default=40)
    time_limit_minutes = models.PositiveIntegerField(default=15)

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('a','A'),('b','B'),('c','C'),('d','D')])
    marks = models.PositiveIntegerField(default=1)

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

class Enrollment(models.Model):
    """The College a-la-carte path AND School plan-covered access both create this."""
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                 limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    institution = models.ForeignKey('institutions.Institution', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    referred_by_partner = models.ForeignKey('partners.Partner', null=True, blank=True,
                                             on_delete=models.SET_NULL)
    covered_by_plan = models.BooleanField(default=False)   # True = School Plan access, no separate charge
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')