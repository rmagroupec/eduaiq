from django.contrib import admin
from .models import (
    OlympiadCategory,
    Olympiad,
    OlympiadQuiz,
    OlympiadQuestion,
    OlympiadRegistration,
    OlympiadAttempt,
    OlympiadResult,
    OlympiadScholarship,
    OlympiadAward,
)

class OlympiadQuizInline(admin.TabularInline):
    model = OlympiadQuiz
    extra = 1

class OlympiadQuestionInline(admin.StackedInline):
    model = OlympiadQuestion
    extra = 1

@admin.register(OlympiadCategory)
class OlympiadCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Olympiad)
class OlympiadAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'academic_year', 'level', 'fee', 'result_display_mode', 'result_declaration_date', 'is_active']
    list_filter = ['category', 'level', 'result_display_mode', 'is_active']
    search_fields = ['name', 'class_group']
    inlines = [OlympiadQuizInline, OlympiadQuestionInline]

@admin.register(OlympiadRegistration)
class OlympiadRegistrationAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'student', 'olympiad', 'status', 'registered_at']
    list_filter = ['status', 'olympiad']
    search_fields = ['roll_number', 'student__username', 'student__email']

@admin.register(OlympiadAttempt)
class OlympiadAttemptAdmin(admin.ModelAdmin):
    list_display = ['registration', 'started_at', 'submitted_at', 'raw_score', 'score_pct', 'passed']
    list_filter = ['passed']

@admin.register(OlympiadResult)
class OlympiadResultAdmin(admin.ModelAdmin):
    list_display = ['registration', 'percentile', 'grade', 'published_at']
    list_filter = ['grade']

admin.site.register(OlympiadQuiz)
admin.site.register(OlympiadQuestion)
admin.site.register(OlympiadScholarship)
admin.site.register(OlympiadAward)

