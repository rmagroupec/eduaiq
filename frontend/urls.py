from django.urls import path
from django.views.generic import TemplateView

app_name = 'frontend'

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('facility/', TemplateView.as_view(template_name='facility.html'), name='facility'),
    path('gallery/', TemplateView.as_view(template_name='gallery.html'), name='gallery'),
    path('testimonial/', TemplateView.as_view(template_name='testimonial.html'), name='testimonial'),
    path('categories/', TemplateView.as_view(template_name='categories.html'), name='categories'),
    path('legal-notice/', TemplateView.as_view(template_name='legal-notice.html'), name='legal_notice'),
    path('coming-soon/', TemplateView.as_view(template_name='comming-soon.html'), name='coming_soon'),
    path('search/', TemplateView.as_view(template_name='search.html'), name='search'),

    # Courses
    path('courses/', TemplateView.as_view(template_name='product-archive.html'), name='course_list'),
    path('courses/featured/', TemplateView.as_view(template_name='feature-course.html'), name='course_featured'),
    path('courses/<slug:slug>/', TemplateView.as_view(template_name='course-detail.html'), name='course_detail'),

    # Cart / checkout
    path('cart/', TemplateView.as_view(template_name='product-cart.html'), name='cart'),
    path('checkout/', TemplateView.as_view(template_name='product-checkout.html'), name='checkout'),
    path('product/<slug:slug>/', TemplateView.as_view(template_name='product-detail.html'), name='product_detail'),

    # Blog
    path('blog/', TemplateView.as_view(template_name='blog-archive.html'), name='blog_list'),
    path('blog/<slug:slug>/', TemplateView.as_view(template_name='single-blog.html'), name='blog_detail'),

    # Team
    path('team/', TemplateView.as_view(template_name='team.html'), name='team'),
    path('team/<slug:slug>/', TemplateView.as_view(template_name='team-detail.html'), name='team_detail'),

    # Career
    path('career/', TemplateView.as_view(template_name='career.html'), name='career'),
    path('career/<slug:slug>/', TemplateView.as_view(template_name='career-detail.html'), name='career_detail'),

    # AI Lab (dedicated page, must come before the generic slug route below)
    path('page/ai-lab/', TemplateView.as_view(template_name='ai-lab.html'), name='ai_lab'),

    # AI Books (dedicated page, must come before the generic slug route below)
    path('page/ai-books/', TemplateView.as_view(template_name='ai-books.html'), name='ai_books'),

    # Skill Development (dedicated page, must come before the generic slug route below)
    path('page/skill-development/', TemplateView.as_view(template_name='skill-development.html'), name='skill_development'),

    # EduAiQ Ecosystem (dedicated page, must come before the generic slug route below)
    path('page/eduaiq-ecosystem/', TemplateView.as_view(template_name='eduaiq-ecosystem.html'), name='eduaiq_ecosystem'),

    # Olympiads (dedicated page, must come before the generic slug route below)
    path('page/olympiads/', TemplateView.as_view(template_name='olympiads.html'), name='olympiads'),

    # Olympiad Curriculum (dedicated page, must come before the generic slug route below)
    path('page/olympiad-curriculum/', TemplateView.as_view(template_name='olympiad-curriculum.html'), name='olympiad_curriculum'),

    # Olympiad Form (dedicated page, must come before the generic slug route below)
    path('page/olympiad-form/', TemplateView.as_view(template_name='olympiad-form.html'), name='olympiad_form'),

    # Growth Partner Kit (dedicated page, must come before the generic slug route below)
    path('page/growth-partner-kit/', TemplateView.as_view(template_name='growth-partner-kit.html'), name='growth_partner_kit'),

    # Support (dedicated page, must come before the generic slug route below)
    path('page/support/', TemplateView.as_view(template_name='support.html'), name='support'),

    # Apply For Franchise (dedicated page, must come before the generic slug route below)
    path('page/apply-for-franchise/', TemplateView.as_view(template_name='apply-for-franchise.html'), name='apply_for_franchise'),

    # Generic single page (for CMS-style pages)
    path('page/<slug:slug>/', TemplateView.as_view(template_name='single-page.html'), name='single_page'),
    
    
    # Admin Panel

    path("dashboard/", TemplateView.as_view(template_name="admin_panel/index.html"), name="dashboard"),
    path("dashboard/index", TemplateView.as_view(template_name="admin_panel/index.html"), name="dashboard_index"),
    path("dashboard/add-new-employee", TemplateView.as_view(template_name="admin_panel/add-new-employee.html"), name="dashboard_add_new_employee"),
    path("dashboard/add-new-guardian", TemplateView.as_view(template_name="admin_panel/add-new-guardian.html"), name="dashboard_add_new_guardian"),
    path("dashboard/add-new-student", TemplateView.as_view(template_name="admin_panel/add-new-student.html"), name="dashboard_add_new_student"),
    path("dashboard/add-new-teacher", TemplateView.as_view(template_name="admin_panel/add-new-teacher.html"), name="dashboard_add_new_teacher"),
    path("dashboard/assign-role-plan", TemplateView.as_view(template_name="admin_panel/assign-role-plan.html"), name="dashboard_assign_role_plan"),
    path("dashboard/books-list", TemplateView.as_view(template_name="admin_panel/books-list.html"), name="dashboard_books_list"),
    path("dashboard/certificate", TemplateView.as_view(template_name="admin_panel/certificate.html"), name="dashboard_certificate"),
    path("dashboard/class-list", TemplateView.as_view(template_name="admin_panel/class-list.html"), name="dashboard_class_list"),
    path("dashboard/class-room-list", TemplateView.as_view(template_name="admin_panel/class-room-list.html"), name="dashboard_class_room_list"),
    path("dashboard/currencies", TemplateView.as_view(template_name="admin_panel/currencies.html"), name="dashboard_currencies"),
    path("dashboard/department", TemplateView.as_view(template_name="admin_panel/department.html"), name="dashboard_department"),
    path("dashboard/designation", TemplateView.as_view(template_name="admin_panel/designation.html"), name="dashboard_designation"),
    path("dashboard/edit-guardian", TemplateView.as_view(template_name="admin_panel/edit-guardian.html"), name="dashboard_edit_guardian"),
    path("dashboard/edit-student", TemplateView.as_view(template_name="admin_panel/edit-student.html"), name="dashboard_edit_student"),
    path("dashboard/edit-teacher", TemplateView.as_view(template_name="admin_panel/edit-teacher.html"), name="dashboard_edit_teacher"),
    path("dashboard/employee-attendance", TemplateView.as_view(template_name="admin_panel/employee-attendance.html"), name="dashboard_employee_attendance"),
    path("dashboard/employee-details", TemplateView.as_view(template_name="admin_panel/employee-details.html"), name="dashboard_employee_details"),
    path("dashboard/employee-list", TemplateView.as_view(template_name="admin_panel/employee-list.html"), name="dashboard_employee_list"),
    path("dashboard/event", TemplateView.as_view(template_name="admin_panel/event.html"), name="dashboard_event"),
    path("dashboard/exam", TemplateView.as_view(template_name="admin_panel/exam.html"), name="dashboard_exam"),
    path("dashboard/exam-result", TemplateView.as_view(template_name="admin_panel/exam-result.html"), name="dashboard_exam_result"),
    path("dashboard/exam-schedule", TemplateView.as_view(template_name="admin_panel/exam-schedule.html"), name="dashboard_exam_schedule"),
    path("dashboard/expense-head", TemplateView.as_view(template_name="admin_panel/expense-head.html"), name="dashboard_expense_head"),
    path("dashboard/expense-list", TemplateView.as_view(template_name="admin_panel/expense-list.html"), name="dashboard_expense_list"),
    path("dashboard/fees-collect", TemplateView.as_view(template_name="admin_panel/fees-collect.html"), name="dashboard_fees_collect"),
    path("dashboard/fees-discount", TemplateView.as_view(template_name="admin_panel/fees-discount.html"), name="dashboard_fees_discount"),
    path("dashboard/fees-group", TemplateView.as_view(template_name="admin_panel/fees-group.html"), name="dashboard_fees_group"),
    path("dashboard/fees-type", TemplateView.as_view(template_name="admin_panel/fees-type.html"), name="dashboard_fees_type"),
    path("dashboard/general", TemplateView.as_view(template_name="admin_panel/general.html"), name="dashboard_general"),
    path("dashboard/guardian-details", TemplateView.as_view(template_name="admin_panel/guardian-details.html"), name="dashboard_guardian_details"),
    path("dashboard/guardian-list", TemplateView.as_view(template_name="admin_panel/guardian-list.html"), name="dashboard_guardian_list"),
    path("dashboard/income-head", TemplateView.as_view(template_name="admin_panel/income-head.html"), name="dashboard_income_head"),
    path("dashboard/income-list", TemplateView.as_view(template_name="admin_panel/income-list.html"), name="dashboard_income_list"),
    path("dashboard/issue-return", TemplateView.as_view(template_name="admin_panel/issue-return.html"), name="dashboard_issue_return"),
    path("dashboard/languages", TemplateView.as_view(template_name="admin_panel/languages.html"), name="dashboard_languages"),
    path("dashboard/leave-request", TemplateView.as_view(template_name="admin_panel/leave-request.html"), name="dashboard_leave_request"),
    path("dashboard/leave-types", TemplateView.as_view(template_name="admin_panel/leave-types.html"), name="dashboard_leave_types"),
    path("dashboard/member-details", TemplateView.as_view(template_name="admin_panel/member-details.html"), name="dashboard_member_details"),
    path("dashboard/members-list", TemplateView.as_view(template_name="admin_panel/members-list.html"), name="dashboard_members_list"),
    path("dashboard/message", TemplateView.as_view(template_name="admin_panel/message.html"), name="dashboard_message"),
    path("dashboard/notice-board", TemplateView.as_view(template_name="admin_panel/notice-board.html"), name="dashboard_notice_board"),
    path("dashboard/notification", TemplateView.as_view(template_name="admin_panel/notification.html"), name="dashboard_notification"),
    path("dashboard/payroll", TemplateView.as_view(template_name="admin_panel/payroll.html"), name="dashboard_payroll"),
    path("dashboard/role-access", TemplateView.as_view(template_name="admin_panel/role-access.html"), name="dashboard_role_access"),
    path("dashboard/section-list", TemplateView.as_view(template_name="admin_panel/section-list.html"), name="dashboard_section_list"),
    path("dashboard/student-attendance", TemplateView.as_view(template_name="admin_panel/student-attendance.html"), name="dashboard_student_attendance"),
    path("dashboard/student-category", TemplateView.as_view(template_name="admin_panel/student-category.html"), name="dashboard_student_category"),
    path("dashboard/student-details", TemplateView.as_view(template_name="admin_panel/student-details.html"), name="dashboard_student_details"),
    path("dashboard/student-list", TemplateView.as_view(template_name="admin_panel/student-list.html"), name="dashboard_student_list"),
    path("dashboard/subject-list", TemplateView.as_view(template_name="admin_panel/subject-list.html"), name="dashboard_subject_list"),
    path("dashboard/subscription-plan", TemplateView.as_view(template_name="admin_panel/subscription-plan.html"), name="dashboard_subscription_plan"),
    path("dashboard/suspended-student", TemplateView.as_view(template_name="admin_panel/suspended-student.html"), name="dashboard_suspended_student"),
    path("dashboard/teacher-attendance", TemplateView.as_view(template_name="admin_panel/teacher-attendance.html"), name="dashboard_teacher_attendance"),
    path("dashboard/teacher-details", TemplateView.as_view(template_name="admin_panel/teacher-details.html"), name="dashboard_teacher_details"),
    path("dashboard/teacher-list", TemplateView.as_view(template_name="admin_panel/teacher-list.html"), name="dashboard_teacher_list"),
    path("dashboard/teacher-timetable", TemplateView.as_view(template_name="admin_panel/teacher-timetable.html"), name="dashboard_teacher_timetable"),
    path("dashboard/transaction", TemplateView.as_view(template_name="admin_panel/transaction.html"), name="dashboard_transaction"),

    # Login/Register aliases under dashboard/ — the sidebar links to these as
    # relative "login.html"/"register.html" from a /dashboard/<page> URL, which
    # resolves relative to that sibling path once the .html suffix is dropped.
    path("dashboard/login", TemplateView.as_view(template_name="admin_panel/login.html"), name="dashboard_login"),
    path("dashboard/register", TemplateView.as_view(template_name="admin_panel/register.html"), name="dashboard_register"),

    # Auth pages (standalone, not part of the dashboard shell)
    path("login/", TemplateView.as_view(template_name="admin_panel/login.html"), name="login"),
    path("register/", TemplateView.as_view(template_name="admin_panel/register.html"), name="register"),

]