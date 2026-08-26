"""
Account URLs Configuration
Routes for authentication, profile, and user management (JSON API only)
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ========================================================================
    # AUTHENTICATION URLS
    # ========================================================================
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    # ========================================================================
    # PASSWORD MANAGEMENT URLS
    # ========================================================================
    path('forgot-password/', views.forgot_password_api, name='forgot-password'),
    path('change-password/', views.change_password, name='change-password'),
    path('delete-account/', views.delete_account, name='delete-account'),


    # ========================================================================
    # USER PROFILE URLS
    # ========================================================================
    path('profile/', views.user_profile, name='profile'),
    path('profile/edit/', views.user_edit, name='profile-edit'),
    path('profile/detail/', views.profile_detail, name='profile-detail'),
    path('profile/detail/edit/', views.profile_edit, name='profile-detail-edit'),


    # ========================================================================
    # USER MANAGEMENT URLS (Admin/Staff)
    # ========================================================================
    path('users/', views.user_list, name='user-list'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),


    # ========================================================================
    # ROLE MANAGEMENT URLS (Admin/Staff)
    # ========================================================================
    path('roles/', views.role_list, name='role-list'),


    # ========================================================================
    # API URLS (JSON/AJAX)
    # ========================================================================
    path('api/check-username/', views.check_username, name='check-username'),
    path('api/check-email/', views.check_email, name='check-email'),
    path('api/check-phone/', views.check_phone, name='check-phone'),
    path('api/user-stats/', views.user_stats, name='user-stats'),
    path('api/departments/', views.department_api, name='department_api'),
    path('api/designations/', views.designation_api, name='designation_api'),
    path('api/employee/onboard/', views.employee_onboarding_api, name='employee_onboarding_api'),
    path('api/employee/delete/', views.delete_employee_api, name='delete_employee_api_post'),
    path('api/audit-logs/', views.audit_log_list_api, name='audit-logs-api'),
    path('api/employee/<int:emp_id>/delete/', views.delete_employee_api, name='delete_employee_api'),
    path('api/employee/<int:emp_id>/suspend/', views.suspend_employee_api, name='suspend_employee_api'),
    path('api/profile/update-image/', views.update_profile_image_api, name='update_profile_image_api'),
    path('api/profile/update-info/', views.update_profile_info_api, name='update_profile_info_api'),
    path('api/attendance/', views.attendance_api, name='attendance_api'),
    path('api/attendance/check-in/', views.attendance_check_in_api, name='attendance_check_in_api'),
    path('api/attendance/check-out/', views.attendance_check_out_api, name='attendance_check_out_api'),
    path('api/attendance/today-status/', views.attendance_today_status_api, name='attendance_today_status_api'),
    path('api/attendance/settings/', views.attendance_settings_api, name='attendance_settings_api'),
    path('api/wfh/request/', views.wfh_request_api, name='wfh_request_api'),
    path('api/wfh/approve/', views.wfh_approve_api, name='wfh_approve_api'),
]



