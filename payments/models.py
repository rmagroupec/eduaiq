from django.db import models

class Transaction(models.Model):
    SOURCE_CHOICES = [('enrollment', 'Course Enrollment'), ('olympiad', 'Olympiad Registration'),
                       ('subscription', 'Institution Subscription'), ('partner_fee', 'Partner Joining Fee'),
                       ('general', 'General / Admin Record')]
    STATUS = [('success', 'Success'), ('failed', 'Failed'), ('refunded', 'Refunded')]

    invoice_no = models.CharField(max_length=50, blank=True, null=True)
    transaction_type = models.CharField(max_length=100, default='General')
    payment_type = models.CharField(max_length=50, default='Cash')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='general')
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    gateway_txn_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='success')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Txn #{self.invoice_no or self.id} - ₹{self.amount}"

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


class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('subscription', 'Institution Subscription'),
        ('student_fee', 'Student Tuition Fee'),
        ('custom', 'Custom Invoice'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    institution = models.ForeignKey('institutions.Institution', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    student = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='student_fee')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_status_display()})"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} x {self.quantity}"


class FeeCollection(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI / QR Code'),
        ('card', 'Credit / Debit Card'),
        ('bank_transfer', 'Bank Transfer / NEFT'),
        ('cheque', 'Cheque'),
        ('gateway', 'Online Payment Gateway'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='fee_collections')
    student = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='fee_payments')
    student_name = models.CharField(max_length=150, blank=True, null=True)
    admission_no = models.CharField(max_length=50, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    institution = models.ForeignKey('institutions.Institution', on_delete=models.SET_NULL, null=True, blank=True)
    
    amount_collected = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cash')
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    collected_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_fees')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.student_name or (self.student.get_full_name() if self.student else "Student")
        return f"Fee ₹{self.amount_collected} by {name}"
