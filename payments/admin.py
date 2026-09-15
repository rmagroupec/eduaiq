from django.contrib import admin

# Register your models here.

from .models import Invoice, FeeCollection

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'total_amount', 'status', 'due_date')
    list_filter = ('status',)

@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'amount_collected', 'created_at')

