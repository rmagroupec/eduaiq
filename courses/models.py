"""
Complete Encrypted Quiz Models for Courses App
- All models with full encryption for quizzes
- Ready to use: Copy to courses/models.py
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken
import os
import json
import logging
from accounts.models import User 

validate_image_extension = FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])

logger = logging.getLogger(__name__)


# ============================================================================
# ENCRYPTION UTILITIES
# ============================================================================

class EncryptionManager:
    """Manages encryption/decryption for quiz data using Fernet (256-bit AES)."""
    
    ENCRYPTION_KEY = os.getenv('QUIZ_ENCRYPTION_KEY', 'generate_secure_key')
    
    @classmethod
    def get_or_create_key(cls):
        """Get encryption key from environment or generate a new one."""
        if cls.ENCRYPTION_KEY == 'generate_secure_key':
            key = Fernet.generate_key()
            logger.warning(f"No QUIZ_ENCRYPTION_KEY found. Add to .env: QUIZ_ENCRYPTION_KEY={key.decode()}")
            return key
        return cls.ENCRYPTION_KEY.encode() if isinstance(cls.ENCRYPTION_KEY, str) else cls.ENCRYPTION_KEY
    
    @classmethod
    def encrypt(cls, data: str) -> str:
        """Encrypt a string value."""
        try:
            if not data:
                return data
            key = cls.get_or_create_key()
            cipher_suite = Fernet(key)
            encrypted = cipher_suite.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError("Encryption error") from e
    
    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        try:
            if not encrypted_data:
                return encrypted_data
            key = cls.get_or_create_key()
            cipher_suite = Fernet(key)
            decrypted = cipher_suite.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token")
            raise ValueError("Decryption error - invalid or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Decryption error") from e


# ============================================================================
# COURSE CATEGORY
# ============================================================================

class CourseCategory(models.Model):
    """Course categories with metadata."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True, validators=[validate_image_extension])
    image = models.ImageField(upload_to='category_images/', null=True, blank=True, validators=[validate_image_extension])
    color_code = models.CharField(max_length=7, default='#0066cc')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    @property
    def icon_class(self):
        name_lower = self.name.lower()
        if 'book' in name_lower or 'guide' in name_lower or 'library' in name_lower:
            return 'fas fa-book'
        elif 'ai' in name_lower or 'machine' in name_lower or 'robot' in name_lower:
            return 'fas fa-robot'
        elif 'web' in name_lower or 'software' in name_lower or 'code' in name_lower or 'dev' in name_lower:
            return 'fas fa-laptop-code'
        elif 'data' in name_lower or 'analytic' in name_lower or 'chart' in name_lower or 'science' in name_lower:
            return 'fas fa-chart-line'
        elif 'business' in name_lower or 'management' in name_lower or 'communication' in name_lower:
            return 'fas fa-briefcase'
        elif 'mobile' in name_lower or 'app' in name_lower or 'android' in name_lower or 'ios' in name_lower:
            return 'fas fa-mobile-alt'
        elif 'program' in name_lower or 'basic' in name_lower:
            return 'fas fa-code'
        return 'fas fa-graduation-cap'


    @property
    def course_badge(self):
        if self.description and len(self.description) <= 30:
            return self.description
        count = self.courses.filter(status='published').count()
        if count > 0:
            return f"{count} module{'s' if count > 1 else ''}"
        return "Self-paced"



# ============================================================================
# COURSE
# ============================================================================

class Course(models.Model):
    STATUS = [('draft', 'Draft'), ('in_review', 'In Review'), ('changes_requested', 'Changes Requested'),
              ('approved', 'Approved'), ('published', 'Published'), ('archived', 'Archived')]
    DELIVERY_MODES = [('video_lecture', 'Video Lecture Based'), ('content_based', 'Content/Reading Based'),
                      ('hybrid', 'Hybrid — Video + Content')]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(CourseCategory, on_delete=models.PROTECT, related_name='courses')
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODES, default='hybrid')
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbs/', null=True, blank=True, validators=[validate_image_extension])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='authored_courses')
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_courses')
    author = models.CharField(max_length=200, default='EduAiQ Editorial Team', blank=True)
    pdf_file = models.FileField(upload_to='book_pdfs/', null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['slug']), models.Index(fields=['status', 'published_at']),
                   models.Index(fields=['category', 'status'])]

    def __str__(self):
        return self.title

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than 0")

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Catalog display helpers — no schema change, computed from
    # existing status + published_at. Not queryable directly in a
    # .filter() — use the equivalent status/published_at conditions
    # in querysets (see courses/page_views.py and course_list view).
    # ------------------------------------------------------------------
    @property
    def is_live(self):
        """Published AND publish date has already passed — shows Enroll."""
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()

    @property
    def is_coming_soon(self):
        """Approved (ready, not yet published) OR published with a future date — shows Notify Me."""
        if self.status == 'approved':
            return True
        if self.status == 'published' and self.published_at and self.published_at > timezone.now():
            return True
        return False


