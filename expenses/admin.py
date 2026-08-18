from django.contrib import admin
from .models import ExpenseHead, Expense

@admin.register(ExpenseHead)
class ExpenseHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'expense_head', 'amount', 'expense_date', 'status', 'paid_to', 'payment_mode')
    list_filter = ('status', 'payment_mode', 'expense_head', 'expense_date')
    search_fields = ('title', 'paid_to', 'reference_no')
