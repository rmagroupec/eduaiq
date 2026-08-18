from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    # Leads (Institution / Franchise — B2B)
    path("leads/", views.lead_list, name="lead-list"),
    path("leads/<int:pk>/", views.lead_detail, name="lead-detail"),
    path("leads/<int:pk>/convert/", views.lead_convert, name="lead-convert"),

    # Student Inquiries (Admission / Course Enquiry — B2C)
    path("student-inquiries/", views.inquiry_list, name="inquiry-list"),
    path("student-inquiries/<int:pk>/", views.inquiry_detail, name="inquiry-detail"),
    path("student-inquiries/<int:pk>/convert/", views.inquiry_convert, name="inquiry-convert"),

    # Opportunities (Sales pipeline / deals)
    path("opportunities/", views.opportunity_list, name="opportunity-list"),
    path("opportunities/<int:pk>/", views.opportunity_detail, name="opportunity-detail"),

    # Activities (follow-ups / interaction log)
    path("activities/", views.activity_list, name="activity-list"),
    path("activities/<int:pk>/", views.activity_detail, name="activity-detail"),

    # Sales Targets
    path("targets/", views.target_list, name="target-list"),
    path("targets/<int:pk>/", views.target_detail, name="target-detail"),

    # Dashboard summary (pipeline KPIs)
    path("dashboard/", views.crm_dashboard, name="crm-dashboard"),
]
