from django.contrib import admin

from .models import Activity, Lead, Opportunity, SalesTarget, StudentInquiry


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('lead_name', 'institution_name', 'stage', 'priority', 'owner', 'partner',
                     'phone', 'next_follow_up_date', 'created_at')
    list_filter = ('stage', 'priority', 'source', 'institution_type')
    search_fields = ('lead_name', 'institution_name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at', 'converted_at')
    date_hierarchy = 'created_at'


@admin.register(StudentInquiry)
class StudentInquiryAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'guardian_name', 'stage', 'priority', 'owner',
                     'phone', 'class_grade_interested', 'next_follow_up_date', 'created_at')
    list_filter = ('stage', 'priority', 'source', 'interested_in_olympiad')
    search_fields = ('student_name', 'guardian_name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at', 'converted_at')
    date_hierarchy = 'created_at'


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage', 'amount', 'probability_pct', 'weighted_amount',
                     'owner', 'expected_close_date', 'actual_close_date')
    list_filter = ('stage',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'expected_close_date'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'lead', 'student_inquiry', 'opportunity',
                     'is_completed', 'due_date', 'created_by', 'created_at')
    list_filter = ('activity_type', 'is_completed')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'period_type', 'period_start', 'period_end',
                     'target_amount', 'achieved_amount', 'achievement_pct')
    list_filter = ('period_type',)
    readonly_fields = ('created_at',)
