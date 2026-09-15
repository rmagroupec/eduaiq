from django.urls import path

from . import views

app_name = "institutions"

urlpatterns = [
    # Institutions
    path("institutions/", views.institution_list, name="institution-list"),
    path("institutions/import-csv/", views.import_institutions_csv, name="institution-import-csv"),
    path("institutions/me/", views.my_institution_detail, name="my-institution-detail"),
    path("institutions/<int:pk>/", views.institution_detail, name="institution-detail"),
    path("institutions/<int:pk>/allot-courses/", views.institution_allot_courses, name="institution-allot-courses"),

    # Students (nested under an Institution or global)
    path("institutions/<int:institution_pk>/students/", views.student_list, name="student-list"),
    path("students/", views.student_list, name="global-student-list"),
    path("students/create/", views.create_institution_student, name="student-create"),
    path("students/<int:pk>/", views.student_detail, name="student-detail"),
    path("students/<int:pk>/status/", views.update_student_status, name="student-update-status"),

    # Batches
    path("institutions/<int:institution_pk>/batches/", views.batch_list_create, name="institution-batch-list"),
    path("batches/", views.batch_list_create, name="batch-list-create"),
    path("batches/<int:pk>/", views.batch_detail, name="batch-detail"),

    # "Me" endpoints
    path("me/student-profile/", views.my_student_profile, name="my-student-profile"),
    path("me/children/", views.my_children, name="my-children"),
]