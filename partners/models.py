from django.db import models

class PartnerCategory(models.Model):
    """District / City / School / Campus Ambassador / Sales / Franchise / etc."""
    name = models.CharField(max_length=50)
    investment_min = models.DecimalField(max_digits=10, decimal_places=2)
    investment_max = models.DecimalField(max_digits=10, decimal_places=2)
    commission_product_pct = models.DecimalField(max_digits=5, decimal_places=2)   # course/plan sales
    commission_olympiad_pct = models.DecimalField(max_digits=5, decimal_places=2)
    commission_services_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

class Partner(models.Model):
    STATUS_CHOICES = [('pending', 'Pending Verification'), ('active', 'Active'),
                       ('suspended', 'Suspended'), ('terminated', 'Terminated')]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    category = models.ForeignKey(PartnerCategory, on_delete=models.PROTECT)
    referral_code = models.CharField(max_length=20, unique=True)   # e.g. EDU-SCH-1042
    joining_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    kyc_document = models.FileField(upload_to='partner_kyc/', null=True, blank=True)
    bank_account_no = models.CharField(max_length=30, blank=True)
    bank_ifsc = models.CharField(max_length=15, blank=True)
    territory = models.CharField(max_length=100, blank=True)
    onboarded_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL,
                                     related_name='approved_partners')

class PartnerAgreement(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='agreements')
    agreement_file = models.FileField(upload_to='agreements/')
    signed_at = models.DateTimeField(null=True, blank=True)
    valid_till = models.DateField(null=True, blank=True)