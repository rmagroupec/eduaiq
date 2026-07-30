from django.urls import path

from . import views

app_name = "institutions"

urlpatterns = [
    # Institutions
    path("institutions/", views.institution_list, name="institution-list"),
    path("institutions/<int:pk>/", views.institution_detail, name="institution-detail"),

    # Students (nested under an Institution)
    path("institutions/<int:institution_pk>/students/", views.student_list, name="student-list"),
    path("students/<int:pk>/", views.student_detail, name="student-detail"),
    path("students/<int:pk>/status/", views.update_student_status, name="student-update-status"),

    # "Me" endpoints
    path("me/student-profile/", views.my_student_profile, name="my-student-profile"),
    path("me/children/", views.my_children, name="my-children"),
]