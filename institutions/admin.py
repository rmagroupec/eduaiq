from django.contrib import admin
from .models import Institution, Student, Batch

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'city', 'state', 'status', 'created_at')
    list_filter = ('type', 'status', 'state')
    search_fields = ('name', 'city', 'state')
    filter_horizontal = ('allowed_categories', 'allowed_courses')

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'code', 'target_exam', 'is_active', 'created_at')
    list_filter = ('institution', 'target_exam', 'is_active')
    search_fields = ('name', 'code', 'target_exam', 'institution__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'batch', 'admission_no', 'class_grade', 'status')
    list_filter = ('status', 'class_grade', 'institution', 'batch')
    search_fields = ('admission_no', 'roll_number', 'user__username', 'user__email')

