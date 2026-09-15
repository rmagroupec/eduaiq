from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Profile, Department, Designation, EmployeeProfile, Attendance, WFHRequest



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'status', 'is_staff', 'is_superuser')
    list_filter = ('role', 'status', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('EduAiQ Extra Details', {'fields': ('phone', 'role', 'status', 'school_name', 'gender')}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'created_at')
    list_filter = ('department',)
    search_fields = ('title',)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'designation', 'onboarding_status', 'joining_date')
    list_filter = ('department', 'onboarding_status')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status', 'academic_year', 'check_in', 'check_out')
    list_filter = ('status', 'academic_year', 'date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'remarks')


@admin.register(WFHRequest)
class WFHRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'status', 'applied_at', 'approved_by')
    list_filter = ('status', 'applied_at', 'start_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'reason')