# ============================================================================
# COURSE MODULE
# ============================================================================

class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course', 'order')
        ordering = ['course', 'order']
        indexes = [models.Index(fields=['course', 'is_published'])]

    def __str__(self):
        return f"{self.course.title} - Module {self.order}"


# ============================================================================
# LESSON
# ============================================================================

class Lesson(models.Model):
    CONTENT_TYPES = [('video', 'Video'), ('text', 'Text/Article'), ('pdf', 'PDF'),
                     ('quiz', 'Quiz'), ('live', 'Live Class'), ('assignment', 'Assignment')]

    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_url = models.URLField(blank=True)
    content_file = models.FileField(upload_to='lesson_files/', null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField()
    is_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('module', 'order')
        ordering = ['module', 'order']
        indexes = [models.Index(fields=['module', 'is_published']), models.Index(fields=['content_type'])]

    def __str__(self):
        return f"{self.module.title} - Lesson {self.order}"

    def clean(self):
        if self.content_type in ['video', 'live']:
            if not self.content_url and not self.content_file:
                raise ValidationError(f"'{self.get_content_type_display()}' lessons require either content_url or content_file")
        if self.content_type == 'pdf':
            if not self.content_url and not self.content_file:
                raise ValidationError(f"'{self.get_content_type_display()}' lessons require either content_url or content_file")
        if self.content_type == 'assignment':
            if not self.content_url and not self.content_file and not self.description:
                raise ValidationError("Assignment lessons require task instructions in description, content_url, or content_file")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ============================================================================
# ENCRYPTED QUIZ
# ============================================================================

class Quiz(models.Model):
    """Quiz with encryption support for sensitive data."""
    
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz', limit_choices_to={'content_type': 'quiz'})
    passing_score_pct = models.PositiveIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(100)])
    time_limit_minutes = models.PositiveIntegerField(default=15, validators=[MinValueValidator(1)])
    shuffle_questions = models.BooleanField(default=True, help_text="Randomize question order")
    show_correct_answers = models.BooleanField(default=True, help_text="Show after completion")
    attempts_allowed = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    
    quiz_key = models.CharField(max_length=255, unique=True, help_text="Unique encrypted key for quiz")
    requires_authentication = models.BooleanField(default=True, help_text="Require user authentication")
    enable_anti_cheating = models.BooleanField(default=True, help_text="Enable anti-cheating measures")
    randomize_options = models.BooleanField(default=True, help_text="Randomize answer options")
    shuffle_per_student = models.BooleanField(default=True, help_text="Different randomization per student")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        indexes = [models.Index(fields=['quiz_key']), models.Index(fields=['is_active'])]

    def __str__(self):
        return f"Quiz: {self.lesson.title}"

    def save(self, *args, **kwargs):
        if not self.quiz_key:
            self.quiz_key = EncryptionManager.encrypt(f"{self.lesson.id}-{timezone.now().isoformat()}")
        super().save(*args, **kwargs)

    @property
    def total_marks(self):
        return self.questions.filter(is_active=True).aggregate(total=models.Sum('marks'))['total'] or 0

    def is_user_allowed(self, user) -> bool:
        if not self.is_active:
            return False
        if self.lesson and not self.lesson.is_published:
            if not (user and (user.is_superuser or getattr(user, 'is_staff', False))):
                return False
        if self.requires_authentication and (not user or not user.is_authenticated):
            return False
        if user.is_superuser or getattr(user, 'role', '') in ['admin', 'institution', 'teacher'] or getattr(user, 'is_staff', False):
            return True
        attempt_count = QuizAttempt.objects.filter(quiz=self, student=user).count()
        max_attempts = max(self.attempts_allowed, 100)
        return attempt_count < max_attempts


