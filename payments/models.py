from django.db import models

class Transaction(models.Model):
    SOURCE_CHOICES = [('enrollment', 'Course Enrollment'), ('olympiad', 'Olympiad Registration'),
                       ('subscription', 'Institution Subscription'), ('partner_fee', 'Partner Joining Fee')]
    STATUS = [('success', 'Success'), ('failed', 'Failed'), ('refunded', 'Refunded')]

    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    reference_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    gateway_txn_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

class Commission(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('paid', 'Paid'), ('held', 'Held')]

    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, related_name='commissions')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    commission_pct = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Payout(models.Model):
    STATUS = [('processing', 'Processing'), ('paid', 'Paid'), ('failed', 'Failed')]

    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, related_name='payouts')
    period_start = models.DateField()
    period_end = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS)
    utr_number = models.CharField(max_length=50, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)