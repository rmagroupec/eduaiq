from django.db import models

class Plan(models.Model):
    BILLING = [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')]

    name = models.CharField(max_length=100)
    institution_type = models.CharField(max_length=10,
        choices=[('school', 'School'), ('college', 'College'), ('both', 'Both')], default='school')
    billing_cycle = models.CharField(max_length=10, choices=BILLING, default='annual')
    price_per_student = models.DecimalField(max_digits=8, decimal_places=2)
    min_seats = models.PositiveIntegerField(default=1)
    max_seats = models.PositiveIntegerField(null=True, blank=True)   # null = unlimited
    olympiad_credits_per_student = models.PositiveIntegerField(default=0)  # 0 = not included
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PlanCourseAccess(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='course_access')
    course_category = models.CharField(max_length=100, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)

class InstitutionSubscription(models.Model):
    STATUS = [('pending_payment', 'Pending Payment'), ('active', 'Active'),
              ('expired', 'Expired'), ('cancelled', 'Cancelled')]

    institution = models.ForeignKey('institutions.Institution', on_delete=models.CASCADE,
                                     related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    seats_purchased = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending_payment')
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution'], condition=models.Q(status='active'),
                                     name='one_active_subscription_per_institution')
        ]

class SubscriptionInvoice(models.Model):
    STATUS = [('unpaid', 'Unpaid'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('refunded', 'Refunded')]

    subscription = models.ForeignKey(InstitutionSubscription, on_delete=models.CASCADE,
                                      related_name='invoices')
    invoice_number = models.CharField(max_length=30, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='unpaid')
    transaction = models.ForeignKey('payments.Transaction', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    paid_at = models.DateTimeField(null=True, blank=True)