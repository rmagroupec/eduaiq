from django.db import models
from django.utils.translation import gettext_lazy as _


class ExpenseHead(models.Model):
    """
    Expense category / head (e.g., Rent, Salaries, Electricity, Internet, Maintenance, Marketing)
    """
    name = models.CharField(_('Expense Head Name'), max_length=150, unique=True)
    code = models.CharField(_('Expense Code'), max_length=30, unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Expense Head')
        verbose_name_plural = _('Expense Heads')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Expense(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending Approval')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        PAID = 'paid', _('Paid')

    class PaymentModeChoices(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer / NEFT / RTGS')
        UPI = 'upi', _('UPI / PhonePe / GooglePay')
        CARD = 'card', _('Corporate / Credit Card')
        CHEQUE = 'cheque', _('Cheque')

    expense_head = models.ForeignKey(ExpenseHead, on_delete=models.PROTECT, related_name='expenses')
    title = models.CharField(_('Expense Title'), max_length=255)
    amount = models.DecimalField(_('Amount (₹)'), max_digits=12, decimal_places=2)
    expense_date = models.DateField(_('Expense Date'))
    
    paid_to = models.CharField(_('Paid To / Payee'), max_length=200, help_text=_('Vendor, Employee or Company Name'))
    payment_mode = models.CharField(_('Payment Mode'), max_length=30, choices=PaymentModeChoices.choices, default=PaymentModeChoices.CASH)
    reference_no = models.CharField(_('Reference / Invoice / Txn No.'), max_length=100, blank=True)
    
    receipt_attachment = models.FileField(_('Receipt / Invoice File'), upload_to='expense_receipts/%Y/%m/', null=True, blank=True)
    status = models.CharField(_('Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='submitted_expenses')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True)
    notes = models.TextField(_('Additional Notes'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.get_status_display()})"