# ============================================================================
# ENCRYPTED QUIZ QUESTION
# ============================================================================

class QuizQuestion(models.Model):
    """Quiz questions with encrypted content."""
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    _question_text_encrypted = models.TextField(default='', help_text="Encrypted question")
    _option_a_encrypted = models.CharField(max_length=500, default='', help_text="Encrypted option A")
    _option_b_encrypted = models.CharField(max_length=500, default='', help_text="Encrypted option B")
    _option_c_encrypted = models.CharField(max_length=500, default='', help_text="Encrypted option C")
    _option_d_encrypted = models.CharField(max_length=500, default='', help_text="Encrypted option D")
    _correct_option_encrypted = models.CharField(max_length=100, default='', help_text="Encrypted correct answer")
    _explanation_encrypted = models.TextField(blank=True, default='', help_text="Encrypted explanation")

    marks = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    difficulty = models.CharField(max_length=10, choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
        ordering = ['quiz', 'order']
        indexes = [models.Index(fields=['quiz'])]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50] if self.question_text else '[Encrypted]'}"

    @property
    def question_text(self):
        try:
            return EncryptionManager.decrypt(self._question_text_encrypted) if self._question_text_encrypted else ""
        except Exception as e:
            logger.error(f"Failed to decrypt question: {e}")
            return "[Decryption Error]"
    
    @question_text.setter
    def question_text(self, value):
        if value:
            self._question_text_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def option_a(self):
        try:
            return EncryptionManager.decrypt(self._option_a_encrypted) if self._option_a_encrypted else ""
        except Exception as e:
            logger.error(f"Failed to decrypt option A: {e}")
            return "[Decryption Error]"
    
    @option_a.setter
    def option_a(self, value):
        if value:
            self._option_a_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def option_b(self):
        try:
            return EncryptionManager.decrypt(self._option_b_encrypted) if self._option_b_encrypted else ""
        except Exception as e:
            logger.error(f"Failed to decrypt option B: {e}")
            return "[Decryption Error]"
    
    @option_b.setter
    def option_b(self, value):
        if value:
            self._option_b_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def option_c(self):
        try:
            return EncryptionManager.decrypt(self._option_c_encrypted) if self._option_c_encrypted else ""
        except Exception as e:
            logger.error(f"Failed to decrypt option C: {e}")
            return "[Decryption Error]"
    
    @option_c.setter
    def option_c(self, value):
        if value:
            self._option_c_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def option_d(self):
        try:
            return EncryptionManager.decrypt(self._option_d_encrypted) if self._option_d_encrypted else ""
        except Exception as e:
            logger.error(f"Failed to decrypt option D: {e}")
            return "[Decryption Error]"
    
    @option_d.setter
    def option_d(self, value):
        if value:
            self._option_d_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def correct_option(self):
        try:
            return EncryptionManager.decrypt(self._correct_option_encrypted) if self._correct_option_encrypted else None
        except Exception as e:
            logger.error(f"Failed to decrypt correct option: {e}")
            return None
    
    @correct_option.setter
    def correct_option(self, value):
        if value:
            self._correct_option_encrypted = EncryptionManager.encrypt(value)
    
    @property
    def explanation(self):
        if self._explanation_encrypted:
            try:
                return EncryptionManager.decrypt(self._explanation_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt explanation: {e}")
                return "[Decryption Error]"
        return None
    
    @explanation.setter
    def explanation(self, value):
        if value:
            self._explanation_encrypted = EncryptionManager.encrypt(value)
        else:
            self._explanation_encrypted = None
    
    def get_options(self):
        """Get all options as dictionary."""
        return {'a': self.option_a, 'b': self.option_b, 'c': self.option_c, 'd': self.option_d}
    
    def get_shuffled_options(self):
        """Get shuffled options for student."""
        import random
        if self.quiz.randomize_options:
            options = list(self.get_options().items())
            random.shuffle(options)
            return dict(options)
        return self.get_options()


# ============================================================================
# ENCRYPTED QUIZ ATTEMPT
# ============================================================================

class QuizAttempt(models.Model):
    """Quiz attempt with encrypted student responses."""
    
    STATUS_CHOICES = [('in_progress', 'In Progress'), ('submitted', 'Submitted'), 
                      ('graded', 'Graded'), ('flagged', 'Flagged for Review')]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quiz_attempts', limit_choices_to={'role': 'student'})
    
    session_token = models.CharField(max_length=255, unique=True, help_text="Unique session identifier (encrypted)")
    session_ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address during attempt")
    _student_responses_encrypted = models.TextField(blank=True, default='', help_text="Encrypted student responses (JSON)")    
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_marks = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    cheating_detected = models.BooleanField(default=False, help_text="Potential cheating detected")
    cheating_details = models.TextField(blank=True, help_text="Details of cheating detection")

    class Meta:
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        unique_together = ('quiz', 'student', 'attempt_number')
        ordering = ['-started_at']
        indexes = [models.Index(fields=['student', 'started_at']), models.Index(fields=['quiz', 'passed'])]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.lesson.title} (Attempt {self.attempt_number})"

    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = EncryptionManager.encrypt(f"{self.student.id}-{self.quiz.id}-{timezone.now().isoformat()}")
        self.passed = self.score_pct >= self.quiz.passing_score_pct
        super().save(*args, **kwargs)

    @property
    def student_responses(self):
        """Get decrypted student responses."""
        if self._student_responses_encrypted:
            try:
                decrypted = EncryptionManager.decrypt(self._student_responses_encrypted)
                return json.loads(decrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt student responses: {e}")
                return {}
        return {}
    
    @student_responses.setter
    def student_responses(self, value):
        """Set and encrypt student responses."""
        if value:
            json_str = json.dumps(value)
            self._student_responses_encrypted = EncryptionManager.encrypt(json_str)
        else:
            self._student_responses_encrypted = None

    def add_response(self, question_id: int, selected_option: str):
        """Add or update a student's response."""
        responses = self.student_responses
        responses[str(question_id)] = selected_option
        self.student_responses = responses

    def get_response(self, question_id: int) -> str:
        """Get student's response for a question."""
        responses = self.student_responses
        return responses.get(str(question_id), None)

    def calculate_score(self):
        """Calculate score based on responses."""
        responses = self.student_responses
        total_marks = 0
        obtained_marks = 0
        
        for question in self.quiz.questions.filter(is_active=True):
            total_marks += question.marks
            student_answer = responses.get(str(question.id))
            if student_answer == question.correct_option:
                obtained_marks += question.marks
        
        if total_marks > 0:
            self.score_marks = obtained_marks
            self.score_pct = (obtained_marks / total_marks) * 100
        self.save()


# ============================================================================
# QUIZ ACCESS LOG (AUDIT TRAIL)
# ============================================================================

class QuizAccessLog(models.Model):
    """Audit log for quiz access and modifications."""
    
    ACTION_CHOICES = [('accessed', 'Quiz Accessed'), ('started', 'Quiz Started'), 
                      ('submitted', 'Quiz Submitted'), ('viewed', 'Quiz Viewed in Admin'),
                      ('modified', 'Quiz Modified'), ('published', 'Quiz Published')]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='quiz_access_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz Access Log'
        verbose_name_plural = 'Quiz Access Logs'
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['quiz', 'timestamp']), models.Index(fields=['user', 'timestamp'])]

    def __str__(self):
        return f"{self.action} - {self.user.username if self.user else 'Unknown'} on {self.timestamp}"


# ============================================================================
# ENROLLMENT
# ============================================================================
class Enrollment(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    progress_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    covered_by_plan = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'course')
    
    def save(self, *args, **kwargs):
        # Remove queryset validation if it exists
        super().save(*args, **kwargs)


# ============================================================================
# ASSIGNMENT SUBMISSION
# ============================================================================
class AssignmentSubmission(models.Model):
    """Tracks student submissions, skip status, and grades for assignment lessons."""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('skipped', 'Skipped for now'),
    ]

    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions', 
        limit_choices_to={'content_type': 'assignment'}
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions'
    )
    submission_text = models.TextField(blank=True, default='', help_text="Student's typed response or notes")
    submission_file = models.FileField(upload_to='assignment_submissions/', null=True, blank=True, help_text="Uploaded submission file")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    grade = models.CharField(max_length=20, blank=True, default='')
    feedback = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assignment Submission'
        verbose_name_plural = 'Assignment Submissions'
        unique_together = ('lesson', 'student')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} ({self.status})"