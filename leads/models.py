"""
CRM Models — Sales pipeline for EduAiQ.

Three "record" entry points feed the CRM:
  - Lead            : B2B — a prospective School/College/Coaching Institute.
  - StudentInquiry   : B2C — a prospective student/parent admission enquiry.
  - Opportunity      : a quantified deal (amount, probability, stage) hanging
                        off either a Lead or a StudentInquiry, used for
                        revenue forecasting.
Supporting records:
  - Activity     : follow-up / interaction log (call, email, meeting, note)
                    attached to exactly one of Lead / StudentInquiry / Opportunity.
  - SalesTarget  : revenue target per salesperson or Partner for a period,
                    with achievement computed from Won Opportunities.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

PHONE_VALIDATOR = RegexValidator(regex=r'^\+?1?\d{9,15}$', message='Enter a valid phone number.')

SOURCE_CHOICES = [
    ('website', 'Website Enquiry'),
    ('referral', 'Partner Referral'),
    ('cold_call', 'Cold Call'),
    ('walk_in', 'Walk-in'),
    ('social_media', 'Social Media'),
    ('event', 'Event / Exhibition'),
    ('other', 'Other'),
]

PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]


class Lead(models.Model):
    """
    Sales CRM — Institution / Franchise lead (B2B). A prospective
    School/College/Coaching Institute considering EduAiQ.
    """
    STAGE_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('demo', 'Demo Scheduled'),
        ('negotiation', 'Negotiation'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]
    INSTITUTION_TYPE_CHOICES = [
        ('school', 'School'), ('college', 'College'),
        ('coaching', 'Coaching Institute'), ('other', 'Other'),
    ]

    # Ownership / attribution
    partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='leads',
                                 help_text='Set if this lead was referred in by a franchise Partner.')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='owned_leads',
                               help_text='In-house sales rep responsible for working this lead.')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')

    # Contact details
    lead_name = models.CharField(max_length=150)
    institution_name = models.CharField(max_length=255, blank=True)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, validators=[PHONE_VALIDATOR])
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    # Pipeline
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    expected_seats = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text='Estimated no. of students, for revenue projection.')
    interested_plan = models.ForeignKey('plans.Plan', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='interested_leads')
    next_follow_up_date = models.DateField(null=True, blank=True)
    lost_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Conversion
    converted_institution = models.ForeignKey('institutions.Institution', null=True, blank=True,
                                               on_delete=models.SET_NULL, related_name='source_leads')
    converted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['owner']),
            models.Index(fields=['next_follow_up_date']),
        ]

    def __str__(self):
        return f"{self.lead_name} ({self.institution_name or 'Individual'})"

    @property
    def is_open(self):
        return self.stage not in ('converted', 'lost')


class StudentInquiry(models.Model):
    """
    Sales CRM — Student admission / course enquiry (B2C). A prospective
    student/parent interested in a course, Olympiad, or admission, tracked
    independently of any formal Institution deal.
    """
    STAGE_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('trial', 'Trial / Demo Class'),
        ('admission_offered', 'Admission Offered'),
        ('enrolled', 'Enrolled'),
        ('lost', 'Lost'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='owned_student_inquiries')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')

    # Contact details
    student_name = models.CharField(max_length=150)
    guardian_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, validators=[PHONE_VALIDATOR])
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    class_grade_interested = models.CharField(max_length=20, blank=True)

    # What they're interested in
    interested_institution = models.ForeignKey('institutions.Institution', null=True, blank=True,
                                                on_delete=models.SET_NULL, related_name='student_inquiries')
    interested_course = models.ForeignKey('courses.Course', null=True, blank=True,
                                           on_delete=models.SET_NULL, related_name='inquiries')
    interested_in_olympiad = models.BooleanField(default=False)

    # Pipeline
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    next_follow_up_date = models.DateField(null=True, blank=True)
    lost_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Conversion
    converted_student = models.ForeignKey('institutions.Student', null=True, blank=True,
                                           on_delete=models.SET_NULL, related_name='source_inquiry')
    converted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='created_student_inquiries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Inquiry'
        verbose_name_plural = 'Student Inquiries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['owner']),
            models.Index(fields=['next_follow_up_date']),
        ]

    def __str__(self):
        return f"{self.student_name} — {self.class_grade_interested or 'General Enquiry'}"

    @property
    def is_open(self):
        return self.stage not in ('enrolled', 'lost')


class Opportunity(models.Model):
    """
    Sales CRM — a quantified deal in the pipeline, for revenue forecasting.
    Hangs off exactly one of: a Lead (institution/B2B deal) or a
    StudentInquiry (individual/B2C deal).
    """
    STAGE_CHOICES = [
        ('prospecting', 'Prospecting'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal Sent'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='opportunities')
    student_inquiry = models.ForeignKey(StudentInquiry, on_delete=models.CASCADE, null=True, blank=True,
                                         related_name='opportunities')

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='owned_opportunities')
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text='Projected deal value (INR).')
    probability_pct = models.PositiveIntegerField(default=20, help_text='0-100. Used for weighted forecasting.')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='prospecting')
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    plan = models.ForeignKey('plans.Plan', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='opportunities')
    linked_transaction = models.ForeignKey('payments.Transaction', on_delete=models.SET_NULL, null=True, blank=True,
                                            help_text='Set once payment is actually collected for a Won deal.')

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['owner']),
            models.Index(fields=['expected_close_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(probability_pct__gte=0) & models.Q(probability_pct__lte=100),
                name='opportunity_probability_0_100',
            ),
        ]

    def __str__(self):
        return f"{self.name} — Rs.{self.amount}"

    @property
    def weighted_amount(self):
        return (self.amount * self.probability_pct) / 100

    def clean(self):
        if not self.lead_id and not self.student_inquiry_id:
            raise ValidationError('An Opportunity must be linked to either a Lead or a Student Inquiry.')
        if self.lead_id and self.student_inquiry_id:
            raise ValidationError('An Opportunity cannot be linked to both a Lead and a Student Inquiry.')


class Activity(models.Model):
    """
    Sales CRM — follow-up / interaction log. Attaches to exactly one of:
    Lead, StudentInquiry, or Opportunity.
    """
    TYPE_CHOICES = [
        ('call', 'Call'), ('email', 'Email'), ('whatsapp', 'WhatsApp'),
        ('meeting', 'Meeting'), ('demo', 'Demo'), ('note', 'Note'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    student_inquiry = models.ForeignKey(StudentInquiry, on_delete=models.CASCADE, null=True, blank=True,
                                         related_name='activities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='activities')

    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='note')
    notes = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True,
                                     help_text='Scheduled follow-up time. Leave blank for a logged/completed activity.')
    is_completed = models.BooleanField(default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='logged_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['due_date']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.created_at:%Y-%m-%d}"

    def clean(self):
        linked = [bool(self.lead_id), bool(self.student_inquiry_id), bool(self.opportunity_id)]
        if sum(linked) != 1:
            raise ValidationError('An Activity must be linked to exactly one of: Lead, Student Inquiry, or Opportunity.')


class SalesTarget(models.Model):
    """
    Sales CRM — revenue target per salesperson or Partner for a period.
    Achievement is computed live from Won Opportunities closed in-period.
    """
    PERIOD_CHOICES = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='sales_targets')
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='sales_targets')
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    period_start = models.DateField()
    period_end = models.DateField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(owner__isnull=False) | models.Q(partner__isnull=False),
                name='sales_target_needs_owner_or_partner',
            ),
        ]

    def __str__(self):
        if self.owner_id:
            who = self.owner.get_full_name() or self.owner.username
        elif self.partner_id:
            who = self.partner.user.get_full_name() or self.partner.referral_code
        else:
            who = 'Unassigned'
        return f"{who} target {self.period_start} to {self.period_end}: Rs.{self.target_amount}"

    def clean(self):
        if not self.owner_id and not self.partner_id:
            raise ValidationError('A Sales Target must be assigned to either a sales rep (owner) or a Partner.')

    @property
    def achieved_amount(self):
        qs = Opportunity.objects.filter(
            stage='won',
            actual_close_date__gte=self.period_start,
            actual_close_date__lte=self.period_end,
        )
        if self.owner_id:
            qs = qs.filter(owner=self.owner)
        elif self.partner_id:
            qs = qs.filter(lead__partner=self.partner)
        return qs.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def achievement_pct(self):
        if not self.target_amount:
            return 0
        return round((float(self.achieved_amount) / float(self.target_amount)) * 100, 1)